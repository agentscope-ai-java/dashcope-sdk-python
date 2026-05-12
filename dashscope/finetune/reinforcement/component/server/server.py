"""
server/server.py

Extensible HTTP POST server supporting function type configuration via environment variables and dynamic processor class loading.

== Environment Variables ==

    FUNC_TYPE           Function type, current supported values: "reward"/"rollout" (required)
    PROCESSOR_CLASS     Full Python path to processor class, e.g.:
                            dashscope.agenticRL.component.demo.reward_processor_demo.DemoRewardProcessor
                        (required, processor instantiated using this class)
    SERVER_PORT         Server port, default 8000
    ENABLE_LOGGING      Enable verbose logging, "true"/"1" to enable, default enabled
    THREAD_POOL_WORKERS Max worker threads, default 4
    THREAD_POOL_QUEUE   Max internal queue size (returns 503 when exceeded), default 100

== Startup Methods ==

    # Recommended: Run with python -m
    FUNC_TYPE=reward PROCESSOR_CLASS=dashscope.agenticRL.component.demo.reward_processor_demo.DemoRewardProcessor python -m dashscope.agenticRL.server.server

    # Using uvicorn
    FUNC_TYPE=reward PROCESSOR_CLASS=dashscope.agenticRL.component.demo.reward_processor_demo.DemoRewardProcessor uvicorn dashscope.agenticRL.server.server:app --host 0.0.0.0 --port 8000

== Endpoints ==

    POST /api/v1       Execute business logic (request body parsing based on FUNC_TYPE)
    GET  /health       Health check
"""
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from dashscope.finetune.reinforcement.common.log import logger
from dashscope.finetune.reinforcement.common.model_types import \
    FunctionType as FuncType
from dashscope.finetune.reinforcement.component.func_manager import FuncManager
from dashscope.finetune.reinforcement.component.observability.tracing import (
    ensure_agentic_rl_baggage_span_processor,
    is_tracing_enabled,
    maybe_force_flush_async,
    reset_upstream_trace_linkage,
    set_upstream_trace_linkage,
)

# ============================================================================ #
#                             Environment Config                               #
# ============================================================================ #

_FUNC_TYPE_ENV = os.getenv("FUNC_TYPE", "").strip().lower()
_PROCESSOR_CLASS_ENV = os.getenv("PROCESSOR_CLASS", "").strip()
_SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
_ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").strip().lower() not in (
"false", "0", "no")
_THREAD_POOL_WORKERS = int(os.getenv("THREAD_POOL_WORKERS", "4"))
_THREAD_POOL_QUEUE = int(os.getenv("THREAD_POOL_QUEUE", "100"))

if not _ENABLE_LOGGING:
    logging.disable(logging.INFO)


# ============================================================================ #
#                          Func Type Resolution                                #
# ============================================================================ #

def _resolve_func_type(raw: str) -> FuncType:
    """Parse string to FuncType, raises ValueError for invalid types."""
    try:
        return FuncType(raw)
    except ValueError:
        valid = [t.value for t in FuncType]
        raise ValueError(
            f"Unsupported FUNC_TYPE='{raw}'. Valid values: {valid}"
        )


# ============================================================================ #
#                          Server Initialization                               #
# ============================================================================ #

# Validate FUNC_TYPE
if not _FUNC_TYPE_ENV:
    raise RuntimeError(
        "Environment variable FUNC_TYPE is required. "
        "Example: FUNC_TYPE=reward"
    )

func_type: FuncType = _resolve_func_type(_FUNC_TYPE_ENV)
logger.info(f"[Server] FUNC_TYPE={func_type.value}")

# Validate PROCESSOR_CLASS (required)
if not _PROCESSOR_CLASS_ENV:
    raise RuntimeError(
        "Environment variable PROCESSOR_CLASS is required. "
        "Example: PROCESSOR_CLASS=dashscope.agenticRL.component.demo.reward_processor_demo.DemoRewardProcessor"
    )

logger.info(f"[Server] PROCESSOR_CLASS={_PROCESSOR_CLASS_ENV}")

# Thread pool configuration (used for sync processors to avoid blocking event loop)
_executor = ThreadPoolExecutor(max_workers=_THREAD_POOL_WORKERS)

# Initialize FuncManager for unified parsing and processing
func_manager: FuncManager = FuncManager.create_from_env(
    func_type=func_type,
    processor_class_path=_PROCESSOR_CLASS_ENV,
)
# Use the server's executor for sync processor offload so queue control and capacity
# checks remain accurate.
func_manager.set_executor(_executor)
logger.info(
    f"[Server] FuncManager initialized | "
    f"parser={type(func_manager.parser).__name__} | "
    f"processor={type(func_manager.processor).__name__}"
)

# ============================================================================ #
#                              FastAPI App                                     #
# ============================================================================ #
app = FastAPI(
    title="AgenticRL Func Server",
    version="1.0.0",
    description=(
        f"Extensible AgenticRL function service. "
        f"Current function type: {func_type.value} | "
        f"Processor class: {type(func_manager.processor).__name__}"
    ),
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles request validation errors, logs details and returns 422."""
    errors = exc.errors()
    error_details = [
        {
            "loc": e.get("loc"),
            "msg": e.get("msg"),
            "type": e.get("type"),
            "input": str(e.get("input", ""))[:200],
        }
        for e in errors
    ]

    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8", errors="ignore")
    except Exception as ex:
        body_str = f"Failed to read request body: {str(ex)}"

    logger.error(f"[Server] Request validation error: {error_details}")
    logger.error(f"[Server] Request body: {body_str}")

    return JSONResponse(
        status_code=422,
        content={"detail": error_details, "body": body_str},
    )


@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event handler.
    
    Calls the processor's setup() method to initialize workspace
    before the server starts processing requests.
    Also registers BaggageSpanProcessor for OTel tracing if enabled.
    """
    logger.info("[Server] Starting up... calling processor.setup()")
    try:
        await func_manager.setups()

        logger.info("[Server] Processor setup completed successfully")
    except Exception as ex:
        logger.error(f"[Server] Processor setup failed: {ex}", exc_info=True)
        raise RuntimeError(f"Processor setup failed: {ex}")

    if is_tracing_enabled():
        ensure_agentic_rl_baggage_span_processor()
        logger.info("[Server] OTel BaggageSpanProcessor registered")


@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI shutdown event handler.

    Best-effort force flush spans during graceful worker shutdown to reduce
    tail-span loss during graceful worker shutdown. Force flush is controlled
    by platform/internal runtime configuration (see AGENTIC_RL_FORCE_FLUSH_MODE).
    """

    await maybe_force_flush_async(reason="shutdown")


@app.post("/api/v1")
async def handle_endpoint(request: Request) -> JSONResponse:
    """
    Unified business processing endpoint.

    Automatically selects corresponding parser based on FUNC_TYPE to process request body,
    executes business logic using configured processor, and returns serialized result.

    Request body format: JSON, fields determined by FuncType:
    - reward: See RewardInput
    - rollout: See RolloutInput
    """
    start_time = time.time()
    success = False
    result = None
    processor_input = None
    _otel_ctx_token = None
    _upstream_tokens = None

    # If upstream (e.g. RFT) passes W3C Trace Context headers (traceparent/baggage),
    # extract and attach them so all spans created in this request inherit the parent.
    # Never fail the request if extraction is unavailable or malformed.
    if is_tracing_enabled():
        has_traceparent = "traceparent" in request.headers
        upstream_trace_id = request.headers.get("x-request-id")
        extracted_ok = False
        try:
            from opentelemetry import context as otel_context
            from opentelemetry.propagate import extract as otel_extract

            ctx = otel_extract(dict(request.headers))
            _otel_ctx_token = otel_context.attach(ctx)
            extracted_ok = True
        except Exception:
            _otel_ctx_token = None

        linked = bool(has_traceparent and extracted_ok)
        _upstream_tokens = set_upstream_trace_linkage(
            traceparent_present=linked,
            upstream_trace_id=upstream_trace_id,
        )
        logger.debug(
            "[Server] Upstream trace linkage: linked=%s x-request-id=%s",
            linked,
            upstream_trace_id or "(missing)",
        )

    try:
        # 1. Parse request body
        try:
            raw_body = await request.json()
        except Exception as ex:
            logger.error(f"[Server] Failed to parse JSON body: {ex}")
            raise HTTPException(status_code=400,
                                detail=f"Invalid JSON body: {str(ex)}")

        # 2. Parse request using FuncManager
        try:
            processor_input = func_manager.parses(raw_body)
        except Exception as ex:
            logger.error(f"[Server] Request parsing failed: {ex}")
            raise HTTPException(status_code=422,
                                detail=f"Request parsing error: {str(ex)}")

        # 3. Check thread pool queue capacity
        queue_size = _executor._work_queue.qsize()
        if queue_size >= _THREAD_POOL_QUEUE:
            error_msg = (
                f"Too many concurrent requests. "
                f"Thread pool queue is full (queue_size={queue_size}, max={_THREAD_POOL_QUEUE})"
            )
            logger.error(f"[Server] {error_msg}")
            raise HTTPException(status_code=503,
                                detail="Server is busy, please try again later.")

        # 4. Execute processor
        result = await func_manager.processes(processor_input)

        success = True

        # 5. Serialize result
        if hasattr(result, "model_dump"):
            response_data = result.model_dump()
        elif isinstance(result, dict):
            response_data = result
        else:
            response_data = {"result": result}

        return JSONResponse(
            status_code=200,
            content=response_data,
        )

    except HTTPException:
        raise

    except Exception as ex:
        logger.error(f"[Server] Unexpected error: {ex}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "message": str(ex),
            },
        )

    finally:
        if _otel_ctx_token is not None:
            try:
                from opentelemetry import context as otel_context

                otel_context.detach(_otel_ctx_token)
            except Exception:
                pass
        if _upstream_tokens is not None:
            try:
                reset_upstream_trace_linkage(_upstream_tokens)
            except Exception:
                pass
        elapsed = round(time.time() - start_time, 4)
        logger.info(
            f"[Server] /api/v1 | func_type={func_type.value} | "
            f"success={success} | elapsed={elapsed}s"
        )
        # Best-effort flush based on platform/internal env config.
        await maybe_force_flush_async(reason="request")


@app.get("/health")
async def health_check_endpoint() -> JSONResponse:
    """
    Health check endpoint.

    Returns service status, current function type and processor information.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "func_type": func_type.value,
            "processor": type(func_manager.processor).__name__,
            "parser": type(func_manager.parser).__name__,
        },
    )


# ============================================================================ #
#                                  Entry Point                                 #
# ============================================================================ #

if __name__ == "__main__":
    """
    Direct execution entry point for FastAPI server.

    Alternative startup using uvicorn:
        uvicorn dashscope.agenticRL.server.server:app --host 0.0.0.0 --port 8000
    """
    import uvicorn
    import sys
    import argparse
    import os
    import multiprocessing

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    args, remaining = parser.parse_known_args()

    # Get port from environment or use default
    _SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))

    # Calculate worker count (half of CPU cores, max 8)
    cpu_count = multiprocessing.cpu_count() or 1  # Fallback to 1 if None
    if "WORKERS_COUNT" in os.environ:
        worker_count = max(int(os.environ["WORKERS_COUNT"]), 1)
    else:
        worker_count = cpu_count

    logger.info(f"[Server] Starting server on port {_SERVER_PORT}")
    # logger.info(f"[Server] Trajectory logging enabled: {is_tracing_enabled()}")
    logger.info(
        f"[Server] Using {worker_count} workers (CPU cores: {cpu_count})")

    # Pass remaining arguments to uvicorn
    sys.argv = [sys.argv[0]] + remaining

    # Start uvicorn with calculated worker count
    uvicorn.run(
        "dashscope.finetune.reinforcement.component.server.server:app",  # app,
        host="0.0.0.0",
        port=_SERVER_PORT,
        workers=worker_count,
        reload=False
    )
