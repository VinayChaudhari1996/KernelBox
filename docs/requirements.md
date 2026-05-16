# 📋 What you'll need

Before we dive into the magic of stateful kernels, let's make sure your environment is ready.

---

## 🛠️ Core Essentials

These are required to run KernelBox natively.

| Tool | Purpose |
| :--- | :--- |
| **Python 3.10+** | The heart of the system. |
| **uv** | Our preferred (and lightning-fast) package manager. |
| **ipykernel** | What actually runs the code your agent writes. |

---

## 🌐 For the REST API

If you plan to use KernelBox over HTTP (e.g., via a FastAPI service):

| Tool | Purpose |
| :--- | :--- |
| **FastAPI** | Powers our high-performance REST endpoints. |
| **Uvicorn** | The engine that serves the API. |

---

## 🐳 For Maximum Security

Highly recommended if you're running untrusted agent code.

| Tool | Purpose |
| :--- | :--- |
| **Docker** | Keeps the agent code sandboxed and away from your host files. |
| **Docker Compose** | Orchestrates the service with a single command. |

---

## 💻 Supported Platforms

KernelBox is built to be cross-platform and has been tested on:

*   ✅ **Windows** (including specific fixes for Jupyter connection files)
*   ✅ **macOS**
*   ✅ **Linux**

---

!!! tip "Don't sweat the small stuff"
    If you're contributing to the project, our `scripts/bootstrap.py` will handle most of these for you!
