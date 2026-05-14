"""Named session handling on top of kernel records."""

from __future__ import annotations

from kernelbox.core.manager import KernelManagerService
from kernelbox.core.types import KernelRecord
from kernelbox.store.registry import Registry


class SessionManager:
    def __init__(self, *, manager: KernelManagerService, registry: Registry) -> None:
        self.manager = manager
        self.registry = registry

    def get_or_create(
        self,
        name: str,
        *,
        tags: dict[str, str] | None = None,
    ) -> KernelRecord:
        record = self.registry.get_by_name(name)
        if record is not None and self.manager.ping(record):
            return self.registry.get(record.kernel_id) or record
        if record is not None:
            self.registry.remove(record.kernel_id)
        return self.manager.create(name=name, session_name=name, tags=tags)

