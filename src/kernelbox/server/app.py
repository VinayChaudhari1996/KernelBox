"""FastAPI service exposing KernelBox kernel management."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, status

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.exceptions import KernelAlreadyExists
from kernelbox.core.executor import KernelExecutor
from kernelbox.core.manager import KernelManagerService
from kernelbox.core.retry import RetryController
from kernelbox.core.session import SessionManager
from kernelbox.core.types import ExecutionResult, KernelRecord
from kernelbox.server.models import (
    ApiLink,
    ExecuteRequest,
    ExecutionResultModel,
    HealthResponse,
    KernelCreateRequest,
    KernelDestroyedResponse,
    KernelListResponse,
    KernelModel,
    KernelStatusResponse,
    KernelWipeResponse,
    RetryExecuteRequest,
    RootResponse,
    SessionCreateRequest,
)
from kernelbox.store.registry import create_registry


config = KernelBoxConfig.from_env()
registry = create_registry(config)
manager = KernelManagerService(config=config, registry=registry)
executor = KernelExecutor(config=config, registry=registry)
sessions = SessionManager(manager=manager, registry=registry)
retry = RetryController(executor=executor, config=config, registry=registry)


app = FastAPI(
    title="KernelBox API",
    summary="Lightweight IPython kernel lifecycle and execution service.",
    description=(
        "KernelBox manages Jupyter kernels directly through jupyter_client. "
        "Use these endpoints to create named kernels, run Python or bash code, "
        "inspect status, retry executions, and clean up processes without a "
        "notebook server."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Service",
            "description": "Health checks and API discovery.",
        },
        {
            "name": "Kernels",
            "description": "Kernel lifecycle management.",
        },
        {
            "name": "Sessions",
            "description": "Human-readable sessions mapped one-to-one to kernels.",
        },
        {
            "name": "Execution",
            "description": "Structured code execution and retry operations.",
        },
    ],
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
)


@app.get("/", response_model=RootResponse, tags=["Service"], summary="API discovery")
def root() -> RootResponse:
    return RootResponse(
        service="kernelbox",
        links={
            "swagger": ApiLink(href="/docs", description="Interactive Swagger UI."),
            "redoc": ApiLink(href="/redoc", description="Readable API reference."),
            "openapi": ApiLink(href="/openapi.json", description="OpenAPI schema."),
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["Service"], summary="Health check")
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="kernelbox", version="0.1.0")


@app.post(
    "/kernels",
    response_model=KernelModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Kernels"],
    summary="Create a kernel",
    responses={409: {"description": "A live kernel already uses that name."}},
)
def create_kernel(request: KernelCreateRequest) -> KernelModel:
    try:
        record = manager.create(
            name=request.name,
            session_name=request.session_name,
            tags=request.tags,
        )
    except KernelAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return KernelModel.from_record(record)


@app.get(
    "/kernels",
    response_model=KernelListResponse,
    tags=["Kernels"],
    summary="List registered kernels",
)
def list_kernels(
    refresh: bool = Query(
        default=False,
        description="Ping each kernel before returning registry data.",
    )
) -> KernelListResponse:
    return KernelListResponse(
        kernels=[KernelModel.from_record(record) for record in manager.list(refresh=refresh)]
    )


@app.delete(
    "/kernels",
    response_model=KernelWipeResponse,
    tags=["Kernels"],
    summary="Destroy all registered kernels",
)
def wipe_kernels() -> KernelWipeResponse:
    return KernelWipeResponse(destroyed=manager.wipe_all())


@app.get(
    "/kernels/{identifier}",
    response_model=KernelStatusResponse,
    tags=["Kernels"],
    summary="Get kernel status",
)
def get_kernel(identifier: str) -> KernelStatusResponse:
    record = _require_kernel(identifier)
    alive = manager.ping(record)
    refreshed = manager.get(record.kernel_id) or record
    return KernelStatusResponse(alive=alive, kernel=KernelModel.from_record(refreshed))


@app.post(
    "/kernels/{identifier}/restart",
    response_model=KernelModel,
    tags=["Kernels"],
    summary="Restart a kernel",
)
def restart_kernel(identifier: str) -> KernelModel:
    _require_kernel(identifier)
    return KernelModel.from_record(manager.restart(identifier))


@app.delete(
    "/kernels/{identifier}",
    response_model=KernelDestroyedResponse,
    tags=["Kernels"],
    summary="Destroy a kernel",
)
def destroy_kernel(identifier: str) -> KernelDestroyedResponse:
    _require_kernel(identifier)
    return KernelDestroyedResponse(destroyed=manager.destroy(identifier))


@app.post(
    "/kernels/{identifier}/execute",
    response_model=ExecutionResultModel,
    tags=["Execution"],
    summary="Execute code in a kernel",
)
def execute_code(identifier: str, request: ExecuteRequest) -> ExecutionResultModel:
    record = _require_kernel(identifier)
    result = executor.execute(
        record,
        request.code,
        language=request.language,
        timeout=request.timeout,
    )
    return ExecutionResultModel.from_result(result)


@app.post(
    "/kernels/{identifier}/execute/retry",
    response_model=ExecutionResultModel,
    tags=["Execution"],
    summary="Execute code with retry attempts",
    description=(
        "Runs code repeatedly until success or max attempts. REST clients cannot "
        "send a Python callback, so replacement_codes provides deterministic "
        "repair snippets for later attempts."
    ),
)
def execute_code_with_retry(
    identifier: str,
    request: RetryExecuteRequest,
) -> ExecutionResultModel:
    record = _require_kernel(identifier)

    def on_error(_result: ExecutionResult, attempt: int) -> str | None:
        index = attempt - 1
        if index < len(request.replacement_codes):
            return request.replacement_codes[index]
        return None

    result = retry.execute_with_retry(
        record,
        request.code,
        on_error_fn=on_error,
        max_attempts=request.max_attempts,
        language=request.language,
        timeout=request.timeout,
    )
    return ExecutionResultModel.from_result(result)


@app.post(
    "/sessions/{name}",
    response_model=KernelModel,
    tags=["Sessions"],
    summary="Get or create a named session",
)
def get_or_create_session(
    name: str,
    request: SessionCreateRequest | None = None,
) -> KernelModel:
    record = sessions.get_or_create(name, tags=request.tags if request else None)
    return KernelModel.from_record(record)


@app.post(
    "/sessions/{name}/execute",
    response_model=ExecutionResultModel,
    tags=["Sessions", "Execution"],
    summary="Execute code in a named session",
)
def execute_session(name: str, request: ExecuteRequest) -> ExecutionResultModel:
    record = sessions.get_or_create(name)
    result = executor.execute(
        record,
        request.code,
        language=request.language,
        timeout=request.timeout,
    )
    return ExecutionResultModel.from_result(result)


def _require_kernel(identifier: str) -> KernelRecord:
    record = manager.get(identifier)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown kernel: {identifier}",
        )
    return record

