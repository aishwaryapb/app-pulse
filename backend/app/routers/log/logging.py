from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import APIError, UIError
from app.services.kafka_service import kafka_service
from app.services.metrics_service import metrics_service
from app.services.memory_storage import memory_storage
from app.models.schemas import ErrorLogRequest
from app.database.connection import get_async_session
from datetime import datetime

router = APIRouter()

@router.get("/api-logs")
async def get_api_logs(db: AsyncSession = Depends(get_async_session)):
    """Get API error logs"""
    result = await db.execute(
        select(APIError).order_by(APIError.timestamp.desc()).limit(50)
    )
    return result.scalars().all()

@router.get("/ui-logs") 
async def get_ui_logs(db: AsyncSession = Depends(get_async_session)):
    """Get UI error logs"""
    result = await db.execute(
        select(UIError).order_by(UIError.timestamp.desc()).limit(50)
    )
    return result.scalars().all()

@router.post("/errors")
async def log_error(error: ErrorLogRequest):
    """Log errors from frontend"""
    error_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "frontend",
        "type": "error",
        "data": {
            "error_type": error.error_type,
            "error_message": error.error_message,
            "stack_trace": error.stack_trace,
            "user_id": error.user_id,
            "additional_data": error.additional_data or {}
        }
    }
    
    success = kafka_service.send_message("ui-errors", error_data)
    
    return {
        "message": "Error logged successfully" if success else "Failed to log error",
        "success": success
    }
    
@router.post("/system-metrics")
async def send_system_metrics():
    """Manually send system metrics to Kafka"""
    metrics_service.send_system_metrics()
    return {"message": "System metrics sent to Kafka"}


@router.get("/dashboard-data")
async def get_dashboard_data():
    """Get real-time dashboard data for developer persona"""
    return memory_storage.get_dashboard_data()