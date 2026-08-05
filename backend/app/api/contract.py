"""Cross-cutting HTTP contract enforcement for the versioned public API."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.response import API_VERSION

logger = logging.getLogger("classroomiq.api")


def _metadata(request: Request, started_at: float) -> dict[str, Any]:
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execution_time": round((time.perf_counter() - started_at) * 1000, 2),
        "request_id": request.state.request_id,
        "api_version": API_VERSION,
    }


def _error_body(request: Request, started_at: float, status_code: int, message: str, details: Any = None) -> dict[str, Any]:
    codes = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 409: "CONFLICT", 413: "PAYLOAD_TOO_LARGE", 415: "UNSUPPORTED_MEDIA_TYPE", 422: "VALIDATION_ERROR"}
    return {
        "status": "ERROR",
        "message": message,
        "error": {"code": codes.get(status_code, "INTERNAL_SERVER_ERROR" if status_code >= 500 else "REQUEST_ERROR"), "details": details or []},
        "metadata": _metadata(request, started_at),
    }


def install_api_contract(app: FastAPI) -> None:
    """Install one response/error/logging contract without changing business services."""

    @app.middleware("http")
    async def api_contract(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started_at = time.perf_counter()
        request.state.started_at = started_at
        supplied_id = request.headers.get("X-Request-ID", "").strip()
        request.state.request_id = supplied_id[:128] or str(uuid.uuid4())
        response = await call_next(request)

        if not request.url.path.startswith("/api/v1") and request.url.path not in {"/", "/health"}:
            return response
        if response.status_code == 204 or "application/json" not in response.headers.get("content-type", ""):
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            payload = json.loads(body)
        except (TypeError, ValueError):
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

        if response.status_code >= 400:
            # Exception handlers already provide the canonical body. This guard
            # also protects hand-written JSON error responses in future routers.
            if not isinstance(payload, dict) or payload.get("status") != "ERROR":
                payload = _error_body(request, started_at, response.status_code, "Request failed", payload)
            else:
                payload["metadata"] = _metadata(request, started_at)
        elif not (isinstance(payload, dict) and {"status", "message", "data", "metadata"}.issubset(payload)):
            payload = {"status": "SUCCESS", "message": "Request completed.", "data": payload, "metadata": _metadata(request, started_at)}
        else:
            payload["metadata"] = _metadata(request, started_at)

        headers = dict(response.headers)
        headers.pop("content-length", None)
        headers["X-Request-ID"] = request.state.request_id
        elapsed = (time.perf_counter() - started_at) * 1000
        logger.info("%s %s status=%s duration_ms=%.2f request_id=%s", request.method, request.url.path, response.status_code, elapsed, request.state.request_id)
        return JSONResponse(content=payload, status_code=response.status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        started_at = getattr(request.state, "started_at", time.perf_counter())
        details = [{"field": ".".join(str(part) for part in item["loc"] if part != "body"), "message": item["msg"]} for item in exc.errors()]
        return JSONResponse(status_code=422, content=_error_body(request, started_at, 422, "Request validation failed.", details))

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: HTTPException | StarletteHTTPException) -> JSONResponse:
        started_at = getattr(request.state, "started_at", time.perf_counter())
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        details = [] if isinstance(detail, str) else detail
        return JSONResponse(status_code=exc.status_code, content=_error_body(request, started_at, exc.status_code, message, details))

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error request_id=%s", getattr(request.state, "request_id", "unknown"))
        started_at = getattr(request.state, "started_at", time.perf_counter())
        return JSONResponse(status_code=500, content=_error_body(request, started_at, 500, "An unexpected server error occurred."))

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        components["ApiEnvelope"] = {
            "type": "object",
            "required": ["status", "message", "data", "metadata"],
            "properties": {
                "status": {"type": "string", "example": "SUCCESS"},
                "message": {"type": "string", "example": "Request completed."},
                "data": {"description": "Endpoint-specific response payload"},
                "metadata": {
                    "type": "object",
                    "required": ["timestamp", "execution_time", "request_id", "api_version"],
                    "properties": {
                        "timestamp": {"type": "string", "format": "date-time"},
                        "execution_time": {"type": "number", "description": "Milliseconds"},
                        "request_id": {"type": "string", "format": "uuid"},
                        "api_version": {"type": "string", "example": "v1"},
                    },
                },
            },
        }
        components["ApiErrorEnvelope"] = {
            "type": "object",
            "required": ["status", "message", "error", "metadata"],
            "properties": {
                "status": {"type": "string", "example": "ERROR"},
                "message": {"type": "string"},
                "error": {"type": "object", "properties": {"code": {"type": "string"}, "details": {"type": "array", "items": {}}}},
                "metadata": {"$ref": "#/components/schemas/ApiEnvelope/properties/metadata"},
            },
        }
        error_responses = {str(code): {"description": "Standard API error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ApiErrorEnvelope"}}}} for code in (400, 401, 403, 404, 409, 413, 415, 422, 500)}
        for path, operations in schema.get("paths", {}).items():
            if not path.startswith("/api/v1"):
                continue
            for method, operation in operations.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                responses = operation.setdefault("responses", {})
                success = next((code for code in responses if code.startswith("2")), "200")
                responses[success] = {
                    "description": "Standard successful API response",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ApiEnvelope"}, "example": {"status": "SUCCESS", "message": "Request completed.", "data": {}, "metadata": {"timestamp": "2026-08-05T00:00:00Z", "execution_time": 12.34, "request_id": "00000000-0000-0000-0000-000000000000", "api_version": "v1"}}}},
                }
                for code, response in error_responses.items():
                    responses.setdefault(code, response)
                operation["description"] = (operation.get("description", "") + "\n\nAll responses use the ClassroomIQ v1 envelope. Send `X-Request-ID` to correlate logs; it is echoed in the response.").strip()
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
