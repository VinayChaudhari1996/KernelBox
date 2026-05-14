# Python API

The Python API is the fastest way to use KernelBox. Import four functions and you have everything you need.

```python
from kernelbox import get_or_create, execute, execute_with_retry, destroy
```

---

## `get_or_create(name)` — start or reuse a session

Returns a live `KernelRecord`. If a kernel with this name is already registered and running, you get it back. If not, a new kernel process is started.

```python
kernel = get_or_create("my-session")
```

You can also pass a kernel ID string directly to `execute()` — KernelBox will look it up for you.

---

## `execute(kernel, code)` — run code, get a result

```python
result = execute(kernel, "x = 10\nx * 2")
```

`execute` accepts optional keyword arguments:

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `language` | `str` | `"python"` | `"python"` or `"bash"` |
| `timeout` | `float \| None` | config value | Override the default execution timeout in seconds |

### The `ExecutionResult` object

Every call to `execute` returns an `ExecutionResult` dataclass:

| Field | Type | Description |
| --- | --- | --- |
| `status` | `str` | `"success"` · `"error"` · `"timeout"` · `"max_attempts_exceeded"` |
| `ok` | `bool` | `True` when `status == "success"` — convenient shortcut |
| `output` | `str` | Captured stdout |
| `stderr` | `str` | Captured stderr |
| `return_value` | `str \| None` | String representation of the last expression's value |
| `error` | `ErrorInfo \| None` | Structured error with `.ename`, `.evalue`, `.traceback` |
| `execution_count` | `int \| None` | IPython execution counter |
| `duration_ms` | `int` | Wall-clock execution time in milliseconds |
| `outputs` | `list[OutputItem]` | All raw kernel output items (stream, display_data, etc.) |
| `truncated` | `bool` | `True` if output was cut at `KERNELBOX_OUTPUT_CHAR_LIMIT` |
| `attempts` | `list[AttemptSnapshot]` | Per-attempt history (populated by `execute_with_retry`) |

### Example — reading all fields

```python
result = execute(kernel, "print('hello')\n2 + 2")

print(result.status)          # success
print(result.ok)              # True
print(result.output)          # hello
print(result.return_value)    # 4
print(result.duration_ms)     # e.g. 12
print(result.truncated)       # False
```

### Example — handling an error

```python
result = execute(kernel, "1 / 0")

if not result.ok:
    print(result.error.ename)   # ZeroDivisionError
    print(result.error.evalue)  # division by zero
```

### Example — bash execution

```python
result = execute(kernel, "echo $PWD && ls", language="bash")
print(result.output)
```

!!! note "Bash execution note"

    Bash runs through IPython's `%%bash` cell magic, not a real shell subprocess. Environment variables and the working directory may differ from your terminal session.

---

## `execute_with_retry` — self-correcting execution

Designed for AI agents that can generate a fix when code fails.

```python
result = execute_with_retry(
    kernel,
    code,
    on_error_fn,
    *,
    max_attempts=None,   # defaults to KERNELBOX_MAX_RETRIES (5)
    language="python",
    timeout=None,
)
```

### How it works

1. KernelBox executes `code`.
2. If it succeeds → return `ExecutionResult` immediately.
3. If it fails → call `on_error_fn(result, attempt)`.
   - Return a **new code string** → use that on the next attempt.
   - Return `None` → retry the same code.
4. After `max_attempts` failures → return with `status="max_attempts_exceeded"`.

```python
from kernelbox import execute_with_retry, get_or_create

kernel = get_or_create("agent")

def fix(result, attempt):
    print(f"Attempt {attempt} failed: {result.error.evalue}")
    # Ask your LLM for a fix, or hardcode one:
    return "x = 41\nx + 1"

result = execute_with_retry(kernel, "x + 1", on_error_fn=fix)

print(result.status)        # success
print(result.return_value)  # 42
print(len(result.attempts)) # 2 — the failed attempt and the fixed one
```

Each entry in `result.attempts` is an `AttemptSnapshot` with `attempt`, `code`, `status`, `output`, `stderr`, and `error`.

---

## `destroy(name)` — clean up

Shuts down the kernel subprocess and removes it from the registry. Returns `True` if a kernel was found and destroyed.

```python
destroy("my-session")
```

---

## Stateful sessions in practice

Because state persists, you can build up complex data pipelines step by step:

```python
kernel = get_or_create("pipeline")

execute(kernel, "import pandas as pd")
execute(kernel, "df = pd.read_csv('data.csv')")
execute(kernel, "df = df.dropna()")

result = execute(kernel, "df.shape")
print(result.return_value)  # (1823, 12)

execute(kernel, "df.to_parquet('clean.parquet')")
destroy("pipeline")
```
