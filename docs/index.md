<p align="center">
  <img src="assets/logo.svg" alt="KernelBox logo" style="width: 250px; height: 250px; display: block; margin: 0 auto;" />
</p>

# KernelBox

**Persistent IPython kernels for your AI agents — without the Jupyter overhead.**

Ever wished your AI agent could "just remember" variables between code executions? Or run Bash commands in the same session? KernelBox makes it happen. No notebook server, no bloat. Just pure execution power.

---

## ⚡ Quick Start

Get up and running in seconds.

### Install via pip
```bash
pip install kernelbox
```

### Install via uv (Recommended)
```bash
uv add kernelbox
```

---

## 🤔 What is KernelBox?

KernelBox is a lightweight utility that talks directly to IPython kernels over ZeroMQ. It gives your agent a persistent Python session it can hold open, run code in, and read structured results from.

### Why do you need it?
- **State Persistence:** Variables, imports, and functions stay in memory between calls.
- **Agent-First:** Built specifically for LLM agents that need to execute code and see results.
- **Zero Overhead:** No need to spin up a full Jupyter/Notebook server.
- **Secure:** Designed to run in isolated Docker environments.

---

## 🚀 Quick Demo

See it in action:

```python
from kernelbox import get_or_create, execute, destroy

# Get a kernel named "my-agent"
kernel = get_or_create("my-agent")

# Step 1: Define something
execute(kernel, "data = {'name': 'KernelBox', 'status': 'awesome'}")

# Step 2: It's still there!
result = execute(kernel, "data['name']")
print(result.return_value)  # Output: KernelBox

# Clean up when done
destroy("my-agent")
```
```
'KernelBox'
True
```

---

## ✨ Features at a Glance

*   **Named Sessions:** Keep multiple agents isolated with unique session names.
*   **Rich Results:** Get `stdout`, `stderr`, and `return_value` in a clean, structured object.
*   **Self-Correction:** Use `execute_with_retry` to let your agent fix its own bugs.
*   **Universal Interface:** Use it via **Python API**, **REST API (FastAPI)**, or **CLI**.
*   **Docker Ready:** Pre-configured for secure, non-root execution.

---

## 🗺️ Where to go next?

*   🚀 [**Installation & Setup**](setup.md) — Dive deeper into the setup.
*   🐍 [**Python API Guide**](tutorials/python-api.md) — Master the library.
*   🌐 [**HTTP API Reference**](tutorials/http-api.md) — Connect via REST.
*   💻 [**CLI Reference**](tutorials/cli.md) — Use it from the terminal.
*   🛡️ [**Security First**](security.md) — Essential reading for production.

---

<p align="center">
  <i>Built with ❤️ for the agentic future.</i>
</p>
