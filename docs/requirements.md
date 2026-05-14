# Prerequisites

You need these tools before setting up KernelBox.

## Required

| Tool | Why |
| --- | --- |
| Python 3.10 or newer | Runs KernelBox |
| `uv` | Creates the virtual environment and installs packages |
| `jupyter_client` | Talks to the IPython kernel |
| `ipykernel` | Starts Python kernels |

## For the HTTP API

| Tool | Why |
| --- | --- |
| FastAPI | Provides the REST API |
| `fastapi-cli` | Runs the server with `fastapi dev` and `fastapi run` |
| Uvicorn | Serves the ASGI app |

## For Docker (Recommended for Isolation)

| Tool | Why |
| --- | --- |
| Docker | Creates an isolated container |
| Docker Compose | Simplifies building and running the container |

## For Documentation

| Tool | Why |
| --- | --- |
| Zensical | Builds and serves the documentation site |
| mike | Publishes versioned docs to GitHub Pages |

## Supported Operating Systems

KernelBox works on:

- Windows
- macOS
- Linux

The bootstrap script detects the OS and chooses the right `uv` installer automatically.
