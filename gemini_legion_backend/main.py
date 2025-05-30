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
from .api.rest.endpoints import health, minions, channels

# WebSocket management
from .api.websocket import connection_manager

# Schemas
from .api.rest.schemas import WebSocketMessage, WebSocketCommand

# Core systems
from .core.infrastructure.adk.agents import MinionFactory
from .core.infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from .core.infrastructure.messaging.safeguards import CommunicationSafeguards

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
    
    # Initialize shared systems
    app.state.comm_system = InterMinionCommunicationSystem()
    app.state.safeguards = CommunicationSafeguards()
    
    # Initialize minion factory
    app.state.minion_factory = MinionFactory(
        comm_system=app.state.comm_system,
        safeguards=app.state.safeguards
    )
    
    # Initialize default channels (handled in channels endpoint)
    from .api.rest.endpoints.channels import init_default_channels
    init_default_channels()
    
    logger.info("✅ Gemini Legion Backend initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Gemini Legion Backend shutting down...")
    
    # Shutdown all minions
    try:
        await app.state.minion_factory.shutdown_all()
    except Exception as e:
        logger.error(f"Error shutting down minions: {e}")
    
    # Connection manager will handle WebSocket cleanup
    
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
app.include_router(health.router)
app.include_router(minions.router)
app.include_router(channels.router)

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
            # Check minion health
            factory = app.state.minion_factory
            for minion_id in factory.list_minions():
                minion = factory.get_minion(minion_id)
                if minion:
                    # Check if minion needs emotional state update
                    emotional_state = minion.emotional_engine.get_current_state()
                    
                    # Broadcast if stress is high
                    if emotional_state.stress_level > 0.8:
                        await broadcast_minion_update(
                            minion_id,
                            "high_stress",
                            {
                                "stress_level": emotional_state.stress_level,
                                "mood": emotional_state.mood.to_dict()
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