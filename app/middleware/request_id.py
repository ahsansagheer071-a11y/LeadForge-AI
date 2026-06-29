import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Attach request_id to state so it can be accessed in logging or controllers
        request.state.request_id = request_id
        
        # Set start time
        start_time = time.perf_counter()
        
        # Log request receipt
        logger.info(
            f"[{request_id}] Incoming request: {request.method} {request.url.path} "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Add X-Request-ID header to response
            response.headers["X-Request-ID"] = request_id
            
            # Calculate execution duration
            duration = (time.perf_counter() - start_time) * 1000
            
            # Log response status
            logger.info(
                f"[{request_id}] Outgoing response: {request.method} {request.url.path} "
                f"Status: {response.status_code} | Duration: {duration:.2f}ms"
            )
            return response
            
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] Request failed: {request.method} {request.url.path} | "
                f"Error: {str(e)} | Duration: {duration:.2f}ms",
                exc_info=True
            )
            raise e
