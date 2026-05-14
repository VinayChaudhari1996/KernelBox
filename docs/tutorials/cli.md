# CLI

The `kernelbox` CLI manages kernels and executes code from the terminal. Every command outputs **JSON** — easy to pipe into `jq` or parse in scripts.

---

## Commands at a glance

| Command | What it does |
| --- | --- |
| `create --name <name>` | Start a new named kernel |
| `list` | List all registered kernels |
| `list --refresh` | List kernels and re-ping each for live status |
| `status --name <name>` | Check if a kernel is alive |
| `exec --name <name> <code>` | Run Python code |
| `exec --name <name> --bash <code>` | Run a bash command |
| `exec ... --timeout <secs>` | Override the execution timeout |
| `restart --name <name>` | Restart a kernel (clears all variables) |
| `destroy --name <name>` | Stop a kernel and remove it from the registry |
| `wipe` | Destroy **all** registered kernels |

You can use `--id <kernel-id>` instead of `--name` in any command that accepts an identifier.

---

## Walkthrough

### Create a kernel

```bash
uv run kernelbox create --name demo
```

```json
{
  "connection_file": ".kernelbox/runtime/kernel-abc123.json",
  "created_at": "2026-05-14T06:00:00+00:00",
  "kernel_id": "abc123",
  "name": "demo",
  "status": "running"
}
```

### Run Python code

```bash
uv run kernelbox exec --name demo "2 ** 10"
```

```json
{
  "duration_ms": 8,
  "output": "",
  "return_value": "1024",
  "status": "success"
}
```

### State persists between calls

```bash
uv run kernelbox exec --name demo "x = 42"
uv run kernelbox exec --name demo "x * 2"
# return_value: "84"
```

### Run a bash command

```bash
uv run kernelbox exec --name demo --bash "echo hello && pwd"
```

```json
{
  "output": "hello\n/your/working/dir\n",
  "status": "success"
}
```

### Set a custom timeout

```bash
uv run kernelbox exec --name demo --timeout 5 "import time; time.sleep(10)"
# status: "timeout"
```

### Check kernel health

```bash
uv run kernelbox status --name demo
```

```json
{
  "alive": true,
  "kernel": { "name": "demo", "status": "running", ... }
}
```

### List all kernels

```bash
uv run kernelbox list
uv run kernelbox list --refresh   # re-pings each kernel for a live status check
```

### Restart a kernel

Clears all variables — equivalent to a fresh kernel.

```bash
uv run kernelbox restart --name demo
```

### Destroy a single kernel

```bash
uv run kernelbox destroy --name demo
# { "destroyed": true }
```

### Wipe everything

```bash
uv run kernelbox wipe
# { "destroyed": ["abc123", "def456"] }
```

---

## Tips for agentic workflows

The CLI is convenient for one-off commands. For agents that generate large, multi-line code blocks, prefer the **Python API** or **HTTP API** — passing multi-line code through shell arguments involves quoting and escaping that can silently corrupt the code before it even reaches the kernel.

```bash
# This is fragile for multi-line code:
uv run kernelbox exec --name demo "x = 1\ny = x + 1\nprint(y)"

# Better: use the Python API or HTTP endpoint for generated code
```

---

## FastAPI server CLI

To start the HTTP service:

```bash
uv run fastapi dev --port 8080    # development, hot-reload
uv run fastapi run --port 8080    # production
```

| URL | Description |
| --- | --- |
| `http://127.0.0.1:8080/docs` | Swagger UI |
| `http://127.0.0.1:8080/redoc` | ReDoc |
| `http://127.0.0.1:8080/openapi.json` | OpenAPI schema |
