# 🚀 Let's Run It!

KernelBox is flexible. Whether you're building a Python agent, a web service, or just hacking in the terminal, we've got you covered.

---

## 🐍 1. Use it as a Python Library

The most direct way to give your agent a brain. 

```python
from kernelbox import get_or_create, execute

# This creates a kernel (or joins an existing one) named "my-agent"
kernel = get_or_create("my-agent")

# Run some code!
result = execute(kernel, "x = 10; x * 2")

print(f"Result: {result.return_value}")  # Result: 20
```

---

## 🌐 2. Use it as a REST API (FastAPI)

Perfect if your agents live in a different process or you want to use the Swagger UI.

### Start the server
```bash
# If you installed via pip/uv
kernelbox serve --port 8080

# Or run from source
uv run fastapi dev src/kernelbox/server/app.py --port 8080
```

### Hit the endpoint
```bash
curl -X POST "http://localhost:8080/sessions/demo/execute" \
     -H "Content-Type: application/json" \
     -d '{"code": "print(\"Hello from the API!\")"}'
```

---

## 💻 3. Use it via CLI

Great for shell scripts or quick debugging.

```bash
# Create a session
kernelbox create --name debug-session

# Execute code
kernelbox exec --name debug-session "import os; os.getcwd()"

# Wipe all sessions
kernelbox wipe
```

---

## 🐳 4. Run via Docker (Recommended)

Running in Docker is the gold standard for security. It prevents agent code from accidentally (or intentionally) touching your host machine.

```bash
docker-compose up -d
```
The API will be available at `http://localhost:8080`.

---

## 🧹 Cleaning Up

Done for the day? You can destroy specific kernels or wipe the whole registry.

```python
from kernelbox import destroy
destroy("my-agent")
```

Or via CLI:
```bash
kernelbox wipe
```
