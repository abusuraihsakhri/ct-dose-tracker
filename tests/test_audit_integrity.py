"""Verify HMAC integrity checks detect entry mutation and broken links."""
from agents.base import AuditTrail

def test_valid_audit_chain():
    audit = AuditTrail("fixed-test-key")
    audit.log("tester", "unit", "CREATE", {"status": "ok"})
    audit.log("tester", "unit", "CHECK", {"status": "ok"})
    assert audit.verify_integrity()

def test_modified_signed_metadata_is_detected():
    audit = AuditTrail("fixed-test-key")
    audit.log("tester", "unit", "CREATE", {"status": "ok"})
    audit.logs[0]["actor"] = "forged"
    assert not audit.verify_integrity()

def test_modified_tail_signature_is_detected():
    audit = AuditTrail("fixed-test-key")
    audit.log("tester", "unit", "CREATE", {"status": "ok"})
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()
