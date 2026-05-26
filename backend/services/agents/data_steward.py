"""Data Steward Agent - Monitors data, detects type, evaluates QC."""
import re, logging
from pathlib import Path

logger = logging.getLogger("omicsflow.agent.data_steward")

class DataStewardAgent:
    async def analyze(self, fastq_files: list, metadata: dict = None) -> dict:
        result = {"data_type": "unknown", "confidence": 0.0, "sample_count": 0, "paired_end": False, "total_size_gb": 0, "recommendation": ""}
        if not fastq_files: return result
        sample_names = set()
        total_size = 0
        for fq in fastq_files:
            name = Path(fq).name
            total_size += Path(fq).stat().st_size if Path(fq).exists() else 0
            stem = re.sub(r'\.(fastq|fq)(\.gz)?$', '', name)
            base = re.sub(r'[_\.][Rr]?[12]$', '', stem)
            sample_names.add(base)
        result["sample_count"] = len(sample_names)
        result["paired_end"] = len(fastq_files) > len(sample_names)
        result["total_size_gb"] = round(total_size / (1024**3), 2)
        meta_str = str(metadata).lower() if metadata else ""
        sigs = {"rnaseq": ["rna","mrna","transcriptome"], "wgs": ["wgs","whole genome"], "amplicon": ["16s","its","amplicon"], "scrnaseq": ["single cell","10x","scrna"], "atac": ["atac","chromatin"], "chipseq": ["chip","histone"], "methylation": ["bisulfite","methylation"], "wes": ["wes","exome","capture"]}
        for dtype, kws in sigs.items():
            if any(k in meta_str for k in kws):
                result["data_type"] = dtype
                result["confidence"] = 0.9
                break
        recs = {"rnaseq":"建议使用 RNA-seq 管线 (STAR + Salmon)","wgs":"建议使用 WGS 管线 (BWA + GATK)","amplicon":"建议使用 16S/ITS 管线 (DADA2)","scrnaseq":"建议使用单细胞管线 (Scanpy)","atac":"建议使用 ATAC-seq 管线","chipseq":"建议使用 ChIP-seq 管线","methylation":"建议使用甲基化管线 (Bismark)","wes":"建议使用 WES 管线"}
        result["recommendation"] = recs.get(result["data_type"], "请手动选择分析管线")
        return result

data_steward = DataStewardAgent()
