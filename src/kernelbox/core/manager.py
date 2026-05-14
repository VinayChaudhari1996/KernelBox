"""Kernel lifecycle management."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
from queue import Empty
import subprocess
import uuid

from jupyter_client import BlockingKernelClient, KernelManager

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.exceptions import KernelAlreadyExists
from kernelbox.core.executor import KernelExecutor
from kernelbox.core.types import KernelRecord
from kernelbox.store.registry import Registry, create_registry


class KernelManagerService:
    def __init__(
        self,
        *,
        config: KernelBoxConfig | None = None,
        registry: Registry | None = None,
    ) -> None:
        self.config = config or KernelBoxConfig.from_env()
        self.registry = registry or create_registry(self.config)
        self._owned_managers: dict[str, KernelManager] = {}

    def create(
        self,
        *,
        name: str | None = None,
        session_name: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> KernelRecord:
        if name is not None:
            existing = self.registry.get_by_name(name)
            if existing is not None and self.ping(existing):
                raise KernelAlreadyExists(f"Kernel name already exists: {name}")
            if existing is not None:
                self.registry.remove(existing.kernel_id)

        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)
        manager = KernelBoxKernelManager(
            kernel_name=self.config.kernel_type,
            connection_file=str(
                self.config.runtime_dir / f"kernel-{uuid.uuid4().hex}.json"
            ),
        )
        manager.start_kernel(
            env=_kernel_environment(self.config.runtime_dir),
            extra_arguments=["--HistoryManager.enabled=False"],
            independent=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        client = manager.client()
        client.start_channels()
        try:
            client.wait_for_ready(timeout=self.config.execution_timeout)
        finally:
            client.stop_channels()

        kernel_id = _kernel_id_from_connection_file(manager.connection_file)
        record = KernelRecord(
            kernel_id=kernel_id,
            connection_file=str(manager.connection_file),
            name=name,
            session_name=session_name,
            tags=dict(tags or {}),
        )
        self._owned_managers[kernel_id] = manager
        self.registry.upsert(record)

        if self.config.startup_code:
            KernelExecutor(config=self.config, registry=self.registry).execute(
                record,
                self.config.startup_code,
            )

        return record

    def get(self, identifier: str) -> KernelRecord | None:
        return self.registry.get(identifier)

    def list(self, *, refresh: bool = False) -> list[KernelRecord]:
        records = self.registry.all()
        if refresh:
            records = [self._refresh(record) for record in records]
        return sorted(records, key=lambda record: record.created_at)

    def ping(self, kernel: KernelRecord | str, *, timeout: float = 2.0) -> bool:
        record = kernel if isinstance(kernel, KernelRecord) else self.registry.get(kernel)
        if record is None or not Path(record.connection_file).exists():
            if record is not None:
                record.status = "dead"
                self.registry.upsert(record)
            return False

        client = BlockingKernelClient()
        client.load_connection_file(record.connection_file)
        client.start_channels()
        alive = False
        try:
            msg_id = client.kernel_info()
            while True:
                try:
                    reply = client.get_shell_msg(timeout=timeout)
                except Empty:
                    break
                if reply.get("parent_header", {}).get("msg_id") == msg_id:
                    alive = reply.get("content", {}).get("status") == "ok"
                    break
        finally:
            client.stop_channels()

        record.status = "running" if alive else "dead"
        self.registry.upsert(record)
        return alive

    def restart(self, identifier: str) -> KernelRecord:
        record = self._require(identifier)
        manager = self._owned_managers.get(record.kernel_id)
        if manager is not None:
            manager.restart_kernel(now=True)
            client = manager.client()
            client.start_channels()
            try:
                client.wait_for_ready(timeout=self.config.execution_timeout)
            finally:
                client.stop_channels()
        else:
            result = KernelExecutor(config=self.config, registry=self.registry).execute(
                record,
                "%reset -f",
            )
            if not result.ok:
                record.status = "unknown"
                self.registry.upsert(record)
                return record

        record.status = "running"
        record.touch()
        self.registry.upsert(record)
        return record

    def destroy(self, identifier: str) -> bool:
        record = self.registry.get(identifier)
        if record is None:
            return False

        manager = self._owned_managers.pop(record.kernel_id, None)
        try:
            if manager is not None:
                manager.shutdown_kernel(now=True)
            elif Path(record.connection_file).exists():
                client = BlockingKernelClient()
                client.load_connection_file(record.connection_file)
                client.start_channels()
                try:
                    client.shutdown()
                finally:
                    client.stop_channels()
        finally:
            self.registry.remove(record.kernel_id)
        return True

    def wipe_all(self) -> list[str]:
        destroyed: list[str] = []
        for record in self.registry.all():
            if self.destroy(record.kernel_id):
                destroyed.append(record.kernel_id)
        return destroyed

    def _refresh(self, record: KernelRecord) -> KernelRecord:
        self.ping(record)
        refreshed = self.registry.get(record.kernel_id)
        return refreshed or record

    def _require(self, identifier: str) -> KernelRecord:
        record = self.registry.get(identifier)
        if record is None:
            raise KeyError(f"Unknown kernel: {identifier}")
        return record


def _kernel_id_from_connection_file(connection_file: str) -> str:
    stem = Path(connection_file).stem
    if stem.startswith("kernel-") and len(stem) > len("kernel-"):
        return stem[len("kernel-") :]
    return uuid.uuid4().hex


def _kernel_environment(runtime_dir: Path) -> dict[str, str]:
    ipython_dir = runtime_dir / "ipython"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    ipython_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("JUPYTER_RUNTIME_DIR", str(runtime_dir))
    env.setdefault("IPYTHONDIR", str(ipython_dir))
    return env


class KernelBoxKernelManager(KernelManager):
    def write_connection_file(self, **kwargs):
        try:
            return super().write_connection_file(**kwargs)
        except Exception as exc:
            if not _is_windows_acl_denied(exc):
                raise
            with _without_windows_acl_restriction():
                return super().write_connection_file(**kwargs)

    def cleanup_connection_file(self):
        pass


def _is_windows_acl_denied(exc: Exception) -> bool:
    if os.name != "nt":
        return False
    if isinstance(exc, PermissionError) and getattr(exc, "winerror", None) == 5:
        return True
    text = str(exc)
    return "Access is denied" in text and (
        "SetFileSecurity" in text or "WinError 5" in text
    )


@contextmanager
def _without_windows_acl_restriction():
    import jupyter_core.paths as jupyter_paths

    original = getattr(jupyter_paths, "win32_restrict_file_to_user", None)
    if original is None:
        yield
        return

    jupyter_paths.win32_restrict_file_to_user = lambda _fname: None
    try:
        yield
    finally:
        jupyter_paths.win32_restrict_file_to_user = original
