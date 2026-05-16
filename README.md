<p align="center">
  <img src="logo/logo.svg" alt="KernelBox logo" width="320" />
</p>

<h3 align="center">The lightweight GenAI kernels for agentic Python — persistent kernels, zero token waste, self-healing execution.</h3>

<p align="center">
  <a href="https://pypi.org/project/kernelbox/"><img src="https://img.shields.io/pypi/v/kernelbox?color=orange&label=pypi" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/kernelbox/"><img src="https://img.shields.io/pypi/pyversions/kernelbox" alt="Python 3.10+" /></a>
  <a href="https://vinaychaudhari1996.github.io/KernelBox/"><img src="https://img.shields.io/badge/docs-latest-brightgreen" alt="Documentation" /></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
</p>

---

## Install

```bash
pip install kernelbox
```

> **Using `uv`?** &nbsp;`uv add kernelbox`

---

## 30-second demo

Spin up a **persistent Python kernel**, run stateful agentic code — no notebook server, no setup overhead:

```python
from kernelbox import get_or_create, execute, destroy

# Agentic AI: give your agent a named, persistent execution kernel
kernel = get_or_create("agent-sandbox")

# Step 1 — agent sends first code block
result = execute(kernel, "x = [1, 2, 3]\nsum(x)")
print(result.status)        # success
print(result.return_value)  # 6

# Step 2 — kernel remembers x. No context re-serialisation needed.
result = execute(kernel, "x.append(4)\nsum(x)")
print(result.return_value)  # 10

destroy("agent-sandbox")
```

That's it. One import. No server to start, no notebook to open, no context window wasted on state.

---

## The context engineering problem

In 2026, **agentic AI** systems don't just call an LLM once — they run Python code across dozens of steps, loop, retry, and self-correct. That creates a brutal bottleneck: **state management**.

Every time an agent moves to the next step, it faces a choice: carry the full execution state forward in the prompt (burning tokens on dataframes, variables, and imports), or lose it entirely and re-run from scratch.

**KernelBox solves this at the kernel level.** State lives natively inside a persistent Python kernel — not in the context window. The agent just sends the *next line of code*. The kernel remembers everything else.

> 💡 **In practice:** a multi-step GenAI data pipeline that re-serialises state into the prompt can burn **5–20× more tokens per run** than one backed by a persistent kernel. With KernelBox, context engineering becomes trivial — your agent's context window stays clean.

## Why KernelBox?

| Approach | The real cost |
|---|---|
| Subprocess per call | State lost — agent re-runs or re-serialises from scratch every step |
| Feed state into LLM prompt | 💸 **Token burn explodes** — each step re-sends the full execution context |
| Full Jupyter server | Heavy, slow — REST + WebSocket overhead, not built for agentic workflows |
| **KernelBox** | ✅ **Lightweight GenAI sandbox. Persistent kernel. Zero token waste. Self-healing.** |

KernelBox gives every agentic AI workflow a **dedicated, lightweight Python kernel** — stateful, fast, and isolated. No re-running. No re-serialising. No context window pollution.

---

## Features

- 🪙 **Drastic token savings** — state lives in the Python kernel, not the prompt; perfect for context engineering in agentic AI
- 🧠 **Agentic AI ready** — named, persistent kernels designed for multi-step LLM-driven workflows
- 🔁 **Stateful execution** — variables, imports, and objects survive between agent calls automatically
- 🩹 **Self-healing execution** — built-in retry API with caller-owned repair callbacks; agents auto-correct on failure
- 🏖️ **Lightweight GenAI sandbox** — isolated Python kernel per agent session, no notebook server, minimal footprint
- ⚡ **ZeroMQ direct communication** — no HTTP round-trip, no serialisation overhead, kernel-speed execution
- 🐚 **Bash execution** — run shell commands inside the same persistent kernel session
- 🌐 **FastAPI REST service** — expose kernels over HTTP with Swagger UI and OpenAPI schema
- 🖥️ **CLI** — manage kernels from the terminal with structured JSON output
- 🐳 **Docker support** — hardened non-root GenAI sandbox container for production isolation
- 🔧 **Fully configurable** — all settings overridable with environment variables

---

## Quick CLI test

After install, verify everything works in one line:

```bash
kernelbox exec --name test "print('KernelBox is working!')"
```

```json
{"status": "success", "output": "KernelBox is working!\n", "return_value": null}
```

---

> [!WARNING]
> KernelBox runs code with the **same OS privileges** as the user who started it. Use Docker for production or untrusted code. See [Security Overview](docs/security.md).

---

## 📚 Full Documentation

**→ [vinaychaudhari1996.github.io/KernelBox](https://vinaychaudhari1996.github.io/KernelBox/)**

Includes guides for Docker deployment, the FastAPI server, CLI reference, agentic AI patterns, and context engineering best practices.

---

---

<details>
<summary><strong>🤓 For Nerds — Full API, CLI & Config Reference</strong></summary>

## Python API reference

KernelBox exposes four lightweight functions that cover the full agentic kernel lifecycle:

```python
from kernelbox import get_or_create, execute, execute_with_retry, destroy
```

### `get_or_create(name)`

Returns a live named kernel, creating it if it doesn't exist yet.

```python
kernel = get_or_create("data-pipeline")
```

---

### `execute(kernel, code, *, language, timeout)`

Runs code and returns an `ExecutionResult`.

```python
result = execute(kernel, "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})")

result.status        # "success" | "error" | "timeout"
result.output        # stdout as string
result.stderr        # stderr as string
result.return_value  # last expression value as string
result.duration_ms   # wall-clock time in milliseconds
result.truncated     # True if output was cut at KERNELBOX_OUTPUT_CHAR_LIMIT
```

Run a bash command in the same session:

```python
result = execute(kernel, "echo $HOME", language="bash")
```

---

### `execute_with_retry(kernel, code, on_error_fn, *, max_attempts, language, timeout)`

**Self-healing execution** — runs code and calls your `on_error_fn` on failure, letting the agentic AI loop self-correct before giving up.

```python
from kernelbox import execute_with_retry, get_or_create

kernel = get_or_create("agent")

def fix_code(result, attempt):
    # result.error has: .ename, .evalue, .traceback
    # Return new code to retry, or None to retry the same code
    return f"# attempt {attempt}\nx = 41\nx + 1"

result = execute_with_retry(kernel, "x + 1", on_error_fn=fix_code)
result.status        # "success"
result.return_value  # "42"
len(result.attempts) # number of attempts made
```

---

### `destroy(name)`

Shuts down the kernel process and removes it from the registry.

```python
destroy("data-pipeline")
```

---

## CLI reference

```bash
kernelbox create --name my-kernel
kernelbox list
kernelbox list --refresh          # re-ping each kernel for live status
kernelbox status --name my-kernel
kernelbox exec --name my-kernel "print(1 + 1)"
kernelbox exec --name my-kernel --bash "echo hello"
kernelbox exec --name my-kernel --timeout 30 "some_long_call()"
kernelbox restart --name my-kernel
kernelbox destroy --name my-kernel
kernelbox wipe                    # destroy ALL registered kernels
```

All commands output **JSON** — easy to pipe into `jq`:

```bash
kernelbox exec --name demo "2 ** 10" | jq .return_value
# "1024"
```

> If you installed KernelBox inside a `uv` project, prefix commands with `uv run kernelbox ...`

---

## FastAPI HTTP service

```bash
# Development mode (hot-reload)
uvicorn kernelbox.server.app:app --port 8080 --reload

# Or via uv
uv run fastapi dev --port 8080
```

| Endpoint | Description |
|---|---|
| `http://127.0.0.1:8080/docs` | Swagger UI |
| `http://127.0.0.1:8080/redoc` | ReDoc |
| `http://127.0.0.1:8080/openapi.json` | OpenAPI schema |

---

## Docker (recommended for production)

```bash
docker-compose up --build -d   # API at http://localhost:8080
docker-compose down
```

Runs as a non-root user with dropped capabilities and a read-only filesystem.

---

## Configuration

All settings are read from environment variables — no config file needed.

| Variable | Default | Description |
|---|---|---|
| `KERNELBOX_MAX_RETRIES` | `5` | Max attempts in `execute_with_retry` |
| `KERNELBOX_EXECUTION_TIMEOUT` | `60` | Seconds before a single execution times out |
| `KERNELBOX_KERNEL_IDLE_TIMEOUT` | `1800` | Seconds before an idle kernel is considered stale |
| `KERNELBOX_OUTPUT_CHAR_LIMIT` | `10000` | Max characters of stdout/stderr captured |
| `KERNELBOX_STORE_BACKEND` | `file` | `file` (survives restarts) or `memory` (in-process only) |
| `KERNELBOX_REGISTRY_PATH` | `.kernelbox/registry.json` | Where the file registry is stored |
| `KERNELBOX_RUNTIME_DIR` | `.kernelbox/runtime` | Where kernel connection files live |
| `KERNELBOX_STARTUP_CODE` | *(unset)* | Python code executed after every new kernel starts |
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

| Area | Behaviour |
|---|---|
| **Sandboxing** | Kernels run with the same OS privileges as the calling process. Use Docker for isolation. |
| **Authentication** | The FastAPI server has **no authentication**. Bind to `127.0.0.1` or use a reverse proxy. |
| **Kernel type** | Only `python3` kernelspec is tested. Other kernels may work but are unsupported. |
| **Concurrency** | The file registry is not designed for heavy concurrent writes from multiple processes. |
| **Windows ACL** | KernelBox patches Jupyter's ACL restriction on Windows to avoid `PermissionError`. Connection files may have broader read permissions. |
| **Idle detection** | `KERNELBOX_KERNEL_IDLE_TIMEOUT` is tracked in metadata only — KernelBox does not automatically kill idle kernels. |
| **Output size** | stdout/stderr is truncated at `KERNELBOX_OUTPUT_CHAR_LIMIT`. `result.truncated` will be `True`. |
| **Bash execution** | Bash runs through IPython's `%%bash` cell magic, not a real shell. Environment variables and working directory may differ. |

---

## Development (from source)

```bash
git clone https://github.com/VinayChaudhari1996/KernelBox.git
cd KernelBox

# Bootstrap: installs uv, creates .venv, syncs dev deps
python scripts/bootstrap.py

# Or manually if uv is already installed
uv venv && uv sync --extra dev
```

```bash
uv run pytest              # test suite
uv run ruff check .        # lint
uv run ruff format .       # format
uv run zensical serve      # docs at http://127.0.0.1:8000
uv run fastapi dev --port 8080  # API at http://127.0.0.1:8080
```

> See the [Development Guide](docs/dev_guide.md) for architecture details and contribution workflow.

</details>

---

## License

MIT © [Vinay Chaudhari](https://www.vinaychaudhari.com)
