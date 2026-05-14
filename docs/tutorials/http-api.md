# HTTP API

KernelBox includes a FastAPI service that exposes the full kernel management API over HTTP. Use it when your agent or tool is not written in Python, or when you want to call KernelBox from a separate process.

---

## Start the server

```bash
uv run fastapi dev --port 8080    # development, hot-reload
uv run fastapi run --port 8080    # production
```

!!! tip "Port recommendation"

    Use port `8080` to avoid conflicts with the Zensical docs server which runs on port `8000`.

---

## Interactive docs

Once running, open:

- **Swagger UI** — `http://127.0.0.1:8080/docs` — try every endpoint in the browser
- **ReDoc** — `http://127.0.0.1:8080/redoc`
- **OpenAPI schema** — `http://127.0.0.1:8080/openapi.json`

---

## Endpoints

### Execute code in a named session

```
POST /sessions/{name}/execute
```

Creates the session if it doesn't exist, then runs the code. Sessions are persistent — state carries over between calls with the same `name`.

**Request:**

```json
{
  "code": "x = 42\nx * 2",
  "language": "python",
  "timeout": null
}
```

**Response:**

```json
{
  "status": "success",
  "output": "",
  "stderr": "",
  "return_value": "84",
  "execution_count": 1,
  "duration_ms": 11,
  "truncated": false,
  "error": null
}
```

**curl example:**

```bash
curl -X POST http://127.0.0.1:8080/sessions/demo/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "2 + 2"}'
```

**Python (`httpx`) example:**

```python
import httpx

response = httpx.post(
    "http://127.0.0.1:8080/sessions/demo/execute",
    json={"code": "sum([1, 2, 3, 4, 5])"},
)
result = response.json()
print(result["return_value"])  # 15
print(result["status"])        # success
```

---

### Execute with retry

```
POST /sessions/{name}/execute_with_retry
```

Runs code with automatic retries. Include `on_error_code` — the code to run after each failure.

**Request:**

```json
{
  "code": "x + 1",
  "on_error_code": "x = 41\nx + 1",
  "max_attempts": 3
}
```

---

### List all kernels

```
GET /kernels
```

Returns all registered kernels.

```bash
curl http://127.0.0.1:8080/kernels
```

---

### Get a single kernel

```
GET /kernels/{kernel_id}
```

---

### Create a kernel

```
POST /kernels
```

**Request:**

```json
{ "name": "my-kernel" }
```

---

### Restart a kernel

```
POST /kernels/{kernel_id}/restart
```

Clears all variables — equivalent to a fresh kernel.

---

### Destroy a kernel

```
DELETE /kernels/{kernel_id}
```

---

### Health check

```
GET /health
```

Returns `{ "status": "ok" }`. Useful for Docker health checks and load balancers.

---

## Running with Docker

The `docker-compose.yml` exposes port `8080` on your host:

```bash
docker-compose up --build -d
curl http://localhost:8080/health
```

!!! warning "No authentication"

    The HTTP API has **no authentication**. In production, always bind to `127.0.0.1` or place the server behind a reverse proxy (Nginx, Caddy) that enforces authentication.
