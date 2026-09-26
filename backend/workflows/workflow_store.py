from enum import StrEnum
from uuid import uuid4


MAX_REPAIR_ATTEMPTS = 3


class WorkflowStatus(StrEnum):
  ANALYZING = "analyzing"
  AWAITING_APPROVAL = "awaiting_approval"
  APPLYING = "applying"
  TESTING = "testing"
  TESTS_FAILED = "tests_failed"
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


def create_workflow(problem: str) -> str:
  workflow_id = str(uuid4())

  workflows[workflow_id] = {
    "problem": problem,
    "status": WorkflowStatus.ANALYZING,
    "test_result": None,
    "proposals": {},
    "current_proposal_id": None,
    "repair_attempts": 0,
  }

  return workflow_id


def get_workflow(workflow_id: str) -> dict:
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
  workflow = get_workflow(workflow_id)

  workflow.update(updates)

  return workflow


def set_workflow_status(
  workflow_id: str,
  status: WorkflowStatus,
) -> dict:
  workflow = get_workflow(workflow_id)

  workflow["status"] = status

  return workflow


def increment_repair_attempts(
  workflow_id: str,
) -> int:
  workflow = get_workflow(workflow_id)

  workflow["repair_attempts"] += 1

  return workflow["repair_attempts"]


def store_proposal(
  workflow_id: str,
  changes: list[dict],
) -> str:
  workflow = get_workflow(workflow_id)

  proposal_id = str(uuid4())

  workflow["proposals"][proposal_id] = {
    "id": proposal_id,
    "changes": changes,
    "status": ProposalStatus.PENDING,
  }

  workflow["current_proposal_id"] = proposal_id

  return proposal_id


def get_proposal(
  workflow_id: str,
  proposal_id: str,
) -> dict:
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
  proposal = get_proposal(
    workflow_id=workflow_id,
    proposal_id=proposal_id,
  )

  proposal["status"] = status

  return proposal
