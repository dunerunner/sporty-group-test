from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


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
  acquire_workflow_operation,
  get_proposal,
  get_workflow,
  increment_repair_attempts,
  release_workflow_operation,
  set_proposal_status,
  set_workflow_status,
  update_workflow,
)


MAX_PROBLEM_LENGTH = 4000

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:4200",
    "http://localhost:4300",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:4300",
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
  problem: str = Field(
    min_length=1,
    max_length=MAX_PROBLEM_LENGTH,
  )


@app.post("/analyze", response_model=AgentResult)
def analyze(request: AnalyzeRequest):
  problem = request.problem.strip()

  if not problem:
    raise HTTPException(
      status_code=400,
      detail="Problem must not be empty.",
    )

  return run(problem)


@app.get("/workflow/{workflow_id}")
def read_workflow(workflow_id: str):
  try:
    workflow = get_workflow(workflow_id)
  except ValueError as error:
    raise HTTPException(
      status_code=404,
      detail=str(error),
    )

  return workflow


@app.post("/apply-change")
def apply_change(request: ApplyChangeRequest):
  try:
    acquire_workflow_operation(
      request.workflow_id
    )
  except ValueError as error:
    raise HTTPException(
      status_code=404,
      detail=str(error),
    )
  except RuntimeError as error:
    raise HTTPException(
      status_code=409,
      detail=str(error),
    )

  try:
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

    if workflow["status"] != WorkflowStatus.AWAITING_APPROVAL:
      raise HTTPException(
        status_code=400,
        detail="Workflow is not awaiting approval.",
      )

    if proposal["status"] != ProposalStatus.PENDING:
      raise HTTPException(
        status_code=400,
        detail="Proposal is no longer pending.",
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
      WorkflowStatus.VERIFYING,
    )

    verification_result = run_verification()

    status = (
      WorkflowStatus.COMPLETED
      if verification_result["success"]
      else WorkflowStatus.VERIFICATION_FAILED
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

  finally:
    release_workflow_operation(
      request.workflow_id
    )


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
    acquire_workflow_operation(workflow_id)
  except ValueError as error:
    raise HTTPException(
      status_code=404,
      detail=str(error),
    )
  except RuntimeError as error:
    raise HTTPException(
      status_code=409,
      detail=str(error),
    )

  try:
    try:
      workflow = get_workflow(workflow_id)
    except ValueError as error:
      raise HTTPException(
        status_code=404,
        detail=str(error),
      )

    if (
      workflow["status"]
      != WorkflowStatus.VERIFICATION_FAILED
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

  finally:
    release_workflow_operation(workflow_id)
