
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import (
    MaskingResponse, TriageResponse, RAGResponse, GenerateResponse,
    ReviewActionResponse
)
from app.services.review_service import ReviewRecord

client = TestClient(app)

def test_contract_mask_endpoint():
    """Contract: POST /mask -> MaskingResponse"""
    response = client.post("/mask", json={"text": "Test 123"})
    assert response.status_code == 200
    
    # Validation against Pydantic model (strict check)
    data = response.json()
    validated = MaskingResponse(**data)
    
    # Explicit field checks (Double Safety)
    assert "masked_text" in data
    assert "masked_entities" in data
    assert isinstance(data["masked_entities"], list)

def test_contract_predict_endpoint():
    """Contract: POST /predict -> TriageResponse"""
    response = client.post("/predict", json={"text": "Kredi kartım çalındı"})
    assert response.status_code == 200
    
    data = response.json()
    validated = TriageResponse(**data)
    
    assert "category" in data
    assert "category_confidence" in data
    assert "urgency" in data
    assert "urgency_confidence" in data
    assert "needs_human_review" in data
    assert "model_loaded" in data
    assert "review_status" in data

def test_contract_retrieve_endpoint():
    """Contract: POST /retrieve -> RAGResponse"""
    response = client.post("/retrieve", json={"text": "Kart aidatı"})
    assert response.status_code == 200
    
    data = response.json()
    validated = RAGResponse(**data)
    
    assert "relevant_sources" in data
    assert isinstance(data["relevant_sources"], list)

def test_contract_generate_endpoint():
    """Contract: POST /generate -> GenerateResponse"""
    response = client.post("/generate", json={
        "text": "Kartım nerede?",
        "category": "INFORMATION_REQUEST",
        "urgency": "LOW",
        "relevant_sources": []
    })
    
    if response.status_code != 200:
        print(f"Generate fail: {response.text}")
        
    assert response.status_code == 200
    
    data = response.json()
    validated = GenerateResponse(**data)
    
    assert "action_plan" in data
    assert "customer_reply_draft" in data
    assert "risk_flags" in data
    assert "sources" in data
    assert isinstance(data["action_plan"], list)

def test_contract_review_endpoints():
    """Contract: POST /review/approve & /reject"""
    # Create a review first (hack via predict low conf or manually)
    # For contract test, we can try to approve a non-existent one and check error schema,
    # OR mock the store. Let's rely on schema validation of the 404 or success model.
    
    # 1. Try to approve a random ID (Should be 404 but schema is defined for 200)
    # We want to check the *Success* contract.
    # Let's mock review_store to return a dummy record
    from unittest.mock import patch, MagicMock
    from review_store import ReviewRecord
    
    mock_record = ReviewRecord(
        review_id="test-id",
        status="APPROVED",
        created_at="2023-01-01",
        updated_at="2023-01-01",
        masked_text="masked",
        category="CAT",
        category_confidence=0.9,
        urgency="HIGH",
        urgency_confidence=0.9,
        notes="note"
    )
    
    with patch("app.services.review_service.review_store.update_review", return_value=mock_record):
        response = client.post("/review/approve", json={"review_id": "test-id", "notes": "ok"})
        assert response.status_code == 200
        data = response.json()
        validated = ReviewActionResponse(**data)
        assert data["review_id"] == "test-id"
        assert data["status"] == "APPROVED"
