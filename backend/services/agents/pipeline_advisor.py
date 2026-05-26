"""Pipeline Advisor Agent - Recommends pipelines based on data + research question."""
import logging
logger = logging.getLogger("omicsflow.agent.pipeline_advisor")

class PipelineAdvisorAgent:
    PIPELINE_DB = {
        "rnaseq": {"pipeline": "rnaseq", "tools": "STAR + Salmon + DESeq2", "input": "FASTQ + 参考基因组", "output": "基因计数矩阵 + DEGs", "typical_time": "4-8h"},
        "wgs": {"pipeline": "wgs", "tools": "BWA-MEM2 + GATK HaplotypeCaller", "input": "FASTQ + 参考基因组", "output": "VCF 变异文件", "typical_time": "24-72h"},
        "amplicon": {"pipeline": "amplicon", "tools": "DADA2 + Phyloseq", "input": "FASTQ + SILVA", "output": "ASV 表 + 多样性分析", "typical_time": "2-4h"},
        "tcr": {"pipeline": "tcr", "tools": "MiXCR", "input": "FASTQ", "output": "clonotype 表 + 多样性", "typical_time": "1-3h"},
        "atac": {"pipeline": "atac", "tools": "Bowtie2 + MACS3 + chromVAR", "input": "FASTQ + 参考基因组", "output": "peaks + TF 偏好", "typical_time": "4-8h"},
        "chipseq": {"pipeline": "chipseq", "tools": "Bowtie2 + MACS3 + HOMER", "input": "FASTQ + 参考基因组", "output": "peaks + motif", "typical_time": "4-8h"},
        "spatial": {"pipeline": "spatial", "tools": "Squidpy", "input": "h5ad / Space Ranger", "output": "空间域图 + Moran's I", "typical_time": "1-2h"},
        "metagenomics": {"pipeline": "metagenomics", "tools": "Kraken2 + Bracken", "input": "FASTQ + Kraken2 DB", "output": "物种丰度报告", "typical_time": "2-6h"},
        "somatic": {"pipeline": "somatic", "tools": "GATK Mutect2", "input": "肿瘤/正常 BAM", "output": "过滤后 VCF", "typical_time": "8-24h"},
        "methylation": {"pipeline": "methylation", "tools": "Bismark + methylKit", "input": "FASTQ + 参考基因组", "output": "DMR", "typical_time": "12-48h"},
        "longread": {"pipeline": "longread", "tools": "Minimap2 + Sniffles + Clair3", "input": "FASTQ + 参考基因组", "output": "BAM + SV + 变异", "typical_time": "4-12h"},
        "wes": {"pipeline": "wes", "tools": "BWA + GATK + Panel QC", "input": "FASTQ + target BED", "output": "VCF + 覆盖度", "typical_time": "8-24h"},
        "proteomics": {"pipeline": "proteomics", "tools": "MaxQuant / DIA-NN", "input": "mzML + FASTA", "output": "蛋白定量", "typical_time": "2-8h"},
    }

    async def recommend(self, data_type: str, question: str = "", organism: str = "Homo sapiens") -> dict:
        info = self.PIPELINE_DB.get(data_type, self.PIPELINE_DB.get("wgs"))
        return {"data_type": data_type, "recommended_pipeline": info["pipeline"], "tools": info["tools"], "expected_input": info["input"], "expected_output": info["output"], "typical_runtime": info["typical_time"], "organism": organism, "parameters": self._suggest_params(data_type, organism)}

    def _suggest_params(self, data_type: str, organism: str) -> dict:
        params = {"threads": 16}
        if organism == "Mus musculus": params["reference"] = "GRCm39"
        elif organism == "Homo sapiens": params["reference"] = "GRCh38"
        if data_type == "amplicon": params["threads"] = 8
        elif data_type in ("wgs", "somatic"): params["threads"] = 32
        return params

pipeline_advisor = PipelineAdvisorAgent()
