import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.routers.v1 import crud
from app.routers.log import logging as log_router
from app.routers.chat import chat as chat_router
from app.middleware.metrics_middleware import MetricsMiddleware
from app.services.kafka_consumer import kafka_consumer_service
from app.services.message_handler import message_handler
from app.services.metrics_service import metrics_service
from app.database.connection import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def emit_system_metrics():
    """Emit system metrics every 30 seconds"""
    while True:
        try:
            metrics_service.send_system_metrics()
            await asyncio.sleep(60)  # 30 second interval
        except Exception as e:
            print(f"Error emitting system metrics: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables and start Kafka consumers
    create_tables()
    
    # Start Kafka consumers with message handler
    kafka_consumer_service.start_consumer(
        topics=["api-metrics", "system-metrics", "api-errors"],
        group_id="backend-consumer",
        message_handler=message_handler.handle_kafka_message
    )
    
    kafka_consumer_service.start_consumer(
        topics=["ui-errors"],
        group_id="frontend-consumer", 
        message_handler=message_handler.handle_kafka_message
    )
    
    # Start system metrics emission
    asyncio.create_task(emit_system_metrics())
    
    yield
    
    # Shutdown: Stop Kafka consumers and flush remaining batches
    message_handler.flush_all_batches()
    kafka_consumer_service.stop_all_consumers()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(crud.router, prefix="/api/v1", tags=["crud"])
app.include_router(log_router.router, prefix="/api/log", tags=["logging"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "AppPulse Backend API", "version": settings.app_version}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "apppulse-backend"}