from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


load_dotenv()

from agents.code_agent import repair, run
from agents.models import (
  AgentResult,
  ApplyChangeRequest,
  RejectChangeRequest,
)
from tools.edit_tools import apply_change_set
from tools.test_tools import run_verification
from workflows.workflow_store import (
  MAX_REPAIR_ATTEMPTS,
  ProposalStatus,
  WorkflowStatus,
  get_proposal,
  get_workflow,
  increment_repair_attempts,
  set_proposal_status,
  set_workflow_status,
  update_workflow,
)


app = FastAPI()


class AnalyzeRequest(BaseModel):
  problem: str


@app.post("/analyze", response_model=AgentResult)
def analyze(request: AnalyzeRequest):
  return run(request.problem)


@app.post("/apply-change")
def apply_change(request: ApplyChangeRequest):
  try:
    workflow = get_workflow(
      request.workflow_id
    )

    proposal = get_proposal(
      workflow_id=request.workflow_id,
      proposal_id=request.proposal_id,
    )

  except ValueError as error:
    raise HTTPException(
      status_code=404,
      detail=str(error),
    )

  if (
    workflow["status"]
    != WorkflowStatus.AWAITING_APPROVAL
  ):
    raise HTTPException(
      status_code=400,
      detail=(
        "Workflow is not awaiting approval."
      ),
    )

  if proposal["status"] != ProposalStatus.PENDING:
    raise HTTPException(
      status_code=400,
      detail=(
        "Proposal is no longer pending."
      ),
    )

  set_workflow_status(
    request.workflow_id,
    WorkflowStatus.APPLYING,
  )

  try:
    change_result = apply_change_set(
      changes=proposal["changes"],
    )

  except ValueError as error:
    set_proposal_status(
      request.workflow_id,
      request.proposal_id,
      ProposalStatus.STALE,
    )

    set_workflow_status(
      request.workflow_id,
      WorkflowStatus.PROPOSAL_STALE,
    )

    raise HTTPException(
      status_code=409,
      detail=str(error),
    )

  except RuntimeError as error:
    set_workflow_status(
      request.workflow_id,
      WorkflowStatus.APPLY_FAILED,
    )

    raise HTTPException(
      status_code=500,
      detail=str(error),
    )

  set_proposal_status(
    request.workflow_id,
    request.proposal_id,
    ProposalStatus.APPLIED,
  )

  set_workflow_status(
    request.workflow_id,
    WorkflowStatus.TESTING,
  )

  verification_result = run_verification()

  status = (
    WorkflowStatus.COMPLETED
    if verification_result["success"]
    else WorkflowStatus.TESTS_FAILED
  )

  update_workflow(
    request.workflow_id,
    status=status,
    verification_result=verification_result,
    change_result=change_result,
  )

  return {
    "workflow_id": request.workflow_id,
    "proposal_id": request.proposal_id,
    "status": status,
    "change": change_result,
    "verification": verification_result,
  }


@app.post("/reject-change")
def reject_change(request: RejectChangeRequest):
  try:
    workflow = get_workflow(
      request.workflow_id
    )

    proposal = get_proposal(
      workflow_id=request.workflow_id,
      proposal_id=request.proposal_id,
    )

  except ValueError as error:
    raise HTTPException(
      status_code=404,
      detail=str(error),
    )

  if (
    workflow["status"]
    != WorkflowStatus.AWAITING_APPROVAL
  ):
    raise HTTPException(
      status_code=400,
      detail=(
        "Workflow is not awaiting approval."
      ),
    )

  if proposal["status"] != ProposalStatus.PENDING:
    raise HTTPException(
      status_code=400,
      detail=(
        "Proposal is no longer pending."
      ),
    )

  set_proposal_status(
    request.workflow_id,
    request.proposal_id,
    ProposalStatus.REJECTED,
  )

  set_workflow_status(
    request.workflow_id,
    WorkflowStatus.REJECTED,
  )

  return {
    "workflow_id": request.workflow_id,
    "proposal_id": request.proposal_id,
    "status": WorkflowStatus.REJECTED,
  }


@app.post(
  "/repair/{workflow_id}",
  response_model=AgentResult,
)
def repair_workflow(workflow_id: str):
  try:
    workflow = get_workflow(workflow_id)
  except ValueError as error:
    raise HTTPException(
      status_code=404,
      detail=str(error),
    )

  if (
    workflow["status"]
    != WorkflowStatus.TESTS_FAILED
  ):
    raise HTTPException(
      status_code=400,
      detail=(
        "Workflow can only be repaired "
        "when verification has failed."
      ),
    )

  if (
    workflow["repair_attempts"]
    >= MAX_REPAIR_ATTEMPTS
  ):
    set_workflow_status(
      workflow_id,
      WorkflowStatus.REPAIR_LIMIT_REACHED,
    )

    raise HTTPException(
      status_code=409,
      detail=(
        "Maximum repair attempts reached. "
        "Manual intervention is required."
      ),
    )

  increment_repair_attempts(workflow_id)

  return repair(
    workflow_id=workflow_id,
    problem=workflow["problem"],
    verification_result=workflow[
      "verification_result"
    ],
  )
