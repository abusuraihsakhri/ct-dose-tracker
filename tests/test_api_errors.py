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
