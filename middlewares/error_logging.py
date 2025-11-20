from starlette.middleware.base import BaseHTTPMiddleware
import time, logging

logger = logging.getLogger(__name__)

class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        except Exception:
            logger.debug(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else "-",
                    "latency_ms": int((time.perf_counter() - start) * 1000),
                },
            )
            raise
