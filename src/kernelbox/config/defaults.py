"""Default configuration and environment loading."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import tempfile


def default_registry_path() -> Path:
    home = os.getenv("KERNELBOX_HOME")
    if home:
        return Path(home) / "registry.json"
    if os.name == "nt":
        return Path.cwd() / ".kernelbox" / "registry.json"
    return Path(tempfile.gettempdir()) / "kernelbox" / "registry.json"


def default_runtime_dir() -> Path:
    home = os.getenv("KERNELBOX_HOME")
    if home:
        return Path(home) / "runtime"
    if os.name == "nt":
        return Path.cwd() / ".kernelbox" / "runtime"
    return Path(tempfile.gettempdir()) / "kernelbox" / "runtime"


DEFAULT_MAX_RETRIES = 5
DEFAULT_KERNEL_IDLE_TIMEOUT = 30 * 60
DEFAULT_EXECUTION_TIMEOUT = 60.0
DEFAULT_OUTPUT_CHAR_LIMIT = 10_000
DEFAULT_STORE_BACKEND = "file"
DEFAULT_KERNEL_TYPE = "python3"


@dataclass(frozen=True, slots=True)
class KernelBoxConfig:
    max_retries: int = DEFAULT_MAX_RETRIES
    kernel_idle_timeout: int = DEFAULT_KERNEL_IDLE_TIMEOUT
    execution_timeout: float = DEFAULT_EXECUTION_TIMEOUT
    output_char_limit: int = DEFAULT_OUTPUT_CHAR_LIMIT
    store_backend: str = DEFAULT_STORE_BACKEND
    registry_path: Path = field(default_factory=default_registry_path)
    runtime_dir: Path = field(default_factory=default_runtime_dir)
    startup_code: str | None = None
    kernel_type: str = DEFAULT_KERNEL_TYPE

    @classmethod
    def from_env(cls) -> "KernelBoxConfig":
        return cls(
            max_retries=_env_int("KERNELBOX_MAX_RETRIES", DEFAULT_MAX_RETRIES),
            kernel_idle_timeout=_env_int(
                "KERNELBOX_KERNEL_IDLE_TIMEOUT",
                DEFAULT_KERNEL_IDLE_TIMEOUT,
            ),
            execution_timeout=_env_float(
                "KERNELBOX_EXECUTION_TIMEOUT",
                DEFAULT_EXECUTION_TIMEOUT,
            ),
            output_char_limit=_env_int(
                "KERNELBOX_OUTPUT_CHAR_LIMIT",
                DEFAULT_OUTPUT_CHAR_LIMIT,
            ),
            store_backend=os.getenv("KERNELBOX_STORE_BACKEND", DEFAULT_STORE_BACKEND),
            registry_path=Path(
                os.getenv("KERNELBOX_REGISTRY_PATH", str(default_registry_path()))
            ),
            runtime_dir=Path(
                os.getenv("KERNELBOX_RUNTIME_DIR", str(default_runtime_dir()))
            ),
            startup_code=os.getenv("KERNELBOX_STARTUP_CODE") or None,
            kernel_type=os.getenv("KERNELBOX_KERNEL_TYPE", DEFAULT_KERNEL_TYPE),
        )


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a float") from exc
