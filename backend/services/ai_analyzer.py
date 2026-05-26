import httpx
import json
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import get_settings

settings = get_settings()
logger = logging.getLogger("omicsflow.ai_analyzer")


class AIAnalyzer:
    """AI-powered analysis service supporting Anthropic and OpenAI providers."""

    def __init__(self):
        self.api_key = settings.anthropic_api_key or settings.openai_api_key
        self.provider = "anthropic" if settings.anthropic_api_key else "openai"
        self.model = settings.ai_model
        self.max_tokens = settings.ai_max_tokens
        self.timeout = settings.ai_timeout

    async def analyze_intent(self, user_message: str) -> dict:
        """Analyze user message to determine bioinformatics analysis intent."""
        if not self.api_key:
            return self._rule_based_intent(user_message)

        prompt = f"""Analyze this bioinformatics analysis request and classify it:

Request: {user_message}

Categories:
- cnv: copy number variation analysis (CNVkit)
- de: differential expression (edgeR, DESeq2, limma)
- qc: quality control (FastQC, MultiQC)
- rnaseq: RNA-seq analysis (STAR, Salmon)
- wgs: whole genome sequencing variant calling (GATK, BWA-MEM2)
- metagenomics: metagenomics classification (Kraken2, Bracken, MetaPhlAn)
- single_cell: single-cell RNA-seq (Scanpy, Seurat)
- chip_seq: ChIP-seq analysis (MACS3, DiffBind)
- atac_seq: ATAC-seq analysis
- methylation: methylation analysis (Bismark, methylKit)
- proteomics: mass spectrometry proteomics
- metabolomics: LC-MS metabolomics
- pathway: pathway enrichment analysis (GO, KEGG, Reactome)
- visualization: data visualization (ggplot2, volcano, heatmap)
- phylogenetics: phylogenetic tree construction
- population_genetics: population genetics (PLINK, GWAS)

Return a JSON with:
- category: the main analysis type
- confidence: 0-1 confidence score
- params: suggested parameters for the analysis
"""
        return await self._call_ai(prompt)

    async def generate_analysis_code(
        self,
        analysis_type: str,
        context: dict,
        skill_name: Optional[str] = None,
    ) -> str:
        """Generate analysis code based on skill guidelines and context."""
        from services.skills_loader import skill_loader

        skill_content = ""
        if skill_name:
            skill = skill_loader.get_skill_by_name(skill_name)
            if skill:
                skill_content = skill.get("content", "")

        prompt = f"""You are a bioinformatics expert. Generate analysis code based on the following skill guidelines:

Skill: {skill_name}
{skill_content}

Analysis Type: {analysis_type}
Context: {json.dumps(context, indent=2)}

Generate R or Python code that follows best practices. Include comments explaining each step.
Return only the code without additional explanation.
"""
        return await self._call_ai(prompt)

    async def explain_results(self, results: dict, analysis_type: str) -> str:
        """Explain bioinformatics analysis results in plain language."""
        prompt = f"""Explain these bioinformatics analysis results to a researcher:

Analysis Type: {analysis_type}
Results: {json.dumps(results, indent=2)}

Provide a clear, concise explanation including:
1. Summary of findings
2. Key metrics
3. Interpretation
4. Recommendations for follow-up

Use plain language suitable for a scientist.
"""
        return await self._call_ai(prompt)

    def _rule_based_intent(self, message: str) -> dict:
        """Rule-based intent classification when AI is unavailable."""
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["cnv", "copy number", "copy-number"]):
            return {"category": "cnv", "confidence": 0.9, "params": {"pipeline": "cnv"}}
        elif any(kw in message_lower for kw in ["differential expression", "dea", "de analysis", "edgeR", "deseq2"]):
            return {"category": "de", "confidence": 0.9, "params": {"method": "edger"}}
        elif any(kw in message_lower for kw in ["quality control", "qc", "fastqc"]):
            return {"category": "qc", "confidence": 0.9, "params": {}}
        # Single-cell must be checked before RNA-seq as "single-cell RNA-seq" is more specific
        elif any(kw in message_lower for kw in ["single cell", "single-cell", "scrnaseq", "scanpy", "seurat", "clustering"]):
            return {"category": "single_cell", "confidence": 0.8, "params": {"pipeline": "single_cell"}}
        elif any(kw in message_lower for kw in ["rna-seq", "rnaseq", "rna seq", "transcriptome", "gene expression", "star", "salmon"]):
            return {"category": "rnaseq", "confidence": 0.9, "params": {"pipeline": "rnaseq"}}
        elif any(kw in message_lower for kw in ["wgs", "whole genome", "variant calling", "snp", "indel", "haplotypecaller", "gatk"]):
            return {"category": "wgs", "confidence": 0.9, "params": {"pipeline": "wgs"}}
        elif any(kw in message_lower for kw in ["metagenomics", "metagenome", "kraken", "bracken", "microbiome", "pathogen", "taxonom"]):
            return {"category": "metagenomics", "confidence": 0.9, "params": {"pipeline": "metagenomics"}}
        elif any(kw in message_lower for kw in ["volcano", "heatmap", "plot", "visualize"]):
            return {"category": "visualization", "confidence": 0.8, "params": {}}
        else:
            return {"category": "unknown", "confidence": 0.3, "params": {}}

    async def _call_ai(self, prompt: str) -> str:
        """Route AI call to the appropriate provider."""
        if not self.api_key:
            return "AI analysis requires API key configuration."

        if self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            return await self._call_openai(prompt)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)),
        reraise=True,
    )
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API with retry logic."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": self.max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("content", [{}])[0].get("text", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Anthropic API error: {type(e).__name__}")
            raise RuntimeError("AI service is temporarily unavailable. Please try again later.") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)),
        reraise=True,
    )
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": self.max_tokens,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"OpenAI API error: {type(e).__name__}")
            raise RuntimeError("AI service is temporarily unavailable. Please try again later.") from e


ai_analyzer = AIAnalyzer()
