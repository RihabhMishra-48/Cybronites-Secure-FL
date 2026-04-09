"""
API Middleware — CORS, authentication, request logging, rate limiting.
"""

import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from secure_training_platform.config import API_KEY

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_TRAIN = 10  # max training submissions per window


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming API requests."""
    
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)
        
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} "
            f"({duration}ms)"
        )
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Simple API key authentication.
    Checks X-API-Key header for protected endpoints.
    """
    
    PROTECTED_PREFIXES = ["/api/v1/train"]
    
    async def dispatch(self, request: Request, call_next):
        # Only enforce on protected endpoints
        path = request.url.path
        needs_auth = any(path.startswith(p) for p in self.PROTECTED_PREFIXES)
        
        if needs_auth and request.method == "POST":
            api_key = request.headers.get("X-API-Key", "")
            if api_key != API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid or missing API key"}
                )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit training job submissions."""
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/v1/train" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            
            # Clean old entries
            _rate_limit_store[client_ip] = [
                t for t in _rate_limit_store[client_ip]
                if now - t < RATE_LIMIT_WINDOW
            ]
            
            if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_TRAIN:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Max {RATE_LIMIT_MAX_TRAIN} training jobs per minute"
                    }
                )
            
            _rate_limit_store[client_ip].append(now)
        
        return await call_next(request)
