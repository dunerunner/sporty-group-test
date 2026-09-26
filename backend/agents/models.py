from typing import Any

from pydantic import BaseModel


class AgentStep(BaseModel):
  tool: str
  arguments: dict[str, Any]
  success: bool
  result: Any | None = None
  error: str | None = None


class AgentResult(BaseModel):
  workflow_id: str
  answer: str
  steps: list[AgentStep]
  proposal_id: str | None = None


class ApplyChangeRequest(BaseModel):
  workflow_id: str
  proposal_id: str


class RejectChangeRequest(BaseModel):
  workflow_id: str
  proposal_id: str
