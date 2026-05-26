"""
Sequencer management and data monitoring API.
Supports BGI sequencers: G99, T1Plus, T7.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from services.database import get_db
from services.rbac import check_permission
from models.database import Sequencer, SequencerRun, Sample, User
from models.schemas import SequencerCreate, SequencerResponse, SequencerRunResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/sequencers", tags=["Sequencers"])

# BGI sequencer output directory patterns
BGI_OUTPUT_PATTERNS = {
    "G99": ["*_G99_*", "G99_*"],
    "T1Plus": ["*_T1_*", "T1_*"],
    "T7": ["*_T7_*", "T7_*"],
}


@router.post("/", response_model=SequencerResponse, status_code=status.HTTP_201_CREATED)
async def create_sequencer(
    data: SequencerCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new sequencer."""
    check_permission(current_user, "sequencers:write")

    sequencer = Sequencer(
        name=data.name,
        model=data.model,
        platform=data.platform,
        location=data.location,
        data_dir=data.data_dir,
    )
    db.add(sequencer)
    await db.commit()
    await db.refresh(sequencer)
    return sequencer


@router.get("/", response_model=List[SequencerResponse])
async def list_sequencers(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all registered sequencers."""
    check_permission(current_user, "sequencers:read")
    result = await db.execute(select(Sequencer).order_by(Sequencer.name))
    return result.scalars().all()


@router.get("/{sequencer_id}", response_model=SequencerResponse)
async def get_sequencer(
    sequencer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "sequencers:read")
    result = await db.execute(select(Sequencer).where(Sequencer.id == sequencer_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequencer not found")
    return seq


@router.delete("/{sequencer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequencer(
    sequencer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "sequencers:delete")
    result = await db.execute(select(Sequencer).where(Sequencer.id == sequencer_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequencer not found")
    await db.delete(seq)
    await db.commit()


@router.post("/{sequencer_id}/scan")
async def scan_sequencer_data(
    sequencer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan sequencer data directory for new runs."""
    check_permission(current_user, "sequencers:write")

    result = await db.execute(select(Sequencer).where(Sequencer.id == sequencer_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequencer not found")

    if not seq.data_dir or not os.path.isdir(seq.data_dir):
        raise HTTPException(status_code=400, detail="Sequencer data directory not configured or does not exist")

    # Scan for run directories
    runs_found = []
    data_path = Path(seq.data_dir)
    for item in sorted(data_path.iterdir()):
        if not item.is_dir():
            continue
        # Check if this is a new run (not already in DB)
        existing = await db.execute(
            select(SequencerRun).where(
                SequencerRun.run_dir == str(item),
                SequencerRun.sequencer_id == sequencer_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Detect fastq files
        fastq_files = list(item.rglob("*.fastq.gz")) + list(item.rglob("*.fq.gz"))
        sample_names = set()
        for fq in fastq_files:
            # Extract sample name from filename (BGI naming convention)
            name = fq.stem.replace(".fastq", "").replace(".fq", "")
            name = re.sub(r"_R?[12]$", "", name)
            name = re.sub(r"\.[12]$", "", name)
            sample_names.add(name)

        new_run = SequencerRun(
            sequencer_id=sequencer_id,
            run_name=item.name,
            run_dir=str(item),
            status="detected",
            sample_count=len(sample_names),
            started_at=datetime.fromtimestamp(item.stat().st_ctime),
        )
        db.add(new_run)
        runs_found.append(item.name)

        # Create sample records
        for sample_name in sorted(sample_names):
            r1_files = [f for f in fastq_files if sample_name in f.name and ("_R1" in f.name or ".1." in f.name or "_1." in f.name)]
            r2_files = [f for f in fastq_files if sample_name in f.name and ("_R2" in f.name or ".2." in f.name or "_2." in f.name)]
            sample = Sample(
                run=new_run,
                name=sample_name,
                read1_path=str(r1_files[0]) if r1_files else None,
                read2_path=str(r2_files[0]) if r2_files else None,
                status="pending",
            )
            db.add(sample)

    # Update last seen
    seq.last_seen = datetime.now(timezone.utc)
    await db.commit()

    return {
        "sequencer": seq.name,
        "new_runs": runs_found,
        "count": len(runs_found),
    }


@router.get("/{sequencer_id}/runs", response_model=List[SequencerRunResponse])
async def list_runs(
    sequencer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all runs for a sequencer."""
    check_permission(current_user, "sequencers:read")
    result = await db.execute(
        select(SequencerRun)
        .where(SequencerRun.sequencer_id == sequencer_id)
        .order_by(SequencerRun.created_at.desc())
    )
    return result.scalars().all()