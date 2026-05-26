"""
HPC Scheduler service for Sugon cluster (NIDVD HPC).
Supports PBS/Torque job submission with GPU node selection.
"""
import os
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict
from config import get_settings

logger = logging.getLogger("omicsflow.hpc")
settings = get_settings()

# Sugon cluster node definitions
SUGON_NODES = {
    "compute": {
        "nodes": "computer[1-4]",
        "cpu": "AMD EPYC 7763",
        "cores": 64,
        "mem": "1000gb",
        "gpu": None,
        "queue": "batch",
        "description": "CPU计算节点 (64核/1TB内存)",
    },
    "gpu_a40": {
        "nodes": "gpu[1-9]",
        "cpu": "Intel Xeon Gold 6326",
        "cores": 16,
        "mem": "512gb",
        "gpu": "A40:4",
        "queue": "gpu",
        "description": "GPU节点 (4×A40 48G)",
    },
    "gpu_3090": {
        "nodes": "gpu[10-17]",
        "cpu": "Intel Xeon Gold 5317",
        "cores": 12,
        "mem": "256gb",
        "gpu": "RTX3090:4",
        "queue": "gpu",
        "description": "GPU节点 (4/8×RTX3090 24G)",
    },
    "gpu_z100l": {
        "nodes": "gpu18",
        "cpu": "Intel Xeon Gold 5317",
        "cores": 12,
        "mem": "256gb",
        "gpu": "Z100L:2",
        "queue": "gpu",
        "description": "GPU节点 (2×Z100L 32G)",
    },
}

# Pipeline resource requirements
PIPELINE_RESOURCES = {
    "cnv": {"node_type": "compute", "cores": 8, "mem": "32gb", "walltime": "24:00:00"},
    "de": {"node_type": "compute", "cores": 4, "mem": "16gb", "walltime": "04:00:00"},
    "rnaseq": {"node_type": "compute", "cores": 16, "mem": "64gb", "walltime": "48:00:00"},
    "wgs": {"node_type": "compute", "cores": 32, "mem": "128gb", "walltime": "72:00:00"},
    "metagenomics": {"node_type": "compute", "cores": 16, "mem": "64gb", "walltime": "12:00:00"},
    "scRNA": {"node_type": "gpu_a40", "cores": 8, "mem": "64gb", "walltime": "24:00:00"},
    "deepvariant": {"node_type": "gpu_a40", "cores": 8, "mem": "64gb", "walltime": "12:00:00"},
}


def generate_pbs_script(
    job_name: str,
    task_id: str,
    pipeline_type: str,
    params: dict,
    node_type: str = "compute",
    cores: int = 8,
    mem: str = "32gb",
    walltime: str = "24:00:00",
    gpu_count: int = 0,
    queue: str = "batch",
    email: Optional[str] = None,
) -> str:
    """Generate a PBS/Torque submission script."""
    node_info = SUGON_NODES.get(node_type, SUGON_NODES["compute"])
    
    output_dir = Path(settings.output_dir) / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_dir = Path(settings.workflow_dir)
    pipeline_map = {
        "cnv": "cnv_workflow.nf",
        "de": "de_workflow.nf",
        "rnaseq": "rnaseq_workflow.nf",
        "wgs": "wgs_variant_workflow.nf",
        "metagenomics": "metagenomics_workflow.nf",
    }
    nf_file = workflow_dir / pipeline_map.get(pipeline_type, "main.nf")
    
    # Build Nextflow params
    nf_params = ""
    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                nf_params += f"    --{key} \\\n"
        elif value is not None:
            nf_params += f"    --{key} {value} \\\n"
    
    # GPU directive
    gpu_directive = ""
    if gpu_count > 0:
        gpu_directive = f"#PBS -l ngpus={gpu_count}"
    
    email_directive = ""
    if email:
        email_directive = f"#PBS -m abe\n#PBS -M {email}"
    
    script = f"""#!/bin/bash
# ============================================
# OmicsFlow PBS Job Script
# Task: {task_id}
# Pipeline: {pipeline_type}
# Cluster: Sugon NIDVD HPC
# ============================================
#PBS -N {job_name}
#PBS -q {node_info['queue']}
#PBS -l nodes=1:ppn={cores}
#PBS -l mem={mem}
#PBS -l walltime={walltime}
{gpu_directive}
#PBS -o {output_dir}/job_stdout.log
#PBS -e {output_dir}/job_stderr.log
{email_directive}

# Environment setup
export PATH="/opt/omicsflow/bin:$PATH"
export NXF_SINGULARITY_CACHEDIR={settings.singularity_cache}
export SINGULARITY_CACHEDIR={settings.singularity_cache}
export NXF_WORK={output_dir}/work
export OMP_NUM_THREADS={cores}

# Load modules (customize per cluster)
# module load singularity/3.8
# module load nextflow/23.04

# Create output directory
mkdir -p {output_dir}/work

echo "=========================================="
echo "OmicsFlow PBS Job Started"
echo "Job ID: $PBS_JOBID"
echo "Task ID: {task_id}"
echo "Pipeline: {pipeline_type}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=========================================="

# Run Nextflow pipeline
cd {workflow_dir}
{settings.nextflow_path} run {nf_file} \\
    -name {task_id} \\
    -work-dir {output_dir}/work \\
    -with-singularity \\
    -singularity-cache {settings.singularity_cache} \\
    -ansi-log false \\
    -resume \\
{nf_params}    --output_dir {output_dir}

EXIT_CODE=$?

echo "=========================================="
echo "Job completed with exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "=========================================="

exit $EXIT_CODE
"""
    return script


def submit_job(script_content: str, task_id: str) -> dict:
    """Submit a PBS job and return job info."""
    script_dir = Path(settings.output_dir) / task_id
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / "submit.sh"
    
    script_path.write_text(script_content, encoding="utf-8")
    script_path.chmod(0o755)
    
    try:
        result = subprocess.run(
            ["qsub", str(script_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            job_id = result.stdout.strip()
            logger.info(f"PBS job submitted: {job_id} for task {task_id}")
            return {
                "status": "submitted",
                "pbs_job_id": job_id,
                "script_path": str(script_path),
            }
        else:
            logger.error(f"PBS submission failed: {result.stderr}")
            return {
                "status": "failed",
                "error": result.stderr,
            }
    except FileNotFoundError:
        logger.warning("qsub not found, saving script only")
        return {
            "status": "script_only",
            "script_path": str(script_path),
            "message": "qsub not found. Run manually: qsub " + str(script_path),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_job_status(pbs_job_id: str) -> dict:
    """Check PBS job status."""
    try:
        result = subprocess.run(
            ["qstat", "-f", pbs_job_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {"status": "completed", "pbs_job_id": pbs_job_id}
        
        output = result.stdout
        if "job_state = Q" in output:
            return {"status": "queued", "pbs_job_id": pbs_job_id}
        elif "job_state = R" in output:
            return {"status": "running", "pbs_job_id": pbs_job_id}
        elif "job_state = C" in output:
            return {"status": "completed", "pbs_job_id": pbs_job_id}
        else:
            return {"status": "unknown", "raw": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def cancel_job(pbs_job_id: str) -> bool:
    """Cancel a PBS job."""
    try:
        result = subprocess.run(
            ["qdel", pbs_job_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to cancel job {pbs_job_id}: {e}")
        return False


def get_cluster_status() -> dict:
    """Get cluster queue status."""
    try:
        result = subprocess.run(
            ["qstat", "-Q"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {"status": "ok", "queues": result.stdout}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_node_types() -> list:
    """List available node types and their specs."""
    return [
        {"key": k, **v} for k, v in SUGON_NODES.items()
    ]