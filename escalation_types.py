"""Typed E2 scaffolding for STEP_5_ESCALATION_OPS_PLUS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class AuthorityStatus(str, Enum):
    NOT_EARNED = "NOT_EARNED"


class DeploymentStatus(str, Enum):
    PROHIBITED = "PROHIBITED"


class EvidenceLevel(str, Enum):
    E2 = "E2"


class EscalationDecision(str, Enum):
    APPROVE_FOR_REVIEW_ONLY = "approve_for_review_only"
    REQUEST_REVISION = "request_revision"
    REJECT = "reject"
    DEFER = "defer"
    ESCALATE_TO_HUMAN_AUTHORITY = "escalate_to_human_authority"


ALLOWED_DECISIONS = {decision.value for decision in EscalationDecision}


@dataclass(frozen=True)
class EscalationRequest:
    request_id: str
    origin: str
    summary: str
    requested_decision: EscalationDecision
    canonical_output: bool
    schema_version: str = "0.1.0"
    artifact_type: str = "escalation_request"
    evidence_level: EvidenceLevel = EvidenceLevel.E2
    authority: AuthorityStatus = AuthorityStatus.NOT_EARNED
    deployment: DeploymentStatus = DeploymentStatus.PROHIBITED
    risk_flags: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["requested_decision"] = self.requested_decision.value
        data["evidence_level"] = self.evidence_level.value
        data["authority"] = self.authority.value
        data["deployment"] = self.deployment.value
        return data


@dataclass(frozen=True)
class EscalationReview:
    review_id: str
    request_id: str
    decision: EscalationDecision
    reviewer_role: str = "human_reviewer"
    schema_version: str = "0.1.0"
    artifact_type: str = "escalation_review"
    authority: AuthorityStatus = AuthorityStatus.NOT_EARNED
    deployment: DeploymentStatus = DeploymentStatus.PROHIBITED
    notes: str = ""
    required_followups: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        data["authority"] = self.authority.value
        data["deployment"] = self.deployment.value
        return data
