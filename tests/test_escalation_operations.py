from __future__ import annotations

import json
from dataclasses import replace

import pytest

from escalation_router import EscalationRoutingError, FileEscalationRouter, load_request
from escalation_types import AuthorityStatus, DeploymentStatus, EscalationDecision, EscalationRequest, EvidenceLevel


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


def _request(request_id="ESC-TEST-001"):
    return EscalationRequest(
        request_id=request_id,
        origin="regression",
        summary="human review only",
        requested_decision=EscalationDecision.REQUEST_REVISION,
        canonical_output=True,
    )


@pytest.mark.parametrize(
    "bad_id",
    ["", "..", "../escape", "../../escape", "nested/file", r"bad\\name",
     ".hidden", "é-unsafe", "a" * 81],
)
def test_unsafe_request_id_never_creates_file(tmp_path, bad_id):
    router = FileEscalationRouter(tmp_path / "outbox")
    with pytest.raises(EscalationRoutingError, match="request_id"):
        router.route(_request(bad_id))
    assert not (tmp_path / "outbox").exists()


def test_repeated_id_cannot_overwrite_existing_request(tmp_path):
    router = FileEscalationRouter(tmp_path / "outbox")
    path = router.route(_request())
    original = path.read_bytes()
    with pytest.raises(EscalationRoutingError, match="overwrite refused"):
        router.route(replace(_request(), summary="altered authority claim"))
    assert path.read_bytes() == original


def test_preplanted_file_symlink_cannot_write_outside_outbox(tmp_path):
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("ORIGINAL")
    (outbox / "ESC-TEST-001.json").symlink_to(outside)
    with pytest.raises(EscalationRoutingError, match="overwrite refused"):
        FileEscalationRouter(outbox).route(_request())
    assert outside.read_text() == "ORIGINAL"


def test_outbox_directory_symlink_refused(tmp_path):
    actual = tmp_path / "external"
    actual.mkdir()
    (tmp_path / "outbox").symlink_to(actual, target_is_directory=True)
    with pytest.raises(EscalationRoutingError, match="symlink"):
        FileEscalationRouter(tmp_path / "outbox").route(_request())
    assert list(actual.iterdir()) == []


@pytest.mark.parametrize(
    "changes",
    [
        {"canonical_output": 1},
        {"authority": "NOT_EARNED"},
        {"deployment": "PROHIBITED"},
        {"evidence_level": "E2"},
        {"requested_decision": "execute"},
    ],
)
def test_untyped_authority_or_gate_values_refused(tmp_path, changes):
    with pytest.raises(EscalationRoutingError):
        FileEscalationRouter(tmp_path / "outbox").route(replace(_request(), **changes))
    assert not (tmp_path / "outbox").exists()


def test_nonfinite_request_payload_refused_before_file_creation(tmp_path):
    bad = replace(_request(), risk_flags=[float("nan")])
    with pytest.raises(EscalationRoutingError, match="canonical JSON"):
        FileEscalationRouter(tmp_path / "outbox").route(bad)
    assert not (tmp_path / "outbox").exists()


@pytest.mark.parametrize(
    "data",
    [
        '{"authority":"NOT_EARNED","authority":"PRODUCTION"}',
        '{"risk_flags":{"x":1,"x":2}}',
        '{"value":NaN}',
        '{"value":Infinity}',
        '[]',
    ],
)
def test_loading_ambiguous_json_fails_closed(tmp_path, data):
    path = tmp_path / "payload.json"
    path.write_text(data)
    with pytest.raises(EscalationRoutingError):
        load_request(path)


def test_valid_request_roundtrips_and_retains_no_authority(tmp_path):
    path = FileEscalationRouter(tmp_path / "outbox").route(_request())
    result = load_request(path)
    assert result["authority"] == AuthorityStatus.NOT_EARNED.value
    assert result["deployment"] == DeploymentStatus.PROHIBITED.value
    assert result["evidence_level"] == EvidenceLevel.E2.value
    assert result["canonical_output"] is True
