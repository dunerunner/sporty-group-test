import json
import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from pydantic import BaseModel


MAX_REPAIR_ATTEMPTS = int(
  os.getenv("MAX_REPAIR_ATTEMPTS", "3")
)
MAX_STORED_WORKFLOWS = int(
  os.getenv("MAX_STORED_WORKFLOWS", "200")
)
MAX_PROPOSALS_PER_WORKFLOW = int(
  os.getenv("MAX_PROPOSALS_PER_WORKFLOW", "10")
)
MAX_PROPOSAL_FILES = int(
  os.getenv("MAX_PROPOSAL_FILES", "20")
)
MAX_PROPOSAL_TOTAL_BYTES = int(
  os.getenv("MAX_PROPOSAL_TOTAL_BYTES", "1000000")
)
MAX_PROPOSAL_FILE_BYTES = int(
  os.getenv("MAX_PROPOSAL_FILE_BYTES", "200000")
)

DATA_DIR = Path(__file__).resolve().parents[1] / ".data"
WORKFLOW_STORE_PATH = DATA_DIR / "workflows.json"

_lock = RLock()
_active_workflow_operations: set[str] = set()


class WorkflowStatus(StrEnum):
  ANALYZING = "analyzing"
  AWAITING_APPROVAL = "awaiting_approval"
  APPLYING = "applying"
  VERIFYING = "verifying"
  VERIFICATION_FAILED = "verification_failed"
  COMPLETED = "completed"
  REJECTED = "rejected"
  PROPOSAL_STALE = "proposal_stale"
  APPLY_FAILED = "apply_failed"
  REPAIR_LIMIT_REACHED = "repair_limit_reached"


class ProposalStatus(StrEnum):
  PENDING = "pending"
  APPLIED = "applied"
  REJECTED = "rejected"
  STALE = "stale"


workflows: dict[str, dict] = {}


def _now() -> str:
  return datetime.now(UTC).isoformat()


def _normalize_status(value: str) -> WorkflowStatus:
  migrations = {
    "testing": WorkflowStatus.VERIFYING,
    "tests_failed": WorkflowStatus.VERIFICATION_FAILED,
  }

  return migrations.get(value, WorkflowStatus(value))


def _to_jsonable(value: Any) -> Any:
  if isinstance(value, BaseModel):
    return _to_jsonable(value.model_dump())

  if isinstance(value, StrEnum):
    return str(value)

  if isinstance(value, dict):
    return {
      str(key): _to_jsonable(item)
      for key, item in value.items()
    }

  if isinstance(value, list):
    return [
      _to_jsonable(item)
      for item in value
    ]

  return value


def _serialize_workflow(workflow: dict) -> dict:
  return {
    **_to_jsonable(workflow),
    "status": str(workflow["status"]),
    "proposals": {
      proposal_id: {
        **_to_jsonable(proposal),
        "status": str(proposal["status"]),
      }
      for proposal_id, proposal in workflow[
        "proposals"
      ].items()
    },
  }


def _deserialize_workflow(workflow: dict) -> dict:
  return {
    **workflow,
    "status": _normalize_status(workflow["status"]),
    "proposals": {
      proposal_id: {
        **proposal,
        "status": ProposalStatus(
          proposal["status"]
        ),
      }
      for proposal_id, proposal in workflow.get(
        "proposals",
        {},
      ).items()
    },
  }


def _persist() -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)

  payload = {
    "version": 1,
    "workflows": {
      workflow_id: _serialize_workflow(workflow)
      for workflow_id, workflow in workflows.items()
    },
  }

  temporary_path = WORKFLOW_STORE_PATH.with_suffix(
    ".json.tmp"
  )

  temporary_path.write_text(
    json.dumps(payload, indent=2, sort_keys=True),
    encoding="utf-8",
  )
  temporary_path.replace(WORKFLOW_STORE_PATH)


def _load() -> None:
  if not WORKFLOW_STORE_PATH.exists():
    return

  payload = json.loads(
    WORKFLOW_STORE_PATH.read_text(encoding="utf-8")
  )

  loaded = payload.get("workflows", {})

  workflows.update(
    {
      workflow_id: _deserialize_workflow(workflow)
      for workflow_id, workflow in loaded.items()
    }
  )


def _prune_workflows_if_needed(
  required_capacity: int = 0,
) -> None:
  if (
    len(workflows) + required_capacity
    <= MAX_STORED_WORKFLOWS
  ):
    return

  terminal_statuses = {
    WorkflowStatus.COMPLETED,
    WorkflowStatus.REJECTED,
    WorkflowStatus.PROPOSAL_STALE,
    WorkflowStatus.APPLY_FAILED,
    WorkflowStatus.REPAIR_LIMIT_REACHED,
  }

  candidates = sorted(
    (
      workflow
      for workflow in workflows.values()
      if workflow["status"] in terminal_statuses
    ),
    key=lambda workflow: workflow.get(
      "updated_at",
      workflow.get("created_at", ""),
    ),
  )

  while (
    len(workflows) + required_capacity
    > MAX_STORED_WORKFLOWS
    and candidates
  ):
    workflow = candidates.pop(0)
    workflows.pop(workflow["id"], None)

  if (
    len(workflows) + required_capacity
    > MAX_STORED_WORKFLOWS
  ):
    raise RuntimeError(
      "Workflow store limit reached. Complete or remove "
      "existing workflows before starting a new one."
    )


def _validate_proposal_changes(
  changes: list[dict],
) -> None:
  if not changes:
    raise ValueError("Proposal must contain at least one file.")

  if len(changes) > MAX_PROPOSAL_FILES:
    raise ValueError(
      "Proposal contains too many files. "
      f"Limit: {MAX_PROPOSAL_FILES}."
    )

  total_bytes = 0

  for change in changes:
    content = change.get("proposed_content", "")
    content_size = len(
      content.encode("utf-8")
    )

    if content_size > MAX_PROPOSAL_FILE_BYTES:
      raise ValueError(
        "Proposed file content is too large: "
        f"{change.get('path', '<unknown>')}."
      )

    total_bytes += content_size

  if total_bytes > MAX_PROPOSAL_TOTAL_BYTES:
    raise ValueError(
      "Proposal is too large. "
      f"Limit: {MAX_PROPOSAL_TOTAL_BYTES} bytes."
    )


_load()


def create_workflow(problem: str) -> str:
  with _lock:
    _prune_workflows_if_needed(required_capacity=1)

    workflow_id = str(uuid4())
    timestamp = _now()

    workflows[workflow_id] = {
      "id": workflow_id,
      "problem": problem,
      "status": WorkflowStatus.ANALYZING,
      "test_result": None,
      "proposals": {},
      "current_proposal_id": None,
      "repair_attempts": 0,
      "created_at": timestamp,
      "updated_at": timestamp,
    }

    _persist()

    return workflow_id


def get_workflow(workflow_id: str) -> dict:
  with _lock:
    workflow = workflows.get(workflow_id)

    if workflow is None:
      raise ValueError(
        f"Workflow not found: {workflow_id}"
      )

    return workflow


def update_workflow(
  workflow_id: str,
  **updates,
) -> dict:
  with _lock:
    workflow = get_workflow(workflow_id)

    workflow.update(updates)
    workflow["updated_at"] = _now()

    _persist()

    return workflow


def set_workflow_status(
  workflow_id: str,
  status: WorkflowStatus,
) -> dict:
  with _lock:
    workflow = get_workflow(workflow_id)

    workflow["status"] = status
    workflow["updated_at"] = _now()

    _persist()

    return workflow


def increment_repair_attempts(
  workflow_id: str,
) -> int:
  with _lock:
    workflow = get_workflow(workflow_id)

    workflow["repair_attempts"] += 1
    workflow["updated_at"] = _now()

    _persist()

    return workflow["repair_attempts"]


def store_proposal(
  workflow_id: str,
  changes: list[dict],
) -> str:
  with _lock:
    _validate_proposal_changes(changes)

    workflow = get_workflow(workflow_id)

    if (
      len(workflow["proposals"])
      >= MAX_PROPOSALS_PER_WORKFLOW
    ):
      raise RuntimeError(
        "Workflow proposal limit reached."
      )

    proposal_id = str(uuid4())
    timestamp = _now()

    workflow["proposals"][proposal_id] = {
      "id": proposal_id,
      "changes": changes,
      "status": ProposalStatus.PENDING,
      "created_at": timestamp,
      "updated_at": timestamp,
    }

    workflow["current_proposal_id"] = proposal_id
    workflow["updated_at"] = timestamp

    _persist()

    return proposal_id


def get_proposal(
  workflow_id: str,
  proposal_id: str,
) -> dict:
  with _lock:
    workflow = get_workflow(workflow_id)

    proposal = workflow["proposals"].get(
      proposal_id
    )

    if proposal is None:
      raise ValueError(
        f"Proposal not found: {proposal_id}"
      )

    return proposal


def set_proposal_status(
  workflow_id: str,
  proposal_id: str,
  status: ProposalStatus,
) -> dict:
  with _lock:
    proposal = get_proposal(
      workflow_id=workflow_id,
      proposal_id=proposal_id,
    )

    proposal["status"] = status
    proposal["updated_at"] = _now()

    get_workflow(workflow_id)["updated_at"] = _now()

    _persist()

    return proposal


def acquire_workflow_operation(
  workflow_id: str,
) -> None:
  with _lock:
    if workflow_id in _active_workflow_operations:
      raise RuntimeError(
        "Workflow already has an operation in progress."
      )

    get_workflow(workflow_id)
    _active_workflow_operations.add(workflow_id)


def release_workflow_operation(
  workflow_id: str,
) -> None:
  with _lock:
    _active_workflow_operations.discard(workflow_id)
