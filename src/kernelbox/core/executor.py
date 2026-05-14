"""Code execution against a live Jupyter kernel."""

from __future__ import annotations

from queue import Empty
import time
from typing import Any

from jupyter_client import BlockingKernelClient

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.types import ErrorInfo, ExecutionResult, KernelRecord, OutputItem
from kernelbox.store.registry import Registry


class KernelExecutor:
    def __init__(
        self,
        *,
        config: KernelBoxConfig | None = None,
        registry: Registry | None = None,
    ) -> None:
        self.config = config or KernelBoxConfig.from_env()
        self.registry = registry

    def execute(
        self,
        kernel: KernelRecord,
        code: str,
        *,
        language: str = "python",
        timeout: float | None = None,
        silent: bool = False,
    ) -> ExecutionResult:
        started = time.perf_counter()
        limit = timeout if timeout is not None else self.config.execution_timeout
        prepared_code = _prepare_code(code, language)
        client = _client_from_record(kernel)
        client.start_channels()

        outputs: list[OutputItem] = []
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        return_value: str | None = None
        execution_count: int | None = None
        error: ErrorInfo | None = None
        status = "success"
        truncated = False

        try:
            msg_id = client.execute(prepared_code, silent=silent, store_history=not silent)
            deadline = time.monotonic() + limit

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    status = "timeout"
                    break

                try:
                    message = client.get_iopub_msg(timeout=remaining)
                except Empty:
                    status = "timeout"
                    break

                if message.get("parent_header", {}).get("msg_id") != msg_id:
                    continue

                message_type = message.get("header", {}).get("msg_type")
                content: dict[str, Any] = message.get("content", {})

                if message_type == "status" and content.get("execution_state") == "idle":
                    break
                if message_type == "execute_input":
                    execution_count = content.get("execution_count")
                    continue
                if message_type == "stream":
                    text = str(content.get("text", ""))
                    name = str(content.get("name", "stdout"))
                    outputs.append(OutputItem(kind="stream", name=name, text=text))
                    if name == "stderr":
                        stderr_parts.append(text)
                    else:
                        stdout_parts.append(text)
                    continue
                if message_type in {"display_data", "execute_result"}:
                    data = dict(content.get("data", {}))
                    metadata = dict(content.get("metadata", {}))
                    text_value = data.get("text/plain")
                    outputs.append(
                        OutputItem(
                            kind=str(message_type),
                            text=text_value,
                            data=data,
                            metadata=metadata,
                        )
                    )
                    if message_type == "execute_result":
                        return_value = text_value
                        execution_count = content.get("execution_count", execution_count)
                    continue
                if message_type == "error":
                    error = ErrorInfo.from_content(content)
                    outputs.append(
                        OutputItem(
                            kind="error",
                            text=f"{error.ename}: {error.evalue}",
                            data=error.to_dict(),
                        )
                    )
                    status = "error"

            if status != "timeout":
                shell_status, shell_error = _read_shell_reply(client, msg_id, deadline)
                if shell_status == "timeout":
                    status = "timeout"
                elif shell_status == "error":
                    status = "error"
                    error = error or shell_error
        finally:
            client.stop_channels()

        output, was_truncated = _limit_text("".join(stdout_parts), self.config.output_char_limit)
        stderr, stderr_truncated = _limit_text(
            "".join(stderr_parts),
            self.config.output_char_limit,
        )
        truncated = truncated or was_truncated or stderr_truncated

        for item in outputs:
            if item.text:
                item.text, item_truncated = _limit_text(
                    item.text,
                    self.config.output_char_limit,
                )
                truncated = truncated or item_truncated

        kernel.touch()
        if self.registry is not None:
            self.registry.upsert(kernel)

        return ExecutionResult(
            status=status,
            output=output,
            stderr=stderr,
            error=error,
            return_value=return_value,
            execution_count=execution_count,
            duration_ms=int((time.perf_counter() - started) * 1000),
            outputs=outputs,
            truncated=truncated,
        )


def _client_from_record(record: KernelRecord) -> BlockingKernelClient:
    client = BlockingKernelClient()
    client.load_connection_file(record.connection_file)
    return client


def _prepare_code(code: str, language: str) -> str:
    normalized = language.lower()
    if normalized in {"python", "py"}:
        return code
    if normalized in {"bash", "sh", "shell"}:
        return "%%bash\n" + code
    raise ValueError(f"Unsupported execution language: {language}")


def _read_shell_reply(
    client: BlockingKernelClient,
    msg_id: str,
    deadline: float,
) -> tuple[str, ErrorInfo | None]:
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "timeout", None
        try:
            reply = client.get_shell_msg(timeout=remaining)
        except Empty:
            return "timeout", None
        if reply.get("parent_header", {}).get("msg_id") != msg_id:
            continue
        content = reply.get("content", {})
        if content.get("status") == "error":
            return "error", ErrorInfo.from_content(content)
        return "success", None


def _limit_text(value: str, limit: int) -> tuple[str, bool]:
    if limit <= 0 or len(value) <= limit:
        return value, False
    marker = "\n...[truncated by kernelbox]..."
    keep = max(0, limit - len(marker))
    return value[:keep] + marker, True

