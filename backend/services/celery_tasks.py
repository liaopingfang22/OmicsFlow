"""
Celery task definitions for OmicsFlow.
"""
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from services.celery_app import celery_app
from config import get_settings

logger = logging.getLogger("omicsflow.celery_tasks")
settings = get_settings()


def _get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@celery_app.task(bind=True, name="services.celery_tasks.run_pipeline")
def run_pipeline(self, task_id: str, pipeline_type: str, params: dict):
    """Execute a Nextflow pipeline as a Celery task."""
    logger.info(f"Celery task started: {task_id} ({pipeline_type})")
    self.update_state(state="RUNNING", meta={"task_id": task_id, "progress": 0})

    workflow_dir = Path(settings.workflow_dir)
    output_dir = Path(settings.output_dir) / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline_map = {
        "cnv": "cnv_workflow.nf", "de": "de_workflow.nf",
        "rnaseq": "rnaseq_workflow.nf", "wgs": "wgs_variant_workflow.nf",
        "metagenomics": "metagenomics_workflow.nf", "amplicon": "amplicon_workflow.nf",
        "tcr": "tcr_workflow.nf", "atac": "atac_workflow.nf",
        "spatial": "spatial_workflow.nf", "chipseq": "chipseq_workflow.nf",
        "smrna": "smrna_workflow.nf", "somatic": "somatic_workflow.nf",
        "methylation": "methylation_workflow.nf", "longread": "longread_workflow.nf",
        "wes": "wes_workflow.nf", "proteomics": "proteomics_workflow.nf",
    }

    nf_file = workflow_dir / pipeline_map.get(pipeline_type, "main.nf")
    cmd = [
        settings.nextflow_path, "run", str(nf_file),
        "-name", task_id,
        "-work-dir", str(output_dir / "work"),
        "-with-singularity",
        "-ansi-log", "false",
    ]

    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"--{key}")
        elif value is not None:
            cmd.extend([f"--{key}", str(value)])

    # Write PID file for safe cancellation
    pid_file = output_dir / ".nextflow.pid"
    log_file = output_dir / "pipeline.log"

    try:
        with open(log_file, "w") as log_fh:
            process = subprocess.Popen(
                cmd, stdout=log_fh, stderr=subprocess.STDOUT,
                cwd=str(workflow_dir),
            )
            pid_file.write_text(str(process.pid))

            process.wait()

        pid_file.unlink(missing_ok=True)

        if process.returncode == 0:
            # Auto-generate report
            try:
                loop = _get_event_loop()
                from services.report_generator import report_generator
                report_path = loop.run_until_complete(
                    report_generator.generate_report(task_id, pipeline_type, str(output_dir))
                )
            except Exception as e:
                logger.warning(f"Report generation failed: {e}")
                report_path = None

            # Auto-trigger results interpreter agent
            try:
                loop = _get_event_loop()
                from services.agents.results_interpreter import results_interpreter
                interpretation = loop.run_until_complete(
                    results_interpreter.interpret(task_id, pipeline_type, str(output_dir))
                )
            except Exception as e:
                interpretation = {}
                logger.warning(f"Agent interpretation failed: {e}")

            return {
                "status": "completed",
                "task_id": task_id,
                "output_path": str(output_dir),
                "report_path": report_path,
                "interpretation": interpretation,
            }
        else:
            return {
                "status": "failed",
                "task_id": task_id,
                "error": f"Exit code: {process.returncode}",
                "log_file": str(log_file),
            }

    except Exception as e:
        logger.error(f"Pipeline {task_id} failed: {e}")
        return {"status": "failed", "task_id": task_id, "error": str(e)}


@celery_app.task(bind=True, name="services.celery_tasks.run_pipeline_gpu")
def run_pipeline_gpu(self, task_id: str, pipeline_type: str, params: dict, gpu_type: str = "A40"):
    """Execute a GPU pipeline on specified GPU node type."""
    logger.info(f"GPU task started: {task_id} on {gpu_type}")
    self.update_state(state="RUNNING", meta={"task_id": task_id, "gpu_type": gpu_type})

    hpc_params = {
        **params,
        "hpc_node_type": f"gpu_{gpu_type.lower()}" if gpu_type != "Z100L" else "gpu_z100l",
    }

    from services.hpc_scheduler import generate_pbs_script, submit_job, PIPELINE_RESOURCES
    resources = PIPELINE_RESOURCES.get(pipeline_type, PIPELINE_RESOURCES["cnv"])

    script = generate_pbs_script(
        job_name=f"omicsflow-{task_id[:8]}",
        task_id=task_id,
        pipeline_type=pipeline_type,
        params=hpc_params,
        node_type=resources["node_type"],
        cores=resources["cores"],
        mem=resources["mem"],
        walltime=resources["walltime"],
    )

    result = submit_job(script, task_id)
    return {"task_id": task_id, "pbs_result": result}


@celery_app.task(name="services.celery_tasks.cleanup_downloads")
def cleanup_downloads():
    """Periodic cleanup of old download files."""
    try:
        from services.download_service import download_service
        removed = download_service.cleanup_old_downloads(max_age_hours=168)
        logger.info(f"Cleanup: removed {removed} old download files")
        return {"removed": removed}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"error": str(e)}


@celery_app.task(name="services.celery_tasks.health_check")
def health_check():
    """Periodic health check task."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "omicsflow-celery",
    }
