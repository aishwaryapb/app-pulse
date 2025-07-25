import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.metrics_service import metrics_service
from app.config import settings

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only collect metrics for /api/v1 endpoints
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)
        
        # Skip if metrics collection is disabled
        if not settings.collect_metrics:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Send metrics to Kafka
            metrics_service.send_api_metrics(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=process_time
            )
            
            # Send API error if status code >= 400
            if response.status_code >= 400:
                metrics_service.send_api_error(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    response_time=process_time
                )
            
            # Add response time header for debugging
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Handle errors and still send metrics
            process_time = time.time() - start_time
            
            # Send error metrics
            metrics_service.send_api_metrics(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time=process_time
            )
            
            # Send API error
            metrics_service.send_api_error(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time=process_time,
                exception=e
            )
            
            # Log the error
            logger.error(f"Error processing request {request.method} {request.url.path}: {e}")
            
            # Re-raise the exception
            raise e