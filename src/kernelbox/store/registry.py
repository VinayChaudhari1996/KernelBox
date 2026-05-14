"""Registry backends for kernel metadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
import json
from pathlib import Path
import threading

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.types import KernelRecord


class Registry(ABC):
    @abstractmethod
    def upsert(self, record: KernelRecord) -> KernelRecord:
        raise NotImplementedError

    @abstractmethod
    def get(self, identifier: str) -> KernelRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> KernelRecord | None:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> list[KernelRecord]:
        raise NotImplementedError

    @abstractmethod
    def remove(self, identifier: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

    def increment_attempt_count(self, identifier: str) -> KernelRecord | None:
        record = self.get(identifier)
        if record is None:
            return None
        record.attempt_count += 1
        record.touch()
        return self.upsert(record)


class MemoryRegistry(Registry):
    def __init__(self) -> None:
        self._records: dict[str, KernelRecord] = {}
        self._lock = threading.RLock()

    def upsert(self, record: KernelRecord) -> KernelRecord:
        with self._lock:
            self._records[record.kernel_id] = deepcopy(record)
            return deepcopy(record)

    def get(self, identifier: str) -> KernelRecord | None:
        with self._lock:
            record = self._records.get(identifier) or self._find_by_name(identifier)
            return deepcopy(record) if record else None

    def get_by_name(self, name: str) -> KernelRecord | None:
        with self._lock:
            record = self._find_by_name(name)
            return deepcopy(record) if record else None

    def all(self) -> list[KernelRecord]:
        with self._lock:
            return [deepcopy(record) for record in self._records.values()]

    def remove(self, identifier: str) -> bool:
        with self._lock:
            record = self._records.get(identifier) or self._find_by_name(identifier)
            if record is None:
                return False
            self._records.pop(record.kernel_id, None)
            return True

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def _find_by_name(self, name: str) -> KernelRecord | None:
        for record in self._records.values():
            if record.name == name or record.session_name == name:
                return record
        return None


class FileRegistry(MemoryRegistry):
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        super().__init__()
        self._records = self._load()

    def upsert(self, record: KernelRecord) -> KernelRecord:
        with self._lock:
            self._records[record.kernel_id] = deepcopy(record)
            self._write()
            return deepcopy(record)

    def remove(self, identifier: str) -> bool:
        with self._lock:
            record = self._records.get(identifier) or self._find_by_name(identifier)
            if record is None:
                return False
            self._records.pop(record.kernel_id, None)
            self._write()
            return True

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._write()

    def _load(self) -> dict[str, KernelRecord]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return {
            kernel_id: KernelRecord.from_dict(record)
            for kernel_id, record in raw.get("kernels", {}).items()
        }

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "kernels": {
                kernel_id: record.to_dict()
                for kernel_id, record in self._records.items()
            },
        }
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)


def create_registry(config: KernelBoxConfig) -> Registry:
    backend = config.store_backend.lower()
    if backend == "memory":
        return MemoryRegistry()
    if backend == "file":
        return FileRegistry(config.registry_path)
    if backend == "redis":
        raise NotImplementedError("Redis registry support is planned but not bundled.")
    raise ValueError(f"Unknown kernelbox registry backend: {config.store_backend}")
