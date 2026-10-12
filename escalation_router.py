"""File-based escalation router for STEP_5_ESCALATION_OPS_PLUS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from escalation_types import EscalationRequest


class EscalationRoutingError(ValueError):
    """Raised when a request cannot be routed safely."""


class FileEscalationRouter:
    """Minimal local router that writes requests to an outbox directory."""

    def __init__(self, outbox_dir: str | Path = "escalations/outbox") -> None:
        self.outbox_dir = Path(outbox_dir)

    def route(self, request: EscalationRequest) -> Path:
        if not request.canonical_output:
            raise EscalationRoutingError("canonical_output gate failed")

        if request.authority.value != "NOT_EARNED":
            raise EscalationRoutingError("authority must remain NOT_EARNED")

        if request.deployment.value != "PROHIBITED":
            raise EscalationRoutingError("deployment must remain PROHIBITED")

        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.outbox_dir / f"{request.request_id}.json"
        output_path.write_text(
            json.dumps(request.to_json_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return output_path


def load_request(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
