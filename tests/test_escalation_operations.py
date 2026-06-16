from __future__ import annotations

import json

import pytest

from escalation_router import EscalationRoutingError, FileEscalationRouter
from escalation_types import EscalationDecision, EscalationRequest


def test_router_writes_canonical_request_to_outbox(tmp_path):
    router = FileEscalationRouter(tmp_path / "outbox")
    request = EscalationRequest(
        request_id="ESC-TEST-001",
        origin="pytest",
        summary="canonical request should be routed to local outbox",
        requested_decision=EscalationDecision.APPROVE_FOR_REVIEW_ONLY,
        canonical_output=True,
        risk_flags=["validation_required"],
    )

    output_path = router.route(request)

    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["request_id"] == "ESC-TEST-001"
    assert data["authority"] == "NOT_EARNED"
    assert data["deployment"] == "PROHIBITED"
    assert data["requested_decision"] == "approve_for_review_only"


def test_router_fails_closed_when_canonical_output_is_false(tmp_path):
    router = FileEscalationRouter(tmp_path / "outbox")
    request = EscalationRequest(
        request_id="ESC-TEST-002",
        origin="pytest",
        summary="non-canonical request must not be routed",
        requested_decision=EscalationDecision.REQUEST_REVISION,
        canonical_output=False,
    )

    with pytest.raises(EscalationRoutingError, match="canonical_output"):
        router.route(request)

    assert not (tmp_path / "outbox" / "ESC-TEST-002.json").exists()


def test_allowed_decisions_are_bounded():
    allowed = {decision.value for decision in EscalationDecision}
    assert "execute" not in allowed
    assert "deploy" not in allowed
    assert "self_authorize" not in allowed
    assert "approve_for_review_only" in allowed
