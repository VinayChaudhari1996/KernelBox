FROM python:3.12-slim

# Set environment variables to optimize Python and set up KernelBox paths
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KERNELBOX_RUNTIME_DIR=/tmp/runtime \
    KERNELBOX_REGISTRY_PATH=/tmp/registry.json

WORKDIR /app

# Install basic build tools and clear cache to keep the image lightweight
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from the official image for blazing fast installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy necessary project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package globally in the container, along with ipykernel to spawn python kernels
RUN uv pip install --system -e . ipykernel

# Create a non-root user for security (Sandboxing mitigation)
RUN useradd -m -s /bin/bash sandbox_user && \
    chown -R sandbox_user:sandbox_user /app

# Switch to the restricted user
USER sandbox_user

# Expose the API port
EXPOSE 8080

# Start the FastAPI server on 0.0.0.0 to allow external access within the Docker network
CMD ["uvicorn", "kernelbox.server.app:app", "--host", "0.0.0.0", "--port", "8080"]
