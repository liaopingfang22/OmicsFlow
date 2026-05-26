"""
Task queue service using Redis as broker.
Provides async task execution for Nextflow pipelines.
"""
import asyncio
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from config import get_settings

logger = logging.getLogger("omicsflow.task_queue")
settings = get_settings()

# In-memory task registry (replace with Redis/Celery in production)
_tasks: dict = {}


class TaskStatus:
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


async def enqueue_pipeline_task(
    task_id: str,
    pipeline_type: str,
    params: dict,
    db_session_factory=None,
):
    """Enqueue a Nextflow pipeline task for async execution."""
    _tasks[task_id] = {
        "id": task_id,
        "status": TaskStatus.QUEUED,
        "progress": 0,
        "started_at": None,
        "log_lines": [],
    }
    
    asyncio.create_task(_execute_pipeline(task_id, pipeline_type, params, db_session_factory))
    return task_id


async def _execute_pipeline(task_id: str, pipeline_type: str, params: dict, db_session_factory):
    """Execute a Nextflow pipeline in background."""
    task_info = _tasks.get(task_id)
    if not task_info:
        return
    
    task_info["status"] = TaskStatus.RUNNING
    task_info["started_at"] = datetime.now(timezone.utc).isoformat()
    
    workflow_dir = Path(settings.workflow_dir)
    output_dir = Path(settings.output_dir) / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline_map = {
        "cnv": "cnv_workflow.nf",
        "de": "de_workflow.nf",
        "rnaseq": "rnaseq_workflow.nf",
        "wgs": "wgs_variant_workflow.nf",
        "metagenomics": "metagenomics_workflow.nf",
    }
    
    nf_file = workflow_dir / pipeline_map.get(pipeline_type, "main.nf")
    
    cmd = [
        settings.nextflow_path, "run", str(nf_file),
        "-name", task_id,
        "-work-dir", str(output_dir / "work"),
        "-with-singularity",
    ]
    
    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"--{key}")
        elif value is not None:
            cmd.extend([f"--{key}", str(value)])
    
    # Check if HPC mode is enabled
    hpc_enabled = getattr(settings, 'hpc_enabled', False)
    if hpc_enabled:
        try:
            from services.hpc_scheduler import generate_pbs_script, submit_job, PIPELINE_RESOURCES
            resources = PIPELINE_RESOURCES.get(pipeline_type, PIPELINE_RESOURCES["cnv"])
            script = generate_pbs_script(
                job_name=f"omicsflow-{task_id[:8]}",
                task_id=task_id,
                pipeline_type=pipeline_type,
                params=params,
                node_type=resources["node_type"],
                cores=resources["cores"],
                mem=resources["mem"],
                walltime=resources["walltime"],
            )
            result = submit_job(script, task_id)
            task_info["log_lines"].append(f"[PBS] Submission result: {result}")
            if result.get("status") == "submitted":
                task_info["pbs_job_id"] = result["pbs_job_id"]
                task_info["status"] = TaskStatus.RUNNING
                return
            else:
                task_info["status"] = TaskStatus.FAILED
                task_info["error"] = result.get("error", "PBS submission failed")
                return
        except Exception as e:
            task_info["log_lines"].append(f"[PBS] Error: {e}, falling back to local execution")

    task_info["log_lines"].append(f"[{datetime.now(timezone.utc).isoformat()}] Starting: {' '.join(cmd)}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(workflow_dir),
        )
        
        async for line in process.stdout:
            decoded = line.decode().strip()
            if decoded:
                task_info["log_lines"].append(decoded)
                
                # Parse progress from Nextflow output
                if "%" in decoded:
                    try:
                        pct = int(decoded.split("%")[0].split()[-1])
                        task_info["progress"] = pct
                    except (ValueError, IndexError):
                        pass
        
        await process.wait()
        
        if process.returncode == 0:
            task_info["status"] = TaskStatus.COMPLETED
            task_info["progress"] = 100
            task_info["output_path"] = str(output_dir)
            
            # Auto-generate report
            try:
                from services.report_generator import report_generator
                report_path = report_generator.generate_report(task_id, pipeline_type, str(output_dir))
                if report_path:
                    task_info["report_path"] = report_path
                    task_info["log_lines"].append(f"[auto] Report generated: {report_path}")
            except Exception as re:
                logger.warning(f"Report generation failed for {task_id}: {re}")
        else:
            task_info["status"] = TaskStatus.FAILED
            task_info["error"] = f"Exit code: {process.returncode}"
    
    except Exception as e:
        task_info["status"] = TaskStatus.FAILED
        task_info["error"] = str(e)
        logger.error(f"Pipeline {task_id} failed: {e}")
    
    task_info["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    # Send WebSocket notification
    try:
        from services.websocket import ws_manager
        await ws_manager.send_task_update(task_id, {
            "status": task_info["status"],
            "progress": task_info.get("progress", 0),
            "error": task_info.get("error"),
        })
        await ws_manager.send_global_update("task_completed", {
            "task_id": task_id,
            "status": task_info["status"],
        })
    except Exception as we:
        logger.warning(f"WebSocket notification failed: {we}")
    
    # Update database if session factory provided
    if db_session_factory:
        try:
            async with db_session_factory() as db:
                from sqlalchemy import update
                from models.database import Task
                await db.execute(
                    update(Task).where(Task.id == task_id).values(
                        status=task_info["status"],
                        progress=task_info["progress"],
                        output_path=task_info.get("output_path"),
                        error_message=task_info.get("error"),
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update task {task_id} in DB: {e}")


def get_task_status(task_id: str) -> Optional[dict]:
    """Get current task status."""
    return _tasks.get(task_id)


def get_task_logs(task_id: str, since_line: int = 0) -> list:
    """Get task logs since a given line number."""
    task = _tasks.get(task_id)
    if not task:
        return []
    return task["log_lines"][since_line:]


async def cancel_task(task_id: str) -> bool:
    """Cancel a running task."""
    task = _tasks.get(task_id)
    if not task or task["status"] not in (TaskStatus.QUEUED, TaskStatus.RUNNING):
        return False
    
    task["status"] = TaskStatus.CANCELLED
    
    import signal
    pid_file = Path(settings.output_dir) / task_id / ".nextflow.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to PID {pid} for task {task_id}")
        except (ValueError, ProcessLookupError) as e:
            logger.warning(f"PID file read failed for {task_id}: {e}")
    else:
        logger.warning(f"No PID file found for task {task_id}, using nextflow stop")
        os.system(f"nextflow stop {task_id}")
    return True
