"""
Rate Limiting Middleware
Prevents API abuse by limiting requests per IP address
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that restricts number of requests per IP
    
    Attributes:
        calls: Maximum number of requests allowed in the period
        period: Time window in seconds
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP (handle proxy cases)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for forwarded IP (when behind reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        now = time.time()
        
        # Clean old requests (older than period)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429, 
                detail=f"Too many requests. Limit: {self.calls} requests per {self.period} seconds."
            )
        
        # Add current request timestamp
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))
        
        return response