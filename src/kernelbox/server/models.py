"""Pydantic models for the KernelBox HTTP API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from kernelbox.core.types import (
    AttemptSnapshot,
    ErrorInfo,
    ExecutionResult,
    KernelRecord,
    OutputItem,
)


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(description="Service health status.")
    service: str = Field(description="Service name.")
    version: str = Field(description="KernelBox API version.")


class ApiLink(BaseModel):
    href: str
    description: str


class RootResponse(BaseModel):
    service: str
    links: dict[str, ApiLink]


class KernelCreateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        description="Optional human-readable alias for the kernel.",
        examples=["data-analysis"],
    )
    session_name: str | None = Field(
        default=None,
        description="Optional session name to associate with this kernel.",
        examples=["agent-run-42"],
    )
    tags: dict[str, str] = Field(
        default_factory=dict,
        description="Optional agent-defined labels for later inspection.",
        examples=[{"task": "eda", "owner": "agent"}],
    )


class SessionCreateRequest(BaseModel):
    tags: dict[str, str] = Field(
        default_factory=dict,
        description="Optional labels to apply if the session creates a new kernel.",
    )


class KernelModel(BaseModel):
    kernel_id: str = Field(description="Internal Jupyter kernel ID.")
    connection_file: str = Field(description="Path to the Jupyter connection file.")
    name: str | None = Field(description="Optional human-readable alias.")
    created_at: str = Field(description="ISO timestamp for kernel creation.")
    last_used_at: str = Field(description="ISO timestamp for last registry touch.")
    status: str = Field(description="Best-known status: running, idle, dead, or unknown.")
    session_name: str | None = Field(description="Session associated with this kernel.")
    attempt_count: int = Field(description="Number of retry attempts tracked in the store.")
    tags: dict[str, str] = Field(description="Agent-defined labels.")
    age_seconds: float = Field(description="Approximate age in seconds.")

    @classmethod
    def from_record(cls, record: KernelRecord) -> "KernelModel":
        payload = record.to_dict()
        payload["age_seconds"] = record.age_seconds
        return cls(**payload)


class KernelListResponse(BaseModel):
    kernels: list[KernelModel]


class KernelStatusResponse(BaseModel):
    alive: bool = Field(description="Whether the kernel responded to kernel_info.")
    kernel: KernelModel


class KernelDestroyedResponse(BaseModel):
    destroyed: bool


class KernelWipeResponse(BaseModel):
    destroyed: list[str] = Field(description="Kernel IDs removed from the registry.")


class ExecuteRequest(BaseModel):
    code: str = Field(
        description="Raw code to run in the target kernel.",
        examples=["import math\nmath.sqrt(81)"],
    )
    language: Literal["python", "bash"] = Field(
        default="python",
        description="Execution language. Bash is sent through IPython's %%bash magic.",
    )
    timeout: float | None = Field(
        default=None,
        ge=0.1,
        description="Optional per-execution timeout in seconds.",
        examples=[30],
    )


class RetryExecuteRequest(ExecuteRequest):
    max_attempts: int | None = Field(
        default=None,
        ge=1,
        description="Maximum execution attempts. Defaults to KernelBox config.",
        examples=[5],
    )
    replacement_codes: list[str] = Field(
        default_factory=list,
        description=(
            "Optional replacement code snippets used after failures. "
            "The first replacement is used after attempt 1 fails."
        ),
    )


class ErrorInfoModel(BaseModel):
    ename: str
    evalue: str
    traceback: list[str] = Field(default_factory=list)

    @classmethod
    def from_error(cls, error: ErrorInfo) -> "ErrorInfoModel":
        return cls(**error.to_dict())


class OutputItemModel(BaseModel):
    kind: str
    text: str | None = None
    name: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_item(cls, item: OutputItem) -> "OutputItemModel":
        return cls(**item.to_dict())


class AttemptSnapshotModel(BaseModel):
    attempt: int
    code: str
    status: str
    output: str = ""
    stderr: str = ""
    error: ErrorInfoModel | None = None

    @classmethod
    def from_attempt(cls, attempt: AttemptSnapshot) -> "AttemptSnapshotModel":
        payload = attempt.to_dict()
        if attempt.error is not None:
            payload["error"] = ErrorInfoModel.from_error(attempt.error)
        return cls(**payload)


class ExecutionResultModel(BaseModel):
    status: str = Field(description="success, error, timeout, or max_attempts_exceeded.")
    output: str = Field(description="Collected stdout text.")
    stderr: str = Field(description="Collected stderr text.")
    error: ErrorInfoModel | None = Field(description="Structured exception data, if any.")
    return_value: str | None = Field(description="text/plain value for the final expression.")
    execution_count: int | None = Field(description="Kernel execution counter.")
    duration_ms: int = Field(description="Wall-clock duration in milliseconds.")
    outputs: list[OutputItemModel] = Field(description="All structured output events.")
    attempts: list[AttemptSnapshotModel] = Field(description="Retry attempt history.")
    truncated: bool = Field(description="Whether output was truncated by config limits.")

    @classmethod
    def from_result(cls, result: ExecutionResult) -> "ExecutionResultModel":
        return cls(
            status=result.status,
            output=result.output,
            stderr=result.stderr,
            error=ErrorInfoModel.from_error(result.error) if result.error else None,
            return_value=result.return_value,
            execution_count=result.execution_count,
            duration_ms=result.duration_ms,
            outputs=[OutputItemModel.from_item(item) for item in result.outputs],
            attempts=[
                AttemptSnapshotModel.from_attempt(attempt)
                for attempt in result.attempts
            ],
            truncated=result.truncated,
        )

