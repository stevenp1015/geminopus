"""
Main FastAPI Application

The Python ADK-powered backend for managing the Legion of AI Minions.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import asyncio
import logging
import os
from datetime import datetime

# API routers
from .api.rest.endpoints import health_router, minions_router, channels_router, tasks_router

# WebSocket management
from .api.websocket import connection_manager

# Schemas
from .api.rest.schemas import WebSocketMessage, WebSocketCommand

# Core systems
from .core.dependencies import initialize_services, shutdown_services, get_service_container

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Gemini Legion Backend starting...")
    
    # Initialize all services
    await initialize_services()
    
    # Store service container in app state for easy access
    app.state.services = get_service_container()
    
    # Set up WebSocket manager with services
    connection_manager.set_services(app.state.services)
    
    logger.info("✅ Gemini Legion Backend initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Gemini Legion Backend shutting down...")
    
    # Shutdown all services
    await shutdown_services()
    
    logger.info("👋 Gemini Legion Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Gemini Legion Backend",
    description="The Python ADK-powered backend for managing the Legion of AI Minions",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(minions_router)
app.include_router(channels_router)
app.include_router(tasks_router)

# Mount static files if they exist
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# --- WebSocket Handler ---

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection for real-time updates"""
    await connection_manager.connect(client_id, websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            command = WebSocketCommand(**data)
            
            # Handle commands through connection manager
            await connection_manager.handle_command(client_id, command)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)


# --- Broadcast Functions ---

async def broadcast_message(channel_id: str, message: dict):
    """Broadcast a message to all connected websockets"""
    await connection_manager.broadcast_to_channel(channel_id, message)


async def broadcast_minion_update(minion_id: str, update_type: str, data: dict):
    """Broadcast minion status updates"""
    await connection_manager.broadcast_minion_update(minion_id, update_type, data)


async def broadcast_channel_update(channel_id: str, update_type: str, data: dict):
    """Broadcast channel updates"""
    await connection_manager.broadcast_to_channel(
        channel_id,
        {
            "update_type": update_type,
            **data
        }
    )


# --- Root Endpoint ---

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Gemini Legion Backend",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/api/docs",
        "websocket": "/ws/{client_id}"
    }


# --- Background Tasks ---

async def periodic_health_check():
    """Periodic health check and monitoring"""
    while True:
        try:
            # Get services
            services = get_service_container()
            minion_service = services.get_minion_service()
            
            # Check all minions
            minions = await minion_service.list_minions()
            for minion_data in minions:
                minion_id = minion_data["minion_id"]
                emotional_state = minion_data.get("emotional_state", {})
                
                # Broadcast if stress is high
                stress_level = emotional_state.get("stress_level", 0.0)
                if stress_level > 0.8:
                    await broadcast_minion_update(
                        minion_id,
                        "high_stress",
                        {
                            "stress_level": stress_level,
                            "mood": emotional_state.get("mood", {})
                        }
                    )
            
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in periodic health check: {e}")
            await asyncio.sleep(60)  # Back off on error


@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(periodic_health_check())


# --- Main Entry Point ---

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting Gemini Legion Backend on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )