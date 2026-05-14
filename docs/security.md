# Security Overview

Before deploying KernelBox in a production or public-facing environment, it is crucial to understand its security model and current limitations. KernelBox is designed as a lightweight, developer-focused tool, and by default, it does **not** include robust security features for untrusted environments.

!!! danger "Read this before production"

    KernelBox runs code with the same OS privileges as the user who started the server.
    The FastAPI server has **no authentication** by default.
    Always read this page and apply the mitigations before exposing the service to any network.

---

## Mitigating the risks with Docker

KernelBox ships with a production-ready `Dockerfile` and `docker-compose.yml` that address the most critical risks out of the box.

**What the included Docker setup does:**

- Runs the service as a **non-root user** (`sandbox_user`) — executed code cannot modify system files.
- Mounts the filesystem as **read-only** — the container cannot write to the host.
- Uses **tmpfs** for the `/tmp` scratch space — writes are in-memory only and discarded on container stop.
- **Drops all Linux capabilities** — the process cannot acquire elevated privileges even if exploited.

**Start the hardened container:**

```bash
docker-compose up --build -d

# Verify it is running
curl http://localhost:8080/health

# Stop
docker-compose down
```

!!! tip "Recommended for production"

    Running KernelBox inside Docker is the single most effective way to contain the RCE risk.
    If you cannot use Docker, bind the API to `127.0.0.1` and restrict access at the network level.

---

## Known Security Flaws & Considerations

### 1. Unauthenticated API Endpoints

**Flaw:** The FastAPI server exposes endpoints (e.g., `/sessions/{name}/execute`) without any authentication — no API keys, OAuth, or JWTs.

**Risk:** Anyone who can reach the API port can execute arbitrary Python or Bash code on the server.

**Mitigation:** Do not expose the KernelBox API directly to the public internet. Run it inside Docker, or put it behind a reverse proxy (Nginx, Caddy, Traefik) that enforces authentication. In development, bind only to `localhost` (`127.0.0.1`).

---

### 2. Arbitrary Code Execution (No Sandboxing)

**Flaw:** KernelBox uses `jupyter_client` to spawn IPython kernels as child processes. These kernels inherit the full OS user context — filesystem access, environment variables, and network access of the parent process.

**Risk:** Code executed via KernelBox has direct Remote Code Execution (RCE) capabilities. Without containerisation, there is nothing preventing executed code from reading secrets, modifying files, or making network calls.

**Mitigation:** Use the included Docker setup (see above). If running natively, only execute trusted code. For untrusted agent-generated code, always run inside the Docker container.

---

### 3. Windows ACL Workaround

**Flaw:** To avoid `PermissionError` on Windows, KernelBox patches Jupyter's `win32_restrict_file_to_user` ACL restriction when writing kernel connection files.

**Risk:** Kernel connection files contain the HMAC keys used by the Jupyter wire protocol. If created with overly permissive ACLs, other users on the same Windows machine may be able to read them and connect to the kernel directly.

**Mitigation:** Use KernelBox on a single-user Windows machine, or prefer a Linux/Docker environment where standard Unix file permissions apply correctly.

---

### 4. Missing CORS Configuration

**Flaw:** The FastAPI application does not configure Cross-Origin Resource Sharing (CORS).

**Risk:** If you build a browser-based frontend for KernelBox, all requests will be blocked by the browser's CORS policy. If CORS is added permissively in the future, it could allow unauthorised web origins to call the API.

**Mitigation:** Add `CORSMiddleware` in `src/kernelbox/server/app.py` with a strict `allow_origins` list before enabling any browser access.

---

### 5. Kernel Connection File Leftovers

**Flaw:** If the KernelBox service crashes unexpectedly, Jupyter kernel connection files (containing HMAC keys) may be left behind in `KERNELBOX_RUNTIME_DIR`.

**Risk:** Orphaned connection files expose kernel credentials and accumulate on disk indefinitely.

**Mitigation:** Periodically clean up `KERNELBOX_RUNTIME_DIR`. When using Docker, tmpfs handles this automatically — files are wiped when the container stops.

---

## Best Practices Checklist

!!! note "Before pushing to a repository or deploying"

    - **Do not commit secrets** — add `.env` files, connection files, and any credential files to `.gitignore`.
    - **Document the risks** — make sure everyone using the deployment knows about RCE and the lack of authentication.
    - **Run a security linter** — use `bandit` or `safety` in CI to catch newly introduced Python vulnerabilities.
    - **Use Docker in production** — the included setup is the recommended baseline for any non-local deployment.
    - **Bind to localhost in development** — `uv run fastapi dev --port 8080` binds to `127.0.0.1` by default; do not change this without a reverse proxy in front.
