"""
Enhanced Sequencer data scanner.
Automatically detects new runs and data files from sequencer directories.
"""
import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("omicsflow.data_scanner")


class DataScanner:
    """Scan sequencer data directories for new runs."""

    # Supported file patterns
    FASTQ_PATTERNS = [
        "*.fastq.gz", "*.fq.gz", "*.fastq", "*.fq",
        "*.fastq.gz.md5", "*.fq.gz.md5",
    ]

    # Sequencer-specific directory structures
    SEQUENCER_LAYOUTS = {
        "G99": {
            "run_dir_pattern": r"\d{8}_\d{4}_.*",
            "sample_sheet": "SampleSheet.csv",
            "fastq_dir": "Fastq",
            "data_dirs": ["Fastq", "fastq"],
        },
        "T1+": {
            "run_dir_pattern": r"\d{8}_.*",
            "sample_sheet": "SampleSheet.csv",
            "fastq_dir": "Fastq",
            "data_dirs": ["Fastq", "fastq", "fastq_pass"],
        },
        "T7": {
            "run_dir_pattern": r"\d{8}_.*",
            "sample_sheet": "SampleSheet.csv",
            "fastq_dir": "Fastq",
            "data_dirs": ["Fastq", "fastq"],
        },
        "i100": {
            "run_dir_pattern": r".*",
            "fastq_dir": "fastq",
            "data_dirs": ["fastq", "Fastq"],
        },
        "GridION": {
            "run_dir_pattern": r".*",
            "fastq_dir": "fastq_pass",
            "data_dirs": ["fastq_pass", "fastq_fail"],
        },
    }

    def scan_directory(self, base_dir: str, sequencer_model: str = "G99") -> dict:
        """Scan a sequencer data directory for runs and samples."""
        base = Path(base_dir)
        if not base.exists():
            return {"error": f"Directory not found: {base_dir}", "runs": []}

        layout = self.SEQUENCER_LAYOUTS.get(sequencer_model, self.SEQUENCER_LAYOUTS["G99"])
        runs = []

        for entry in sorted(base.iterdir()):
            if entry.is_dir():
                run_info = self._scan_run(entry, layout)
                if run_info and run_info.get("samples"):
                    runs.append(run_info)

        return {
            "base_dir": str(base),
            "sequencer_model": sequencer_model,
            "total_runs": len(runs),
            "runs": runs,
            "scan_time": datetime.now().isoformat(),
        }

    def _scan_run(self, run_dir: Path, layout: dict) -> Optional[dict]:
        """Scan a single run directory."""
        run_info = {
            "run_name": run_dir.name,
            "run_dir": str(run_dir),
            "samples": [],
            "total_fastq": 0,
            "total_size_gb": 0,
        }

        # Find FASTQ files
        fastq_files = []
        data_dirs = layout.get("data_dirs", ["Fastq"])
        for dd in data_dirs:
            fastq_path = run_dir / dd
            if fastq_path.exists():
                for pattern in self.FASTQ_PATTERNS:
                    fastq_files.extend(fastq_path.rglob(pattern))

        # Also check root for nanopore
        if not fastq_files:
            for pattern in self.FASTQ_PATTERNS:
                fastq_files.extend(run_dir.rglob(pattern))

        if not fastq_files:
            return None

        # Parse samples from filenames
        samples = self._parse_samples(fastq_files)
        total_size = sum(f.stat().st_size for f in fastq_files if f.exists())

        run_info["samples"] = samples
        run_info["total_fastq"] = len(fastq_files)
        run_info["total_size_gb"] = round(total_size / (1024**3), 2)

        # Parse SampleSheet if exists
        sample_sheet = run_dir / layout.get("sample_sheet", "SampleSheet.csv")
        if sample_sheet.exists():
            run_info["sample_sheet"] = self._parse_sample_sheet(sample_sheet)

        # Check for run metadata
        run_info_file = run_dir / "RunInfo.xml"
        if run_info_file.exists():
            run_info["has_run_info"] = True

        return run_info

    def _parse_samples(self, fastq_files: list) -> List[dict]:
        """Parse sample info from FASTQ filenames."""
        samples = {}
        for fq in fastq_files:
            name = fq.name
            # Skip undetermined
            if "Undetermined" in name:
                continue

            # Extract sample name
            stem = re.sub(r'\.(fastq|fq)(\.gz)?$', '', name)
            is_r2 = bool(re.search(r'[_\.][Rr]?2$', stem))
            base = re.sub(r'[_\.][Rr]?[12]$', '', stem)

            if base not in samples:
                samples[base] = {
                    "sample_name": base,
                    "read1": None,
                    "read2": None,
                    "is_paired": False,
                    "total_size": 0,
                }

            if is_r2:
                samples[base]["read2"] = str(fq)
                samples[base]["is_paired"] = True
            else:
                samples[base]["read1"] = str(fq)

            samples[base]["total_size"] += fq.stat().st_size if fq.exists() else 0

        result = []
        for name, info in samples.items():
            info["total_size_mb"] = round(info["total_size"] / (1024**2), 1)
            if info["read1"]:
                result.append(info)

        return result

    def _parse_sample_sheet(self, sheet_path: Path) -> dict:
        """Parse Illumina SampleSheet.csv."""
        try:
            content = sheet_path.read_text()
            sections = {}
            current_section = None
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("["):
                    current_section = line.strip("[]")
                    sections[current_section] = []
                elif current_section and line:
                    sections[current_section].append(line)
            return {"sections": list(sections.keys()), "path": str(sheet_path)}
        except Exception as e:
            return {"error": str(e)}

    def detect_data_type(self, run_info: dict) -> str:
        """Detect data type from run metadata."""
        run_name = run_info.get("run_name", "").lower()
        sample_sheet = run_info.get("sample_sheet", {})

        # Check run name for hints
        if any(kw in run_name for kw in ["atac", "chip"]):
            return "atac" if "atac" in run_name else "chipseq"
        if any(kw in run_name for kw in ["16s", "its", "amplicon"]):
            return "amplicon"
        if any(kw in run_name for kw in ["tcr", "bcr", "tcell"]):
            return "tcr"
        if any(kw in run_name for kw in ["scrna", "10x", "scRNA"]):
            return "scrnaseq"
        if any(kw in run_name for kw in ["wgs", "genome"]):
            return "wgs"
        if any(kw in run_name for kw in ["exome", "wes", "capture"]):
            return "wes"

        # Default to RNA-seq for Illumina paired-end
        samples = run_info.get("samples", [])
        if samples and samples[0].get("is_paired"):
            return "rnaseq"

        return "unknown"


data_scanner = DataScanner()