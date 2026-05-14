# Setup

KernelBox uses `uv`.

Do not use `pip` for this project.

## 1. Clone or open the project

Open a terminal in the project folder.

```powershell
cd F:\Projects\KernelBox
```

## 2. Docker Setup (Recommended)

To run KernelBox securely inside an isolated container, bypassing the need for local Python or `uv` installation, make sure Docker is installed and running, then simply build the image:

```powershell
docker-compose build
```

## 3. Bootstrap the project

Run:

```powershell
python scripts/bootstrap.py
```

The script will:

- detect your operating system
- install `uv` if it is missing
- create `.venv`
- install project dependencies
- install development tools

## 4. Manual setup

If `uv` is already installed, you can run the commands yourself.

```powershell
uv venv
uv sync --extra dev
```

## 5. Check the install

Run the tests:

```powershell
uv run pytest
```

Expected result:

```text
6 passed
```

## 6. Build the docs

```powershell
uv run zensical build
```

## 7. Serve the docs locally

```powershell
uv run zensical serve
```

Open:

```text
http://127.0.0.1:8000
```

