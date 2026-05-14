# Run KernelBox

You can run KernelBox in three ways.

## Run via Docker (Recommended)

The most secure way to run the FastAPI service is via Docker. This drops all host privileges and prevents executed agent code from reading or destroying local files.

```powershell
# Start the container in the background
docker-compose up -d
```

The API will be available at `http://localhost:8080`.

To stop the service, run:
```powershell
docker-compose down
```

## Run the FastAPI service

Use the official FastAPI CLI. We use port `8080` to prevent conflicts with the Zensical docs server.

Development mode:

```powershell
uv run fastapi dev --port 8080
```

Production-style mode:

```powershell
uv run fastapi run --port 8080
```

Open the API docs:

```text
http://127.0.0.1:8080/docs
```

Other docs:

```text
http://127.0.0.1:8080/redoc
http://127.0.0.1:8080/openapi.json
```

## Run Python code

```python
from kernelbox import get_or_create, execute

kernel = get_or_create("demo")
result = execute(kernel, "1 + 1")

print(result.return_value)
```

## Run CLI commands

```powershell
uv run kernelbox create --name demo
uv run kernelbox exec --name demo "1 + 1"
uv run kernelbox destroy --name demo
```

## Stop everything

Destroy all registered kernels:

```powershell
uv run kernelbox wipe
```

