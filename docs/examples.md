# Examples

Real-world snippets showing KernelBox in action.

---

## Basic stateful session

```python
from kernelbox import get_or_create, execute, destroy

kernel = get_or_create("demo")

# Variables persist between calls
execute(kernel, "numbers = [1, 2, 3, 4, 5]")
result = execute(kernel, "sum(numbers)")

print(result.return_value)   # 15
print(result.status)         # success
print(result.duration_ms)    # e.g. 8

destroy("demo")
```

---

## Data science pipeline

```python
kernel = get_or_create("data-work")

execute(kernel, "import pandas as pd")
execute(kernel, "df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})")
execute(kernel, "df['c'] = df['a'] + df['b']")

result = execute(kernel, "df")
print(result.output)       # printed repr of the dataframe
print(result.return_value) # string repr of last expression

destroy("data-work")
```

---

## Capture printed output vs. return value

```python
# output captures print() calls
result = execute(kernel, "print('hello world')")
print(result.output)        # hello world\n
print(result.return_value)  # None

# return_value captures the last expression
result = execute(kernel, "2 ** 8")
print(result.output)        # (empty)
print(result.return_value)  # 256
```

---

## Handle errors gracefully

```python
result = execute(kernel, "1 / 0")

if not result.ok:
    print(result.status)           # error
    print(result.error.ename)      # ZeroDivisionError
    print(result.error.evalue)     # division by zero
    print(result.error.traceback)  # list of traceback lines
```

---

## Self-correcting agent with retry

```python
from kernelbox import execute_with_retry, get_or_create

kernel = get_or_create("agent")

def fix_code(result, attempt):
    """Called whenever execution fails. Return new code or None to retry the same."""
    print(f"Attempt {attempt} failed: {result.error.ename}: {result.error.evalue}")
    # In a real agent you'd ask the LLM to fix the code.
    # Here we hardcode the fix:
    return "x = 41\nx + 1"

result = execute_with_retry(kernel, "x + 1", on_error_fn=fix_code)

print(result.status)         # success
print(result.return_value)   # 42
print(len(result.attempts))  # 2
```

---

## Bash commands

```python
result = execute(kernel, "echo $HOME && ls -la", language="bash")
print(result.output)
```

!!! note "Bash execution note"

    Bash runs through IPython's `%%bash` magic. It is not a fully interactive shell — things like `cd` will not persist to subsequent calls.

---

## Check if output was truncated

```python
result = execute(kernel, "print('x' * 20000)")

if result.truncated:
    print("Output was cut — increase KERNELBOX_OUTPUT_CHAR_LIMIT to see all of it.")
```

---

## HTTP API from Python

```python
import httpx

# Start the server first: uv run fastapi dev --port 8080

response = httpx.post(
    "http://127.0.0.1:8080/sessions/demo/execute",
    json={"code": "21 * 2"},
)

result = response.json()
print(result["return_value"])  # 42
print(result["status"])        # success
```

---

## Pre-warm a kernel with startup code

Use `KERNELBOX_STARTUP_CODE` so every kernel starts with your imports ready:

```bash
export KERNELBOX_STARTUP_CODE="import numpy as np; import pandas as pd"
```

```python
kernel = get_or_create("warm")
result = execute(kernel, "np.array([1, 2, 3]).mean()")
print(result.return_value)  # 2.0  (numpy was already imported)
```
