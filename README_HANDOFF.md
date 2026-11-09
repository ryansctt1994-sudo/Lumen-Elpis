# Lumen-Elpis STEP_5_ESCALATION_OPS_PLUS Handoff

Status: E2 scaffold only.  
Authority: NOT_EARNED.  
Deployment: PROHIBITED.  
External integrations: PROHIBITED.  
Router mode: file-based only.

This branch adds minimal Step 5 escalation-operations scaffolding for governance review. The implementation is intentionally bounded: cognition may propose, but this code does not grant authority, does not deploy, does not call external systems, and does not treat generated review text as execution permission.

## Included artifacts

- `escalations/escalation_policy.json` — policy outline and allowed decisions.
- `escalations/escalation_request_example.json` — example escalation request.
- `escalations/review_example.json` — example review record.
- `escalation_types.py` — dataclasses and enums matching the JSON artifacts.
- `escalation_router.py` — local file-based router that writes escalation requests to `escalations/outbox/`.
- `tests/test_escalation_operations.py` — minimal pytest tests for gate behavior and file output.
- `semantic_closure/semantic_closure_card.json` — example semantic closure artifact.
- `mission_integrity/mission_integrity_check.json` — example mission integrity artifact.
- `influence_traces/influence_trace.json` — example influence trace artifact.
- `authority_conversion/authority_conversion_record.json` — example authority conversion record.

## Definition of Done for this E2 scaffold

1. Escalation requests are representable as JSON-compatible dataclasses.
2. Router writes only to local files.
3. Router fails closed when `canonical_output` is false.
4. Allowed review decisions are explicit and bounded.
5. No external system integration exists in this branch.
6. No artifact claims earned authority or deployment eligibility.

## Run tests

```bash
python -m pytest tests/test_escalation_operations.py
```

## Router safety hardening (draft, dependent on scaffold PR #1)

The file-based E2 router now refuses unsafe/non-ASCII request IDs, dot path
traversal and overwrite attempts, including pre-existing symlinked files.
It refuses symlinked outbox directories, requires literal enum/boolean
governance status fields, validates JSON before creating the output folder,
and reads JSON with duplicate-key and nonfinite-number rejection. These are
local file-integrity and parsing controls, **not** independent witness
attestations, permission to deploy, an OS sandbox, or cross-process durable
transaction guarantees. A temporary created file can still be partially
written if a disk write fails, and a privileged adversary with write access
to the outbox's parent directory is outside this simple router's threat model.

GitHub Actions now checks the bounded tests on Python 3.11–3.13. Main remains
the E0 incubator until any separately authorized review and merge. Draft
green checks do not raise the portfolio's evidence ceiling or authority.

## Next milestone

STEP_5_ESCALATION_OPS_PLUS remains blocked on validation plus escalation governance. Before promotion beyond E2, the project needs hardened schemas, receipt hashing, replay checks, negative-path tests, reviewer identity policy, and independent audit evidence.
