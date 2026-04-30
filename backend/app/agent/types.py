"""Agent-side protocol models for normalized input and execution."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import TextPart


ArtifactType = Literal["text", "image_url", "image_base64", "audio_url", "file_ref"]


class InputArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ArtifactType
    content: str = Field(default="", description="Normalized content or reference value.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedAgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str
    user_text: str = Field(default="", description="Merged user text content.")
    text_parts: list[TextPart] = Field(default_factory=list)
    artifacts: list[InputArtifact] = Field(default_factory=list)


PlanStepType = Literal["call_skill", "call_service", "respond"]
StepStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1, max_length=64)
    type: PlanStepType
    name: str = Field(default="", description="Human-readable step name.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Step input payload.")
    depends_on: list[str] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    status: StepStatus
    duration_ms: int = Field(default=0, ge=0)
    error: str | None = None
    output_summary: str = ""


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed", "partial"]
    traces: list[ExecutionTrace] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=dict)

