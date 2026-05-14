# Development Guide

Welcome to the KernelBox development guide! This document outlines the local setup, project structure, and workflow for contributing to the codebase.

## Local Setup

### Prerequisites

- Python 3.10+
- `uv` (fast Python package installer and resolver)
- Git

### Installation

1. Clone the repository:

    ```bash
    git clone <your-repo-url>
    cd KernelBox
    ```

2. Sync dependencies using `uv`:

    ```bash
    uv sync --extra dev
    ```

    This will create a `.venv` directory and install all dependencies (including dev dependencies) listed in the `uv.lock` file.

3. Activate the virtual environment:

    - **Windows:** `.venv\Scripts\activate`
    - **Linux/macOS:** `source .venv/bin/activate`

## Project Architecture

KernelBox is divided into several key components located in `src/kernelbox/`:

| Module | Purpose |
| --- | --- |
| `api.py` | Public programmatic Python API |
| `cli/` | Command-line interface using `argparse` |
| `config/` | Configuration loading and defaults |
| `core/manager.py` | Kernel lifecycle — create, list, ping, restart, destroy |
| `core/executor.py` | Code execution and output capture |
| `core/retry.py` | Retry controller (`execute_with_retry`) |
| `server/app.py` | FastAPI route handlers |
| `server/models.py` | Request / response schemas |
| `store/registry.py` | Kernel registry (file or memory backend) |

## Development Workflow

### Running the API Server Locally

Use the official FastAPI CLI. Run on port `8080` to avoid conflicts with the Zensical docs server (port `8000`):

```powershell
uv run fastapi dev --port 8080
```

The server will be available at `http://127.0.0.1:8080`. Access Swagger UI at `http://127.0.0.1:8080/docs`.

### Running the CLI

```powershell
uv run kernelbox --help
```

### Running Tests

We use `pytest` for testing. To run the test suite:

```powershell
uv run pytest
```

Ensure all tests pass before submitting a pull request.

### Running with Docker

To test KernelBox in its isolated, production-ready Docker environment:

```powershell
# Build the image and run it in the background
docker-compose up --build -d

# Check the health of the running container
curl http://localhost:8080/health

# Stop and remove the container
docker-compose down
```

Docker is the recommended way to securely execute code, as it drops Linux capabilities and runs as a restricted `sandbox_user`.

### Building Documentation

The documentation is built using **Zensical** with the Material theme.

Serve the docs locally:

```powershell
uv run zensical serve
```

Then open `http://127.0.0.1:8000` in your browser.

!!! note "Port separation"

    The docs server runs on port `8000` and the FastAPI server on port `8080` to avoid conflicts.

Build the static HTML:

```powershell
uv run zensical build
```

### Code Quality and Linting

Please ensure your code follows the project's styling guidelines. We recommend using `ruff` for formatting and linting:

```powershell
uv run ruff check .
uv run ruff format .
```

## Contributing

1. Fork the repository and create a new branch for your feature or bug fix.

2. Write clear, concise commit messages.

3. Include tests for any new features or critical bug fixes.

4. Update the documentation if your changes affect the user-facing API or CLI.

5. Open a Pull Request!
