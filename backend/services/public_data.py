"""
Public data download service.
Supports searching and downloading from GEO, SRA, ENA.
"""
import re, os, asyncio, logging
from pathlib import Path
from typing import Optional, List
import httpx
from config import get_settings

logger = logging.getLogger("omicsflow.public_data")
settings = get_settings()

class PublicDataService:
    NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    GEO_BASE = "https://www.ncbi.nlm.nih.gov/geo"

    def __init__(self):
        self.download_dir = Path(settings.output_dir) / "public_data"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def search_geo(self, query: str, organism: str = "Homo sapiens", max_results: int = 20) -> List[dict]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.NCBI_BASE}/esearch.fcgi", params={"db": "gds", "term": f"{query} AND {organism}[Organism]", "retmax": max_results, "retmode": "json"}, timeout=15.0)
                ids = resp.json().get("esearchresult", {}).get("idlist", [])
                if not ids: return []
                resp = await client.get(f"{self.NCBI_BASE}/esummary.fcgi", params={"db": "gds", "id": ",".join(ids), "retmode": "json"}, timeout=15.0)
                summaries = resp.json().get("result", {})
                results = []
                for uid in ids:
                    info = summaries.get(uid, {})
                    if not info or uid == "uids": continue
                    results.append({"geo_id": info.get("accession",""), "title": info.get("title",""), "summary": info.get("summary","")[:500], "organism": info.get("taxon",""), "platform": info.get("platform",""), "n_samples": info.get("n_samples",0), "pub_date": info.get("pdat",""), "gse_link": f"{self.GEO_BASE}/acc.cgi?acc={info.get('accession','')}"})
                return results
        except Exception as e:
            logger.error(f"GEO search error: {e}")
            return []

    async def search_sra(self, query: str, max_results: int = 20) -> List[dict]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.NCBI_BASE}/esearch.fcgi", params={"db": "sra", "term": query, "retmax": max_results, "retmode": "json"}, timeout=15.0)
                ids = resp.json().get("esearchresult", {}).get("idlist", [])
                if not ids: return []
                resp = await client.get(f"{self.NCBI_BASE}/esummary.fcgi", params={"db": "sra", "id": ",".join(ids), "retmode": "json"}, timeout=15.0)
                summaries = resp.json().get("result", {})
                results = []
                for uid in ids:
                    info = summaries.get(uid, {})
                    if not info or uid == "uids": continue
                    exp = info.get("expxml", "")
                    title_m = re.search(r'<Title>(.*?)</Title>', exp)
                    title = title_m.group(1) if title_m else info.get("title", "")
                    runs = re.findall(r'run="([^"]+)"', info.get("runs", ""))
                    results.append({"sra_id": uid, "title": title[:300], "bioproject": info.get("bioproject",""), "organism": info.get("organism",""), "run_ids": runs[:5], "created": info.get("createdate","")})
                return results
        except Exception as e:
            logger.error(f"SRA search error: {e}")
            return []

    async def download_sra_run(self, srr_id: str, user_id: str) -> dict:
        output_dir = self.download_dir / user_id / srr_id
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            cmd = f"cd {output_dir} && prefetch {srr_id} && fasterq-dump {srr_id} --threads 4 --outdir ."
            process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            output = []
            async for line in process.stdout:
                output.append(line.decode().strip())
            await process.wait()
            if process.returncode == 0:
                fastq_files = list(output_dir.glob("*.fastq*"))
                return {"status": "completed", "srr_id": srr_id, "output_dir": str(output_dir), "files": [str(f) for f in fastq_files]}
            return {"status": "failed", "error": "\n".join(output[-20:])}
        except FileNotFoundError:
            return {"status": "tool_missing", "error": "Install SRA Toolkit: conda install -c bioconda sra-tools", "manual_cmd": f"prefetch {srr_id} && fasterq-dump {srr_id}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def search_pubmed(self, query: str, max_results: int = 20) -> List[dict]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.NCBI_BASE}/esearch.fcgi", params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json", "sort": "relevance"}, timeout=15.0)
                ids = resp.json().get("esearchresult", {}).get("idlist", [])
                if not ids: return []
                resp = await client.get(f"{self.NCBI_BASE}/esummary.fcgi", params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"}, timeout=15.0)
                summaries = resp.json().get("result", {})
                results = []
                for uid in ids:
                    info = summaries.get(uid, {})
                    if not info or uid == "uids": continue
                    results.append({"pmid": uid, "title": info.get("title",""), "journal": info.get("fulljournalname",""), "pubdate": info.get("pubdate",""), "authors": [a.get("name","") for a in info.get("authors",[])][:5], "doi": info.get("elocationid",""), "pubmed_link": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"})
                return results
        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []

    async def search_literature_for_analysis(self, organism: str, analysis_type: str, max_results: int = 10) -> List[dict]:
        """Search PubMed for literature about a specific analysis approach."""
        queries = {
            "rnaseq": f"RNA-seq {organism} differential expression analysis",
            "wgs": f"whole genome sequencing {organism} variant calling",
            "16s": f"16S rRNA {organism} microbiome analysis",
            "scrnaseq": f"single cell RNA-seq {organism} clustering",
            "chipseq": f"ChIP-seq {organism} peak calling",
            "atac": f"ATAC-seq {organism} chromatin accessibility",
            "metagenomics": f"shotgun metagenomics {organism} classification",
            "methylation": f"whole genome bisulfite sequencing {organism} methylation",
            "proteomics": f"mass spectrometry proteomics {organism} quantification",
            "spatial": f"spatial transcriptomics {organism} tissue",
        }
        q = queries.get(analysis_type, f"{analysis_type} {organism} bioinformatics analysis")
        return await self.search_pubmed(q, max_results)

    async def suggest_analysis_plan(self, organism: str, data_type: str) -> dict:
        """Suggest analysis plan based on literature."""
        papers = await self.search_literature_for_analysis(organism, data_type, 5)
        pipeline_map = {
            "rnaseq": {"pipeline": "rnaseq", "tools": "STAR + Salmon + DESeq2", "typical_params": "--method star_salmon --threads 16"},
            "wgs": {"pipeline": "wgs", "tools": "BWA-MEM2 + GATK HaplotypeCaller", "typical_params": "--threads 32"},
            "16s": {"pipeline": "amplicon", "tools": "DADA2 + SILVA + Phyloseq", "typical_params": "--threads 8"},
            "scrnaseq": {"pipeline": "single_cell", "tools": "Scanpy + Leiden + CellTypist", "typical_params": ""},
            "chipseq": {"pipeline": "chipseq", "tools": "Bowtie2 + MACS3 + HOMER", "typical_params": "--peak_type narrow"},
            "atac": {"pipeline": "atac", "tools": "Bowtie2 + MACS3 + chromVAR", "typical_params": "--threads 8"},
            "metagenomics": {"pipeline": "metagenomics", "tools": "Kraken2 + Bracken", "typical_params": "--threads 16"},
            "methylation": {"pipeline": "methylation", "tools": "Bismark + methylKit", "typical_params": "--threads 8"},
            "proteomics": {"pipeline": "proteomics", "tools": "MaxQuant / DIA-NN", "typical_params": "--method dda"},
            "spatial": {"pipeline": "spatial", "tools": "Squidpy + Scanpy", "typical_params": ""},
        }
        plan = pipeline_map.get(data_type, {"pipeline": "qc", "tools": "FastQC + MultiQC", "typical_params": ""})
        plan["references"] = papers
        plan["organism"] = organism
        plan["data_type"] = data_type
        return plan

public_data_service = PublicDataService()
