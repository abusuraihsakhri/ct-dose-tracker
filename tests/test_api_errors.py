"""FastAPI functions reject submitted identifiers rather than returning HTTP 500."""
import pytest
from fastapi import HTTPException
from agents.api import api_audit, api_chat, ChatRequest
from agents.models import SystemTaskPayload


def test_audit_phi_rejected():
    p = SystemTaskPayload(task_id="MRN-123456", target_identifier="KEY-001", primary_metric=10)
    with pytest.raises(HTTPException) as result:
        api_audit(p)
    assert result.value.status_code == 400


def test_chat_phi_rejected():
    with pytest.raises(HTTPException) as result:
        api_chat(ChatRequest(query="MRN-123456"))
    assert result.value.status_code == 400


def test_nonfinite_generic_metrics_rejected():
    from pydantic import ValidationError
    for invalid in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T", target_identifier="K", primary_metric=invalid)
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T", target_identifier="K", primary_metric=10, secondary_metric=invalid)


def test_mock_chat_does_not_claim_clinical_validation():
    from agents.llm_factory import MockLLM
    answer = MockLLM().invoke("Review my dose")
    assert "no clinical or scientific verification was performed" in answer
    assert "Review my dose" not in answer
