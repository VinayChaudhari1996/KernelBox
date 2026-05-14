"""Structured objects returned by kernelbox APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal


KernelStatus = Literal["running", "idle", "dead", "unknown"]
ExecutionStatus = Literal["success", "error", "timeout", "max_attempts_exceeded"]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass(slots=True)
class KernelRecord:
    kernel_id: str
    connection_file: str
    name: str | None = None
    created_at: str = field(default_factory=utc_now)
    last_used_at: str = field(default_factory=utc_now)
    status: KernelStatus = "running"
    session_name: str | None = None
    attempt_count: int = 0
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        return (datetime.now(UTC) - parse_timestamp(self.created_at)).total_seconds()

    def touch(self) -> None:
        self.last_used_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_id": self.kernel_id,
            "connection_file": self.connection_file,
            "name": self.name,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "status": self.status,
            "session_name": self.session_name,
            "attempt_count": self.attempt_count,
            "tags": dict(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KernelRecord":
        return cls(
            kernel_id=str(data["kernel_id"]),
            connection_file=str(data["connection_file"]),
            name=data.get("name"),
            created_at=str(data.get("created_at") or utc_now()),
            last_used_at=str(data.get("last_used_at") or utc_now()),
            status=data.get("status", "unknown"),
            session_name=data.get("session_name"),
            attempt_count=int(data.get("attempt_count", 0)),
            tags=dict(data.get("tags", {})),
        )


@dataclass(slots=True)
class ErrorInfo:
    ename: str
    evalue: str
    traceback: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ename": self.ename,
            "evalue": self.evalue,
            "traceback": list(self.traceback),
        }

    @classmethod
    def from_content(cls, content: dict[str, Any]) -> "ErrorInfo":
        return cls(
            ename=str(content.get("ename", "")),
            evalue=str(content.get("evalue", "")),
            traceback=list(content.get("traceback", [])),
        )


@dataclass(slots=True)
class OutputItem:
    kind: str
    text: str | None = None
    name: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "text": self.text,
            "name": self.name,
            "data": dict(self.data),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class AttemptSnapshot:
    attempt: int
    code: str
    status: ExecutionStatus
    output: str = ""
    stderr: str = ""
    error: ErrorInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "code": self.code,
            "status": self.status,
            "output": self.output,
            "stderr": self.stderr,
            "error": self.error.to_dict() if self.error else None,
        }


@dataclass(slots=True)
class ExecutionResult:
    status: ExecutionStatus
    output: str = ""
    stderr: str = ""
    error: ErrorInfo | None = None
    return_value: str | None = None
    execution_count: int | None = None
    duration_ms: int = 0
    outputs: list[OutputItem] = field(default_factory=list)
    attempts: list[AttemptSnapshot] = field(default_factory=list)
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def snapshot(self, attempt: int, code: str) -> AttemptSnapshot:
        return AttemptSnapshot(
            attempt=attempt,
            code=code,
            status=self.status,
            output=self.output,
            stderr=self.stderr,
            error=self.error,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "output": self.output,
            "stderr": self.stderr,
            "error": self.error.to_dict() if self.error else None,
            "return_value": self.return_value,
            "execution_count": self.execution_count,
            "duration_ms": self.duration_ms,
            "outputs": [item.to_dict() for item in self.outputs],
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "truncated": self.truncated,
        }

