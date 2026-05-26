"""Public data search and literature API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from services.public_data import public_data_service
from models.database import User
from api.deps import get_current_active_user

router = APIRouter(prefix="/data", tags=["Public Data & Literature"])


class GEOSearchRequest(BaseModel):
    query: str
    organism: str = "Homo sapiens"
    max_results: int = 20


class SRASearchRequest(BaseModel):
    query: str
    max_results: int = 20


class DownloadRequest(BaseModel):
    srr_id: str


class PubMedRequest(BaseModel):
    query: str
    max_results: int = 20


class AnalysisPlanRequest(BaseModel):
    organism: str
    data_type: str


@router.post("/geo/search")
async def search_geo(
    data: GEOSearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Search GEO for public datasets."""
    results = await public_data_service.search_geo(data.query, data.organism, data.max_results)
    return {"query": data.query, "results": results, "count": len(results)}


@router.post("/sra/search")
async def search_sra(
    data: SRASearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Search SRA for sequencing runs."""
    results = await public_data_service.search_sra(data.query, data.max_results)
    return {"query": data.query, "results": results, "count": len(results)}


@router.post("/sra/download")
async def download_sra(
    data: DownloadRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Download an SRA run (requires SRA Toolkit on server)."""
    result = await public_data_service.download_sra_run(data.srr_id, current_user.id)
    return result


@router.post("/pubmed/search")
async def search_pubmed(
    data: PubMedRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Search PubMed for literature."""
    results = await public_data_service.search_pubmed(data.query, data.max_results)
    return {"query": data.query, "results": results, "count": len(results)}


@router.post("/literature/plan")
async def suggest_analysis_plan(
    data: AnalysisPlanRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Get literature-backed analysis plan suggestion."""
    plan = await public_data_service.suggest_analysis_plan(data.organism, data.data_type)
    return plan
