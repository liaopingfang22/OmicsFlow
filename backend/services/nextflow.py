import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
from config import get_settings

settings = get_settings()


class NextflowService:
    def __init__(self):
        self.nextflow_path = settings.nextflow_path
        self.workflow_dir = Path(settings.workflow_dir)
        self.output_dir = Path(settings.output_dir)
        self.singularity_cache = settings.singularity_cache
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run_workflow(
        self,
        workflow_name: str,
        input_files: dict,
        params: dict,
        run_id: str,
    ) -> dict:
        work_dir = self.output_dir / run_id
        work_dir.mkdir(parents=True, exist_ok=True)

        nextflow_file = self.workflow_dir / f"{workflow_name}.nf"
        if not nextflow_file.exists():
            nextflow_file = self.workflow_dir / "main.nf"

        cmd = [
            self.nextflow_path,
            "run",
            str(nextflow_file),
            "-name", run_id,
            "-work-dir", str(work_dir),
            "-with-singularity",
            "-singularity-cache", self.singularity_cache,
        ]

        for key, value in input_files.items():
            cmd.extend([f"--{key}", str(value)])

        for key, value in params.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])

        if settings.singularity_enabled:
            cmd.extend(["-with-singularity"])

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        output_lines = []
        for line in iter(process.stdout.readline, ""):
            if line:
                output_lines.append(line.strip())
                if "ERROR" in line.upper():
                    break

        process.wait()
        return_code = process.returncode

        return {
            "run_id": run_id,
            "status": "completed" if return_code == 0 else "failed",
            "work_dir": str(work_dir),
            "return_code": return_code,
            "log": "\n".join(output_lines[-100:]),
        }

    async def get_task_status(self, run_id: str) -> dict:
        work_dir = self.output_dir / run_id
        log_file = work_dir / ".nextflow.log"

        if not log_file.exists():
            return {"status": "not_found"}

        status = "running"
        with open(log_file, "r") as f:
            content = f.read()
            if "ERROR" in content.upper():
                status = "failed"
            elif "completed" in content.lower():
                status = "completed"

        return {"status": status, "log_file": str(log_file)}

    async def cancel_workflow(self, run_id: str) -> dict:
        os.system(f"pkill -f 'nextflow.*-name {run_id}'")
        return {"status": "cancelled", "run_id": run_id}

    def list_workflows(self) -> list:
        workflows = []
        for nf_file in self.workflow_dir.glob("*.nf"):
            workflows.append({
                "name": nf_file.stem,
                "file": str(nf_file),
                "modified": datetime.fromtimestamp(nf_file.stat().st_mtime).isoformat(),
            })
        return workflows


nextflow_service = NextflowService()
