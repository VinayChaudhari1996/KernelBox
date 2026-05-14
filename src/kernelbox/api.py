"""Small public API for agents."""

from __future__ import annotations

from collections.abc import Callable

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.executor import KernelExecutor
from kernelbox.core.manager import KernelManagerService
from kernelbox.core.retry import RetryController
from kernelbox.core.session import SessionManager
from kernelbox.core.types import ExecutionResult, KernelRecord
from kernelbox.store.registry import create_registry


_config = KernelBoxConfig.from_env()
_registry = create_registry(_config)
_manager = KernelManagerService(config=_config, registry=_registry)
_sessions = SessionManager(manager=_manager, registry=_registry)
_executor = KernelExecutor(config=_config, registry=_registry)
_retry = RetryController(executor=_executor, config=_config, registry=_registry)


def get_or_create(name: str) -> KernelRecord:
    """Return a live named kernel, creating it if needed."""

    return _sessions.get_or_create(name)


def execute(
    kernel: KernelRecord | str,
    code: str,
    *,
    language: str = "python",
    timeout: float | None = None,
) -> ExecutionResult:
    """Execute code in a kernel and return a structured result."""

    record = _coerce_kernel(kernel)
    return _executor.execute(record, code, language=language, timeout=timeout)


def execute_with_retry(
    kernel: KernelRecord | str,
    code: str,
    on_error_fn: Callable[[ExecutionResult, int], str | None],
    *,
    max_attempts: int | None = None,
    language: str = "python",
    timeout: float | None = None,
) -> ExecutionResult:
    """Execute code with a caller-provided repair callback."""

    record = _coerce_kernel(kernel)
    return _retry.execute_with_retry(
        record,
        code,
        on_error_fn=on_error_fn,
        max_attempts=max_attempts,
        language=language,
        timeout=timeout,
    )


def destroy(name: str) -> bool:
    """Destroy a kernel by session name, alias, or kernel ID."""

    return _manager.destroy(name)


def _coerce_kernel(kernel: KernelRecord | str) -> KernelRecord:
    if isinstance(kernel, KernelRecord):
        return kernel

    record = _registry.get(kernel)
    if record is None:
        record = _sessions.get_or_create(kernel)
    return record

