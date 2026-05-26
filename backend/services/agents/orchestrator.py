"""
Agent Orchestrator - Coordinates all 6 agents for end-to-end automation.
Event-driven: triggers agents based on system events.
"""
import logging
from services.agents.data_steward import data_steward
from services.agents.pipeline_advisor import pipeline_advisor
from services.agents.param_optimizer import param_optimizer
from services.agents.results_interpreter import results_interpreter
from services.agents.qc_sentinel import qc_sentinel
from services.agents.literature_agent import literature_agent

logger = logging.getLogger("omicsflow.orchestrator")


class AgentOrchestrator:
    """Coordinates multi-agent workflows."""

    async def on_new_data(self, fastq_files: list, metadata: dict = None) -> dict:
        """Event: New sequencing data detected. Data Steward + Pipeline Advisor."""
        analysis = await data_steward.analyze(fastq_files, metadata)
        advice = await pipeline_advisor.recommend(analysis["data_type"], organism=metadata.get("organism", "Homo sapiens") if metadata else "Homo sapiens")
        refs = await literature_agent.get_references(analysis["data_type"])
        return {"event": "new_data", "data_analysis": analysis, "pipeline_recommendation": advice, "literature": refs}

    async def on_task_start(self, pipeline_type: str, data_info: dict) -> dict:
        """Event: Task about to execute. Parameter Optimizer."""
        optimized = await param_optimizer.optimize(pipeline_type, data_info)
        return {"event": "task_start", "optimized_params": optimized}

    async def on_task_complete(self, task_id: str, pipeline_type: str, output_dir: str) -> dict:
        """Event: Task completed. Results Interpreter + QC Sentinel."""
        interpretation = await results_interpreter.interpret(task_id, pipeline_type, output_dir)
        qc = await qc_sentinel.check_task(task_id, pipeline_type, output_dir)
        return {"event": "task_complete", "interpretation": interpretation, "qc_check": qc}

    async def full_analysis_plan(self, data_type: str, organism: str, question: str = "") -> dict:
        """Full planning pipeline: all agents collaborate."""
        advice = await pipeline_advisor.recommend(data_type, question, organism)
        params = await param_optimizer.optimize(data_type, {"sample_count": 1, "total_size_gb": 50})
        refs = await literature_agent.get_references(data_type)
        return {"pipeline": advice, "parameters": params, "literature": refs, "workflow": self._describe_workflow(data_type)}

    def _describe_workflow(self, data_type: str) -> str:
        workflows = {
            "rnaseq": "FastQC → Trim Galore → STAR → Salmon → MultiQC → DESeq2",
            "wgs": "FastQC → Trim → BWA-MEM2 → MarkDuplicates → HaplotypeCaller → VariantFiltration",
            "amplicon": "DADA2 Filter → Learn Errors → Denoise → ASV Table → SILVA → Phyloseq",
            "tcr": "MiXCR Align → Assemble → Export Clonotypes → Diversity",
            "atac": "FastQC → Bowtie2 → Remove Duplicates → Filter chrM → MACS3 → FRiP",
            "chipseq": "FastQC → Bowtie2 → MACS3 → ChIPseeker → HOMER",
            "metagenomics": "FastQC → Kraken2 → Bracken → Merge Reports",
            "somatic": "Mutect2 → LearnReadOrientation → FilterMutectCalls",
            "methylation": "Bismark Align → Deduplicate → Methylation Extract → methylKit DMR",
            "longread": "Minimap2 → Sniffles SV → Clair3 Variants",
            "wes": "FastQC → BWA → GATK → Panel Coverage QC",
            "proteomics": "MaxQuant / DIA-NN",
        }
        return workflows.get(data_type, "FastQC → Analysis → Report")


orchestrator = AgentOrchestrator()
