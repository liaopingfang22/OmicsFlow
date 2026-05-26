"""Literature Agent - Searches PubMed and bioSkills for method references."""
import logging
logger = logging.getLogger("omicsflow.agent.literature")

class LiteratureAgent:
    METHODS_DB = {
        "rnaseq": {"title": "RNA-seq analysis", "key_papers": ["Dobin 2013 (STAR)", "Patro 2017 (Salmon)", "Love 2014 (DESeq2)"], "skills": ["bio-de-edger-basics", "bio-workflows-rnaseq-pipeline"]},
        "wgs": {"title": "WGS variant calling", "key_papers": ["Li 2009 (BWA)", "McKenna 2010 (GATK)", "Poplin 2018 (DeepVariant)"], "skills": ["bio-workflows-wgs-variant-calling"]},
        "amplicon": {"title": "16S/ITS amplicon", "key_papers": ["Callahan 2016 (DADA2)", "Bokulich 2018 (QIIME2)"], "skills": ["bio-workflows-metagenomics-pipeline"]},
        "tcr": {"title": "TCR/BCR repertoire", "key_papers": ["Bolotin 2015 (MiXCR)"], "skills": []},
        "atac": {"title": "ATAC-seq", "key_papers": ["Buenrostro 2013", "Schep 2017 (chromVAR)"], "skills": []},
        "chipseq": {"title": "ChIP-seq", "key_papers": ["Zhang 2008 (MACS)"], "skills": []},
        "metagenomics": {"title": "Metagenomics", "key_papers": ["Wood 2014 (Kraken2)", "Lu 2017 (Bracken)"], "skills": ["bio-workflows-metagenomics-pipeline"]},
    }

    async def get_references(self, analysis_type: str) -> dict:
        info = self.METHODS_DB.get(analysis_type, {"title": analysis_type, "key_papers": [], "skills": []})
        return {"analysis_type": analysis_type, "title": info["title"], "key_papers": info["key_papers"], "available_skills": info["skills"], "pubmed_query": f"{info['title']} bioinformatics best practices"}

literature_agent = LiteratureAgent()
