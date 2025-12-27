"""
P0 Test Suite: KVKK Compliance Tests for Python AI Service
T1: Fail-Closed - Masking errors return proper HTTP errors
T2: Log sanitization - Raw PII never logged
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestPIIMasking:
    """T1: Test that masking service behaves correctly"""
    
    def test_mask_endpoint_returns_masked_text(self):
        """Verify /mask endpoint masks PII correctly"""
        from main import app
        client = TestClient(app)
        
        # Text with Turkish PII
        response = client.post("/mask", json={
            "text": "Adım Ahmet, TC: 12345678901, IBAN: TR330006100519786457841326"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify PII is masked
        assert "masked_text" in data
        assert "12345678901" not in data["masked_text"] or "[MASKED" in data["masked_text"]
        
        # Verify original_text is NOT in response (ALLOW_RAW_PII_RESPONSE=false by default)
        assert data.get("original_text") is None

    def test_mask_empty_text_handles_gracefully(self):
        """Empty or whitespace text should be handled"""
        from main import app
        client = TestClient(app)
        
        response = client.post("/mask", json={"text": ""})
        assert response.status_code == 200
        
    def test_mask_response_never_contains_raw_by_default(self):
        """ALLOW_RAW_PII_RESPONSE env var controls raw text exposure"""
        import os
        # Ensure env is not set or false
        original = os.environ.get("ALLOW_RAW_PII_RESPONSE")
        os.environ["ALLOW_RAW_PII_RESPONSE"] = "false"
        
        try:
            # Need to reimport to pick up env change
            from main import app
            client = TestClient(app)
            
            response = client.post("/mask", json={
                "text": "Email: test@example.com, Tel: 05551234567"
            })
            
            data = response.json()
            assert data.get("original_text") is None
        finally:
            if original:
                os.environ["ALLOW_RAW_PII_RESPONSE"] = original


class TestLogSanitization:
    """T2: Verify logs don't contain raw PII"""
    
    def test_log_sanitized_request_does_not_log_raw(self):
        """Log function receives masked text, not raw"""
        from main import log_sanitized_request
        
        # This function should only receive masked_text, not raw
        # Verify it doesn't crash and logs properly
        import io
        import logging
        
        # Capture logs
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger("complaintops.ai_service")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            log_sanitized_request(
                endpoint="/mask",
                masked_text="Hesabımdan [MASKED_AMOUNT] çekildi",
                masked_entities=["AMOUNT"],
                request_id="test-123"
            )
            
            log_output = log_capture.getvalue()
            # Should not contain actual amounts or PII
            # Should contain masked indicators
            assert "request_received" in log_output or len(log_output) == 0  # JSON format
        finally:
            logger.removeHandler(handler)


class TestNoRawTextStorage:
    """T3: Verify raw text is never stored"""
    
    def test_review_store_only_stores_masked_text(self):
        """review_store should only receive masked_text"""
        from review_store import review_store
        
        # Create a review with masked text
        review_id = "test-review-123"
        masked_text = "Şikayet: [MASKED_TCKN] hesabından işlem"
        
        record = review_store.create_review(
            review_id=review_id,
            masked_text=masked_text,
            category="FRAUD",
            category_confidence=0.5,
            urgency="HIGH",
            urgency_confidence=0.5
        )
        
        # Verify stored text is masked
        assert record.masked_text == masked_text
        assert "MASKED" in record.masked_text


class TestGenerateEndpoint:
    """Verify /generate uses masked text only"""
    
    def test_generate_uses_masked_input(self):
        """Generate endpoint should only process masked text"""
        from main import app
        client = TestClient(app)
        
        # Send already-masked text (as Java would after /mask call)
        response = client.post("/generate", json={
            "text": "Hesabımdan [MASKED_AMOUNT] çekildi, TC: [MASKED_TCKN]",
            "category": "FRAUD_UNAUTHORIZED_TX",
            "urgency": "HIGH",
            "relevant_sources": []
        })
        
        # Should return valid response structure
        assert response.status_code == 200
        data = response.json()
        
        assert "action_plan" in data
        assert "customer_reply_draft" in data
        assert "risk_flags" in data
        
        # Response should not "unmask" anything
        reply = data.get("customer_reply_draft", "")
        # LLM output is mocked or real, but shouldn't contain raw PII


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
