"""Retry controller with caller-owned repair logic."""

from __future__ import annotations

from collections.abc import Callable

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.executor import KernelExecutor
from kernelbox.core.types import ExecutionResult, KernelRecord
from kernelbox.store.registry import Registry


class RetryController:
    def __init__(
        self,
        *,
        executor: KernelExecutor,
        config: KernelBoxConfig | None = None,
        registry: Registry | None = None,
    ) -> None:
        self.executor = executor
        self.config = config or KernelBoxConfig.from_env()
        self.registry = registry

    def execute_with_retry(
        self,
        kernel: KernelRecord,
        code: str,
        *,
        on_error_fn: Callable[[ExecutionResult, int], str | None],
        max_attempts: int | None = None,
        language: str = "python",
        timeout: float | None = None,
    ) -> ExecutionResult:
        attempts_allowed = max_attempts or self.config.max_retries
        current_code = code
        snapshots = []

        for attempt in range(1, attempts_allowed + 1):
            if self.registry is not None:
                self.registry.increment_attempt_count(kernel.kernel_id)

            result = self.executor.execute(
                kernel,
                current_code,
                language=language,
                timeout=timeout,
            )
            snapshots.append(result.snapshot(attempt, current_code))
            result.attempts = list(snapshots)
            if result.ok:
                return result
            if attempt == attempts_allowed:
                return ExecutionResult(
                    status="max_attempts_exceeded",
                    output=result.output,
                    stderr=result.stderr,
                    error=result.error,
                    return_value=result.return_value,
                    execution_count=result.execution_count,
                    duration_ms=result.duration_ms,
                    outputs=result.outputs,
                    attempts=list(snapshots),
                    truncated=result.truncated,
                )

            replacement = on_error_fn(result, attempt)
            if replacement is not None:
                current_code = replacement

        raise RuntimeError("unreachable retry loop state")

