from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    n: int = Field(description="Step sequence number (1-indexed)")
    intent: str = Field(description="Human-readable description of what this step does")
    tool: Optional[str] = Field(default=None, description="Tool name: code.run, fs.read, fs.write, deliver.docx, deliver.xlsx")
    args: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arguments for the tool")
    success_criterion: str = Field(description="How to verify this step succeeded")
    status: str = Field(default="pending", description="pending | running | completed | failed | repaired")
    result: Optional[str] = Field(default=None, description="Observation or output of the step")
    error: Optional[str] = Field(default=None, description="Error message if step failed")

class Plan(BaseModel):
    goal: str = Field(description="The primary objective of the plan")
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute")
    deliverables: List[str] = Field(default_factory=list, description="Target artifact names, e.g. approval_note.docx")

class AgentRunState(BaseModel):
    session_id: str
    goal: str
    plan: Optional[Plan] = None
    current_step: int = 0
    artifacts: List[str] = Field(default_factory=list)
    completed: bool = False
    error: Optional[str] = None
