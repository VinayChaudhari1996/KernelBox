# 🛠️ Setup & Installation

Ready to give your agents a brain that remembers? Let's get KernelBox installed.

---

## 🔌 For Users (Library)

If you just want to use KernelBox in your project, choose your favorite package manager.

### Using pip
```bash
pip install kernelbox
```

### Using uv (Fastest)
```bash
uv add kernelbox
```

---

## 🏗️ For Contributors (Development)

If you want to modify KernelBox or run the FastAPI server from source, follow these steps.

### 1. Clone the repository
```bash
git clone https://github.com/VinayChaudhari1996/KernelBox.git
cd KernelBox
```

### 2. Bootstrap the project
We use `uv` for lightning-fast dependency management. If you don't have it, our bootstrap script will help.

```bash
python scripts/bootstrap.py
```

This script will:
- Detect your OS.
- Install `uv` if missing.
- Create a virtual environment (`.venv`).
- Install all dependencies (including dev tools).

### 3. Verify the installation
Run the tests to make sure everything is working perfectly:

```bash
uv run pytest
```

---

## 🐳 Docker Setup (Recommended for Production)

For maximum security and isolation, we recommend running KernelBox in Docker. This ensures that any code executed by your agent is sandboxed.

```bash
docker-compose build
docker-compose up -d
```

The API will be live at `http://localhost:8080`.

---

## 📖 Working with Docs

If you want to preview these docs locally while making changes:

### Build the docs
```bash
uv run zensical build
```

### Serve the docs
```bash
uv run zensical serve
```
Then visit `http://127.0.0.1:8000` in your browser.

