from fastapi import APIRouter, HTTPException, Request
from typing import List
import uuid

from app.schemas import (
    SourceItem,
    MaskingRequest, MaskingResponse,
    TriageRequest, TriageResponse,
    RAGRequest, RAGResponse,
    GenerateRequest, GenerateResponse,
    ReviewActionRequest, ReviewActionResponse
)
from app.core.logging import get_logger
from app.services.masking_service import masker
from app.services.triage_service import triage_engine
from app.services.review_service import review_store
from app.services.rag_service import rag_manager
from app.services.llm_service import llm_client
from app.services.similarity_service import similarity_service

router = APIRouter()
logger = get_logger("complaintops.api")

def sanitize_input(text: str) -> dict:
    """Sanitize input using double-pass PII masking for 0% leak rate."""
    masked_text, presidio_entities, regex_entities = masker.mask_with_double_pass(text)
    all_entities = [e["type"] for e in presidio_entities] + [e["type"] for e in regex_entities]
    return {
        "masked_text": masked_text,
        "masked_entities": all_entities,
    }

def log_sanitized_request(
    endpoint: str,
    masked_text: str,
    masked_entities: List[str],
    request_id: str,
) -> None:
    logger.info(
        "request_received endpoint=%s request_id=%s masked_text_length=%s masked_entity_types=%s",
        endpoint,
        request_id,
        len(masked_text),
        ",".join(masked_entities),
    )

@router.post("/mask", response_model=MaskingResponse)
def mask_pii(payload: MaskingRequest, request: Request):
    result = sanitize_input(payload.text)
    log_sanitized_request(
        "/mask",
        result["masked_text"],
        result["masked_entities"],
        request.state.request_id,
    )
    # SECURITY: Never return original_text - removed ALLOW_RAW_PII_RESPONSE vulnerability
    return MaskingResponse(
        masked_text=result["masked_text"],
        masked_entities=result["masked_entities"]
    )

@router.post("/predict", response_model=TriageResponse)
def predict_triage(payload: TriageRequest, request: Request):
    sanitized = sanitize_input(payload.text)
    log_sanitized_request(
        "/predict",
        sanitized["masked_text"],
        sanitized["masked_entities"],
        request.state.request_id,
    )
    result = triage_engine.predict(sanitized["masked_text"])
    needs_human_review = (
        result["category_confidence"] < 0.60
        or result["urgency_confidence"] < 0.60
    )
    review_id = None
    review_status = "AUTO_APPROVED"
    if needs_human_review:
        review_id = str(uuid.uuid4())
        review_store.create_review(
            review_id=review_id,
            masked_text=sanitized["masked_text"],
            category=result["category"],
            category_confidence=result["category_confidence"],
            urgency=result["urgency"],
            urgency_confidence=result["urgency_confidence"],
        )
        review_status = "PENDING_REVIEW"
    return TriageResponse(
        category=result["category"],
        category_confidence=result["category_confidence"],
        urgency=result["urgency"],
        urgency_confidence=result["urgency_confidence"],
        needs_human_review=needs_human_review,
        model_loaded=result["model_loaded"],
        review_status=review_status,
        review_id=review_id,
    )

@router.post("/retrieve", response_model=RAGResponse)
def retrieve_docs(payload: RAGRequest, request: Request):
    sanitized = sanitize_input(payload.text)
    log_sanitized_request(
        "/retrieve",
        sanitized["masked_text"],
        sanitized["masked_entities"],
        request.state.request_id,
    )
    sources = rag_manager.retrieve(sanitized["masked_text"], category=payload.category)
    return RAGResponse(relevant_sources=sources)

@router.post("/generate", response_model=GenerateResponse)
def generate_response(payload: GenerateRequest, request: Request):
    sanitized = sanitize_input(payload.text)
    log_sanitized_request(
        "/generate",
        sanitized["masked_text"],
        sanitized["masked_entities"],
        request.state.request_id,
    )
    risk_flags = []
    sources = payload.relevant_sources
    if not sources:
        try:
            sources = rag_manager.retrieve(
                sanitized["masked_text"],
                category=payload.category,
            )
            if not sources:
                risk_flags.append("RAG_EMPTY_SOURCES")
            else:
                risk_flags.append("RAG_FALLBACK_USED")
        except Exception:
            risk_flags.append("RAG_UNAVAILABLE")
            sources = []
    
    # Ensure source chunks are models or dicts
    snippets = []
    for source in sources:
        if isinstance(source, SourceItem):
            snippets.append(source.model_dump())
        elif isinstance(source, dict):
            snippets.append(source)
        else:
            # Fallback for unknown type
            snippets.append(source)

    result = llm_client.generate_response(
        text=sanitized["masked_text"],
        category=payload.category,
        urgency=payload.urgency,
        snippets=snippets
    )
    return GenerateResponse(
        action_plan=result["action_plan"],
        customer_reply_draft=result["customer_reply_draft"],
        risk_flags=list(dict.fromkeys(result["risk_flags"] + risk_flags)),
        sources=result["sources"],
        error_code=result.get("error_code"),
    )

@router.post("/review/approve", response_model=ReviewActionResponse)
def approve_review(payload: ReviewActionRequest):
    record = review_store.update_review(payload.review_id, "APPROVED", payload.notes)
    if not record:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewActionResponse(review_id=record.review_id, status=record.status, notes=record.notes)

@router.post("/review/reject", response_model=ReviewActionResponse)
def reject_review(payload: ReviewActionRequest):
    record = review_store.update_review(payload.review_id, "REJECTED", payload.notes)
    if not record:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewActionResponse(review_id=record.review_id, status=record.status, notes=record.notes)

# ============== SIMILARITY SEARCH ENDPOINTS ==============

from pydantic import BaseModel
from typing import Optional, Dict, Any

class IndexComplaintRequest(BaseModel):
    complaint_id: str
    masked_text: str
    category: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None

class SimilarComplaintItem(BaseModel):
    id: str
    masked_text: str
    similarity_score: float
    category: Optional[str] = None
    status: Optional[str] = None

class SimilarComplaintsResponse(BaseModel):
    similar_complaints: list[SimilarComplaintItem]
    total_indexed: int

@router.post("/index-complaint")
def index_complaint(payload: IndexComplaintRequest):
    """Index a complaint for similarity search."""
    metadata = {
        "category": payload.category or "",
        "status": payload.status or "",
        "created_at": payload.created_at or ""
    }
    success = similarity_service.index_complaint(
        complaint_id=payload.complaint_id,
        masked_text=payload.masked_text,
        metadata=metadata
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index complaint")
    return {"status": "indexed", "complaint_id": payload.complaint_id}

@router.get("/similar/{complaint_id}")
def find_similar_complaints(
    complaint_id: str,
    query_text: str,
    limit: int = 5
):
    """Find complaints similar to the given query text."""
    results = similarity_service.find_similar(
        query_text=query_text,
        n_results=limit,
        exclude_id=complaint_id
    )
    return SimilarComplaintsResponse(
        similar_complaints=results,
        total_indexed=similarity_service.get_collection_count()
    )
