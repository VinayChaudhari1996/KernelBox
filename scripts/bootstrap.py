"""Bootstrap KernelBox with uv.

This script intentionally avoids pip. It detects the host OS, installs uv when
missing through Astral's official installer, creates a local virtual environment,
and syncs project dependencies from pyproject.toml.
"""

from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
UV_CACHE_DIR = ROOT / ".uv-cache"


def main() -> int:
    os_name = platform.system().lower()
    print(f"Detected OS: {platform.system()} {platform.release()}")
    os.environ.setdefault("UV_CACHE_DIR", str(UV_CACHE_DIR))

    uv = find_uv()
    if uv is None:
        install_uv(os_name)
        uv = find_uv()

    if uv is None:
        raise SystemExit("uv was not found after installation. Restart your shell and rerun.")

    if not (ROOT / ".venv").exists():
        run([str(uv), "venv"])
    run([str(uv), "sync", "--extra", "dev"])
    print("KernelBox environment is ready.")
    return 0


def find_uv() -> Path | None:
    found = shutil.which("uv")
    if found:
        return Path(found)

    candidates = []
    if platform.system().lower() == "windows":
        candidates.extend(
            [
                Path.home() / ".local" / "bin" / "uv.exe",
                Path.home() / ".cargo" / "bin" / "uv.exe",
            ]
        )
    else:
        candidates.extend(
            [
                Path.home() / ".local" / "bin" / "uv",
                Path.home() / ".cargo" / "bin" / "uv",
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def install_uv(os_name: str) -> None:
    print("uv not found; installing uv...")
    if os_name == "windows":
        run(
            [
                "powershell",
                "-ExecutionPolicy",
                "ByPass",
                "-NoProfile",
                "-Command",
                "irm https://astral.sh/uv/install.ps1 | iex",
            ]
        )
        return

    if os_name in {"linux", "darwin"}:
        if shutil.which("curl"):
            run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
            return
        if shutil.which("wget"):
            run(["sh", "-c", "wget -qO- https://astral.sh/uv/install.sh | sh"])
            return
        raise SystemExit("curl or wget is required to install uv on this OS.")

    raise SystemExit(f"Unsupported OS for automatic uv install: {platform.system()}")


def run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
