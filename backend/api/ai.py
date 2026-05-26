from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from config import get_settings
from services.skills_loader import skill_loader

settings = get_settings()

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


class IntentRequest(BaseModel):
    message: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class CodeRequest(BaseModel):
    analysis_type: str
    context: dict
    skill_name: Optional[str] = None


@router.post("/intent")
async def analyze_intent(request: IntentRequest):
    message_lower = request.message.lower()
    
    if any(kw in message_lower for kw in ["cnv", "copy number", "copy-number"]):
        return {"category": "cnv", "confidence": 0.9, "params": {"pipeline": "cnv"}}
    elif any(kw in message_lower for kw in ["differential", "dea", "de analysis", "edger", "deseq2"]):
        return {"category": "de", "confidence": 0.9, "params": {"method": "edger"}}
    elif any(kw in message_lower for kw in ["quality", "qc", "fastqc"]):
        return {"category": "qc", "confidence": 0.9, "params": {}}
    elif any(kw in message_lower for kw in ["rna-seq", "rnaseq", "rna_seq", "rna seq", "transcriptome", "gene expression quantification", "star", "salmon"]):
        return {"category": "rnaseq", "confidence": 0.9, "params": {"pipeline": "rnaseq"}}
    elif any(kw in message_lower for kw in ["wgs", "whole genome", "variant calling", "variant-calling", "snp", "indel", "haplotypecaller"]):
        return {"category": "wgs", "confidence": 0.9, "params": {"pipeline": "wgs"}}
    elif any(kw in message_lower for kw in ["metagenomics", "metagenome", "kraken", "bracken", "microbiome", "pathogen", "taxonom"]):
        return {"category": "metagenomics", "confidence": 0.9, "params": {"pipeline": "metagenomics"}}
    elif any(kw in message_lower for kw in ["single cell", "single-cell", "scrnaseq", "scRNA", "scanpy", "seurat", "clustering", "cell type"]):
        return {"category": "single_cell", "confidence": 0.8, "params": {"pipeline": "single_cell"}}
    elif any(kw in message_lower for kw in ["16s", "its", "amplicon", "dada2", "phyloseq", "扩增子", "微生物组"]):
        return {"category": "amplicon", "confidence": 0.9, "params": {"pipeline": "amplicon"}}
    elif any(kw in message_lower for kw in ["tcr", "bcr", "immune", "repertoire", "免疫", "mixcr", "clone"]):
        return {"category": "tcr", "confidence": 0.9, "params": {"pipeline": "tcr"}}
    elif any(kw in message_lower for kw in ["atac", "chromatin", "accessibility", "染色质", "开放"]):
        return {"category": "atac", "confidence": 0.9, "params": {"pipeline": "atac"}}
    elif any(kw in message_lower for kw in ["spatial", "visium", "stereo", "空间"]):
        return {"category": "spatial", "confidence": 0.9, "params": {"pipeline": "spatial"}}
    elif any(kw in message_lower for kw in ["chipseq", "chip-seq", "chip", "histone", "组蛋白", "转录因子"]):
        return {"category": "chipseq", "confidence": 0.9, "params": {"pipeline": "chipseq"}}
    elif any(kw in message_lower for kw in ["small rna", "mirna", "mirna-seq", "mirge", "mirdeep"]):
        return {"category": "smrna", "confidence": 0.9, "params": {"pipeline": "smrna"}}
    elif any(kw in message_lower for kw in ["somatic", "mutect", "tumor", "体细胞", "肿瘤"]):
        return {"category": "somatic", "confidence": 0.9, "params": {"pipeline": "somatic"}}
    elif any(kw in message_lower for kw in ["methylation", "bisulfite", "wgbs", "甲基化", "bismark"]):
        return {"category": "methylation", "confidence": 0.9, "params": {"pipeline": "methylation"}}
    elif any(kw in message_lower for kw in ["long read", "longread", "nanopore", "pacbio", "ont", "长读长", "三代"]):
        return {"category": "longread", "confidence": 0.9, "params": {"pipeline": "longread"}}
    elif any(kw in message_lower for kw in ["wes", "exome", "targeted", "外显子", "靶向"]):
        return {"category": "wes", "confidence": 0.9, "params": {"pipeline": "wes"}}
    elif any(kw in message_lower for kw in ["proteomics", "mass spec", "mass-spec", "蛋白质组", "质谱", "dda", "dia"]):
        return {"category": "proteomics", "confidence": 0.9, "params": {"pipeline": "proteomics"}}
    else:
        return {"category": "unknown", "confidence": 0.3, "params": {}}


@router.post("/chat")
async def ai_chat(request: ChatRequest):
    """Conversational AI assistant for bioinformatics analysis."""
    from services.ai_chat import ai_chat_service
    import uuid
    session_id = request.session_id or str(uuid.uuid4())[:8]
    result = await ai_chat_service.chat(session_id, request.message)
    return result


@router.get("/skills")
async def list_skills(category: Optional[str] = None):
    return skill_loader.list_skills(category)


@router.get("/skills/{skill_name}")
async def get_skill(skill_name: str):
    skill = skill_loader.get_skill_by_name(skill_name)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill
