<p align="center">
  <img src="logo/logo.svg" alt="KernelBox logo" width="360" />
</p>


<p align="center">
  <em>Persistent IPython kernels for agents, scripts, and tools — no notebook server required.</em>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+" /></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT" />
  <img src="https://img.shields.io/badge/version-0.1.0-orange" alt="0.1.0" />
</p>

---

**KernelBox** is a lightweight Python library for managing long-lived IPython kernels. It communicates directly with kernels over ZeroMQ through `jupyter_client` — no notebook server, no browser, no daemon process.

Built for **AI agents**, **automation scripts**, and **tools** that need to run Python code in a stateful, persistent session.

> [!WARNING]
> KernelBox runs code with the same OS privileges as the user who started it. Read the [Security Overview](docs/security.md) before using in production or exposing the HTTP API.

---

## Why KernelBox?

Autonomous agents often need to execute Python code across multiple steps. The common alternatives each have a painful trade-off:

| Approach | Problem |
| --- | --- |
| Subprocess per call | State lost instantly between calls |
| Feed state back into LLM prompt | Token usage explodes, context window fills up |
| Full Jupyter server | Heavy, requires REST API + WebSocket management |
| **KernelBox** | ✅ Persistent kernel, zero server overhead, structured output |

KernelBox holds the kernel session and variables **natively in memory**. Your agent runs code block A, and the kernel still remembers the data frame when it runs block B. No re-running, no re-serialising.

---

## Features

- **Persistent stateful sessions** — variables, imports, and state survive between calls
- **ZeroMQ direct communication** — no HTTP overhead, kernel-fast execution
- **Built-in Retry API** — caller-owned repair callbacks for self-correcting agents
- **Bash execution** — run shell commands inside the same session via `--bash`
- **FastAPI REST service** — full HTTP API with Swagger UI and OpenAPI schema
- **CLI** — manage kernels from the terminal with JSON output
- **Docker support** — hardened non-root container for production isolation
- **Fully configurable** — all settings overridable with environment variables
- **Two registry backends** — `file` (persists across restarts) or `memory` (in-process)
- **Named sessions** — create, reuse, restart, and destroy kernels by name
- **Rich structured output** — `status`, `output`, `stderr`, `return_value`, `duration_ms`, `truncated`, per-attempt history

---

## Quick Start

```bash
python scripts/bootstrap.py   # installs uv, creates .venv, syncs deps
```

```python
from kernelbox import get_or_create, execute, destroy

kernel = get_or_create("demo")

result = execute(kernel, "x = [1, 2, 3]\nsum(x)")
print(result.status)        # success
print(result.return_value)  # 6

# State persists — x is still in memory
result = execute(kernel, "x.append(4)\nsum(x)")
print(result.return_value)  # 10

destroy("demo")
```

---

## Installation

KernelBox uses [`uv`](https://github.com/astral-sh/uv) for dependency management.

**Recommended — bootstrap script (handles `uv` install automatically):**

```bash
python scripts/bootstrap.py
```

The script detects Windows, macOS, or Linux, installs `uv` if missing, creates `.venv`, and runs `uv sync --extra dev`.

**Manual (if `uv` is already installed):**

```bash
uv venv
uv sync --extra dev
```

---

## Running with Docker *(Recommended for isolation)*

The safest way to use KernelBox in production. The included `docker-compose.yml` runs the API as a non-root user with dropped capabilities and a read-only filesystem.

```bash
docker-compose up --build -d
# API available at http://localhost:8080
```

```bash
docker-compose down
```

---

## Python API

Four functions cover the full lifecycle:

```python
from kernelbox import get_or_create, execute, execute_with_retry, destroy
```

### `get_or_create(name)`

Returns a live named kernel, creating it if it doesn't exist yet.

```python
kernel = get_or_create("data-pipeline")
```

### `execute(kernel, code, *, language, timeout)`

Runs code and returns an `ExecutionResult`.

```python
result = execute(kernel, "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})")
print(result.status)         # "success" | "error" | "timeout"
print(result.output)         # stdout
print(result.stderr)         # stderr
print(result.return_value)   # last expression value as string
print(result.duration_ms)    # wall time
print(result.truncated)      # True if output was cut at KERNELBOX_OUTPUT_CHAR_LIMIT
```

Run a bash command in the same session:

```python
result = execute(kernel, "echo $HOME", language="bash")
```

### `execute_with_retry(kernel, code, on_error_fn, *, max_attempts, language, timeout)`

Runs code and calls your `on_error_fn` whenever execution fails, letting your agent self-correct.

```python
from kernelbox import execute_with_retry, get_or_create

kernel = get_or_create("agent")

def fix_code(result, attempt):
    # result.error has .ename, .evalue, .traceback
    # return new code to try, or None to retry the same code
    return f"# attempt {attempt}\nx = 41\nx + 1"

result = execute_with_retry(kernel, "x + 1", on_error_fn=fix_code)
print(result.status)           # success
print(result.return_value)     # 42
print(len(result.attempts))    # number of attempts made
```

### `destroy(name)`

Shuts down the kernel process and removes it from the registry.

```python
destroy("data-pipeline")
```

---

## CLI

### Kernel management

```bash
uv run kernelbox create --name my-kernel
uv run kernelbox list
uv run kernelbox list --refresh          # re-ping each kernel for live status
uv run kernelbox status --name my-kernel
uv run kernelbox exec --name my-kernel "print(1 + 1)"
uv run kernelbox exec --name my-kernel --bash "echo hello"
uv run kernelbox exec --name my-kernel --timeout 30 "some_long_call()"
uv run kernelbox restart --name my-kernel
uv run kernelbox destroy --name my-kernel
uv run kernelbox wipe                    # destroy all registered kernels
```

All CLI commands output **JSON** — easy to pipe into `jq` or parse in scripts.

```bash
uv run kernelbox exec --name demo "2 ** 10" | jq .return_value
# "1024"
```

### HTTP service (FastAPI)

```bash
uv run fastapi dev --port 8080    # development mode with hot-reload
uv run fastapi run --port 8080    # production mode
```

| Endpoint | Description |
| --- | --- |
| `http://127.0.0.1:8080/docs` | Swagger UI |
| `http://127.0.0.1:8080/redoc` | ReDoc |
| `http://127.0.0.1:8080/openapi.json` | OpenAPI schema |

---

## Configuration

All settings are read from environment variables at startup. No config file needed.

| Variable | Default | Description |
| --- | --- | --- |
| `KERNELBOX_MAX_RETRIES` | `5` | Max attempts in `execute_with_retry` |
| `KERNELBOX_EXECUTION_TIMEOUT` | `60` | Seconds before a single execution times out |
| `KERNELBOX_KERNEL_IDLE_TIMEOUT` | `1800` | Seconds before an idle kernel is considered stale |
| `KERNELBOX_OUTPUT_CHAR_LIMIT` | `10000` | Max characters of stdout/stderr captured |
| `KERNELBOX_STORE_BACKEND` | `file` | `file` (survives restarts) or `memory` (in-process only) |
| `KERNELBOX_REGISTRY_PATH` | `.kernelbox/registry.json` (Windows) / tmp | Where the file registry is stored |
| `KERNELBOX_RUNTIME_DIR` | `.kernelbox/runtime` (Windows) / tmp | Where kernel connection files live |
| `KERNELBOX_STARTUP_CODE` | *(unset)* | Python code executed automatically after every new kernel starts |
| `KERNELBOX_KERNEL_TYPE` | `python3` | Jupyter kernelspec name |
| `KERNELBOX_HOME` | *(unset)* | Override base directory for registry and runtime paths |

**PowerShell:**
```powershell
$env:KERNELBOX_EXECUTION_TIMEOUT = "120"
uv run fastapi dev --port 8080
```

**Bash/zsh:**
```bash
export KERNELBOX_EXECUTION_TIMEOUT=120
uv run fastapi dev --port 8080
```


---

## Assumptions & Limitations

| Area | Current behaviour |
| --- | --- |
| **Sandboxing** | Kernels run with the same OS privileges as the calling process. Use Docker for isolation. |
| **Authentication** | The FastAPI server has **no authentication**. Bind to `127.0.0.1` or put it behind a reverse proxy. |
| **Kernel type** | Only `python3` kernelspec is tested. Other kernels may work but are unsupported. |
| **Concurrency** | The file registry is not designed for heavy concurrent writes from multiple processes. |
| **Windows ACL** | KernelBox patches Jupyter's ACL restriction on Windows to avoid `PermissionError`. Connection files may have broader read permissions. |
| **Idle detection** | `KERNELBOX_KERNEL_IDLE_TIMEOUT` is tracked in metadata only — KernelBox does not automatically kill idle kernels. |
| **Output size** | stdout/stderr is truncated at `KERNELBOX_OUTPUT_CHAR_LIMIT` characters. `result.truncated` will be `True`. |
| **Bash execution** | Bash runs through IPython's `%%bash` cell magic, not a real shell. Environment variables and working directory may differ. |

---

## Development

```bash
uv run pytest          # run the test suite
uv run ruff check .    # lint
uv run ruff format .   # format
uv run zensical serve  # docs at http://127.0.0.1:8000
uv run fastapi dev --port 8080  # API at http://127.0.0.1:8080
```

> See the [Development Guide](docs/dev_guide.md) for architecture details and contribution workflow.
