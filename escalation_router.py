"""Bounded file-only escalation router for STEP_5_ESCALATION_OPS_PLUS.

No authority is earned, no external integration is invoked, and a repeated
request ID is refused rather than silently overwriting an earlier request.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from escalation_types import (
    AuthorityStatus,
    DeploymentStatus,
    EscalationDecision,
    EscalationRequest,
    EvidenceLevel,
)

_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z", re.ASCII)


class EscalationRoutingError(ValueError):
    """Raised when a request cannot be routed safely."""


class FileEscalationRouter:
    """Minimal local, append-only-by-ID outbox; not a secure OS sandbox."""

    def __init__(self, outbox_dir: str | Path = "escalations/outbox") -> None:
        self.outbox_dir = Path(outbox_dir)

    def route(self, request: EscalationRequest) -> Path:
        if type(request) is not EscalationRequest:
            raise EscalationRoutingError("request must be an EscalationRequest")
        if request.canonical_output is not True:
            raise EscalationRoutingError("canonical_output gate failed")
        if request.authority is not AuthorityStatus.NOT_EARNED:
            raise EscalationRoutingError("authority must remain NOT_EARNED")
        if request.deployment is not DeploymentStatus.PROHIBITED:
            raise EscalationRoutingError("deployment must remain PROHIBITED")
        if request.evidence_level is not EvidenceLevel.E2:
            raise EscalationRoutingError("evidence level must remain E2")
        if not isinstance(request.requested_decision, EscalationDecision):
            raise EscalationRoutingError("decision must be a review-only enumeration")
        if not isinstance(request.request_id, str) or not _REQUEST_ID.fullmatch(request.request_id):
            raise EscalationRoutingError("request_id must be 1-80 ASCII safe filename characters")

        try:
            serialized = json.dumps(
                request.to_json_dict(), indent=2, sort_keys=True, allow_nan=False
            ) + "\n"
        except (TypeError, ValueError) as exc:
            raise EscalationRoutingError("request is not canonical JSON") from exc

        # An existing outbox symlink is not a safe destination.
        if self.outbox_dir.is_symlink():
            raise EscalationRoutingError("outbox directory must not be a symlink")
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        if self.outbox_dir.is_symlink():
            raise EscalationRoutingError("outbox directory must not be a symlink")

        output_path = self.outbox_dir / f"{request.request_id}.json"
        try:
            # Exclusive create refuses existing files and pre-planted symlinks.
            # No external delivery, notification, execution, or promotion.
            with output_path.open("x", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
        except FileExistsError as exc:
            raise EscalationRoutingError("request_id already exists; overwrite refused") from exc
        return output_path


def load_request(path: str | Path) -> dict[str, Any]:
    def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key, value in pairs:
            if key in data:
                raise EscalationRoutingError(f"duplicate JSON object key: {key}")
            data[key] = value
        return data

    def no_nonfinite(token: str) -> None:
        raise EscalationRoutingError(f"nonfinite JSON value: {token}")

    parsed = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=unique_keys,
        parse_constant=no_nonfinite,
    )
    if not isinstance(parsed, dict):
        raise EscalationRoutingError("escalation request must be a JSON object")
    return parsed
