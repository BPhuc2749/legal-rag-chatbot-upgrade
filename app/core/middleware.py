import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import (
    set_request_id,
    set_query,
    clear_context,
)

from app.core.logging import log_event
from app.core.tracer import RAGTracer


class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next
    ):
        # =========================
        # Request ID
        # =========================
        request_id = (
            request.headers.get("x-request-id")
            or str(uuid.uuid4())
        )

        # =========================
        # Extract query
        # =========================
        query = None

        if request.method == "GET":
            query = request.query_params.get(
                "question"
            )

        elif request.method == "POST":
            try:
                body = await request.json()

                query = body.get(
                    "question"
                )

            except Exception:
                query = None

        # =========================
        # Set context
        # =========================
        set_request_id(
            request_id
        )

        set_query(
            query or ""
        )

        # =========================
        # Attach tracer
        # =========================
        request.state.request_id = (
            request_id
        )

        request.state.tracer = (
            RAGTracer()
        )

        start_time = time.time()

        response: Response | None = None

        try:
            response = await call_next(
                request
            )

            return response

        finally:
            latency_ms = int(
                (time.time() - start_time)
                * 1000
            )

            log_event({
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": (
                    response.status_code
                    if response
                    else None
                ),
                "latency_ms": latency_ms,
            })

            # tránh leak context
            clear_context()