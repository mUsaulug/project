from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal

# Common Types
CategoryLiteral = Literal[
    "FRAUD_UNAUTHORIZED_TX",
    "CHARGEBACK_DISPUTE",
    "TRANSFER_DELAY",
    "ACCESS_LOGIN_MOBILE",
    "CARD_LIMIT_CREDIT",
    "INFORMATION_REQUEST",
    "CAMPAIGN_POINTS_REWARDS",
]

# --- Shared Models ---

class SourceItem(BaseModel):
    snippet: str
    source: str
    doc_name: str
    chunk_id: str


# --- API Contract Models ---

class MaskingRequest(BaseModel):
    text: str

class MaskingResponse(BaseModel):
    original_text: Optional[str] = None
    masked_text: str
    masked_entities: List[str]

class TriageRequest(BaseModel):
    text: str

class TriageResponse(BaseModel):
    category: CategoryLiteral
    category_confidence: float
    urgency: str
    urgency_confidence: float
    needs_human_review: bool
    model_loaded: bool
    review_status: str
    review_id: Optional[str] = None

class RAGRequest(BaseModel):
    text: str
    category: Optional[str] = None

class RAGResponse(BaseModel):
    relevant_sources: List[SourceItem]

class GenerateRequest(BaseModel):
    text: str
    category: CategoryLiteral
    urgency: str
    relevant_sources: List[SourceItem] = Field(default_factory=list)

class GenerateResponse(BaseModel):
    action_plan: List[str]
    customer_reply_draft: str
    risk_flags: List[str]
    sources: List[SourceItem]
    error_code: Optional[str] = None

class ReviewActionRequest(BaseModel):
    review_id: str
    notes: Optional[str] = None

class ReviewActionResponse(BaseModel):
    review_id: str
    status: str
    notes: Optional[str] = None


# --- LLM Internal Models ---

class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_plan: list[str] = Field(min_length=1)
    customer_reply_draft: str = Field(min_length=1)
    category: Optional[CategoryLiteral] = None
    risk_flags: list[str] = Field(min_length=1)
    sources: list[SourceItem] = Field(default_factory=list)
