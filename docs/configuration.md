# Configuration

KernelBox is configured entirely through environment variables. No config file is needed.

Variables are read once at import time. Restart the process after changing them.

---

## All variables

| Variable | Default | Description |
| --- | --- | --- |
| `KERNELBOX_MAX_RETRIES` | `5` | Maximum attempts in `execute_with_retry` before returning `status="max_attempts_exceeded"` |
| `KERNELBOX_EXECUTION_TIMEOUT` | `60` | Seconds before a single code execution is cancelled and returns `status="timeout"` |
| `KERNELBOX_KERNEL_IDLE_TIMEOUT` | `1800` | Seconds of inactivity before a kernel is considered stale (metadata only — kernels are not killed automatically) |
| `KERNELBOX_OUTPUT_CHAR_LIMIT` | `10000` | Maximum characters of stdout + stderr captured per execution. Output beyond this is dropped and `result.truncated` is set to `True` |
| `KERNELBOX_STORE_BACKEND` | `file` | `file` — persists registry to disk across restarts. `memory` — in-process only, lost when the process exits |
| `KERNELBOX_REGISTRY_PATH` | `.kernelbox/registry.json` (Windows) / `$TMPDIR/kernelbox/registry.json` | Path to the JSON file used by the file registry backend |
| `KERNELBOX_RUNTIME_DIR` | `.kernelbox/runtime` (Windows) / `$TMPDIR/kernelbox/runtime` | Directory where Jupyter kernel connection files are stored |
| `KERNELBOX_STARTUP_CODE` | *(unset)* | Python code executed automatically after **every** new kernel is created. Useful for pre-importing libraries or setting up the environment |
| `KERNELBOX_KERNEL_TYPE` | `python3` | The Jupyter kernelspec name to use when starting kernels. Run `jupyter kernelspec list` to see what's installed |
| `KERNELBOX_HOME` | *(unset)* | If set, overrides the base directory for both `KERNELBOX_REGISTRY_PATH` and `KERNELBOX_RUNTIME_DIR` |

---

## Setting variables

=== "PowerShell"

    ```powershell
    $env:KERNELBOX_EXECUTION_TIMEOUT = "120"
    $env:KERNELBOX_STARTUP_CODE = "import numpy as np; import pandas as pd"
    uv run fastapi dev --port 8080
    ```

=== "Bash / zsh"

    ```bash
    export KERNELBOX_EXECUTION_TIMEOUT=120
    export KERNELBOX_STARTUP_CODE="import numpy as np; import pandas as pd"
    uv run fastapi dev --port 8080
    ```

=== ".env file (manual)"

    KernelBox does not load `.env` files automatically. You can source one manually:

    ```bash
    # .env
    KERNELBOX_EXECUTION_TIMEOUT=120
    KERNELBOX_STORE_BACKEND=memory
    ```

    ```bash
    set -a && source .env && set +a
    uv run fastapi dev --port 8080
    ```

---

## Common recipes

### Pre-import libraries on every kernel start

```bash
export KERNELBOX_STARTUP_CODE="import numpy as np; import pandas as pd; import matplotlib.pyplot as plt"
```

Every new kernel will have `np`, `pd`, and `plt` ready to use without an explicit import step.

### Use a faster in-memory store (ephemeral use)

```bash
export KERNELBOX_STORE_BACKEND=memory
```

The kernel registry lives only in the current process. Great for short-lived scripts or tests.

### Move data files to a custom location

```bash
export KERNELBOX_HOME=/var/kernelbox
# Registry → /var/kernelbox/registry.json
# Runtime  → /var/kernelbox/runtime/
```

### Increase timeout for heavy computations

```bash
export KERNELBOX_EXECUTION_TIMEOUT=600   # 10 minutes
```

### Increase output capture limit

```bash
export KERNELBOX_OUTPUT_CHAR_LIMIT=50000
```

---

## Reading config in Python

```python
from kernelbox import KernelBoxConfig

config = KernelBoxConfig.from_env()
print(config.execution_timeout)   # 60.0
print(config.store_backend)       # "file"
print(config.runtime_dir)         # PosixPath('/tmp/kernelbox/runtime')
```
