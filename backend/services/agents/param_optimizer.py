"""Parameter Optimizer Agent - Auto-tunes pipeline parameters."""
import logging
logger = logging.getLogger("omicsflow.agent.param_optimizer")

class ParameterOptimizerAgent:
    RESOURCE_PROFILES = {
        "rnaseq": {"threads": 16, "mem_gb": 64, "walltime": "48h"},
        "wgs": {"threads": 32, "mem_gb": 128, "walltime": "72h"},
        "amplicon": {"threads": 8, "mem_gb": 32, "walltime": "12h"},
        "tcr": {"threads": 8, "mem_gb": 16, "walltime": "4h"},
        "atac": {"threads": 16, "mem_gb": 64, "walltime": "24h"},
        "chipseq": {"threads": 16, "mem_gb": 64, "walltime": "24h"},
        "metagenomics": {"threads": 16, "mem_gb": 64, "walltime": "12h"},
        "somatic": {"threads": 32, "mem_gb": 128, "walltime": "48h"},
        "longread": {"threads": 16, "mem_gb": 64, "walltime": "24h"},
        "proteomics": {"threads": 8, "mem_gb": 32, "walltime": "8h"},
        "wes": {"threads": 16, "mem_gb": 64, "walltime": "24h"},
    }

    async def optimize(self, pipeline_type: str, data_info: dict) -> dict:
        base = self.RESOURCE_PROFILES.get(pipeline_type, {"threads": 8, "mem_gb": 32, "walltime": "24h"})
        n_samples = data_info.get("sample_count", 1)
        total_size = data_info.get("total_size_gb", 10)
        threads = min(base["threads"], max(4, int(total_size / 5) * 4))
        mem = min(base["mem_gb"], max(8, int(total_size * 2)))
        return {"pipeline_type": pipeline_type, "threads": threads, "memory_gb": mem, "walltime": base["walltime"], "n_samples": n_samples, "notes": f"Optimized for {n_samples} samples ({total_size:.1f} GB)"}

param_optimizer = ParameterOptimizerAgent()
