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

import socketio

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
    connection_manager.set_sio_instance(sio) # We'll add this method to ConnectionManager
    connection_manager.set_services(app.state.services) # Existing call
    
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

# Socket.IO Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*') # Adjust cors_allowed_origins as needed

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

# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: str):
#     """WebSocket connection for real-time updates"""
#     await connection_manager.connect(client_id, websocket)
    
#     try:
#         while True:
#             # Receive messages from client
#             data = await websocket.receive_json()
#             command = WebSocketCommand(**data)
            
#             # Handle commands through connection manager
#             await connection_manager.handle_command(client_id, command)
            
#     except WebSocketDisconnect:
#         connection_manager.disconnect(client_id)
#     except Exception as e:
#         logger.error(f"WebSocket error for client {client_id}: {e}")
#         connection_manager.disconnect(client_id)

# --- Socket.IO Event Handlers ---
@sio.event
async def connect(sid, environ, auth):
    logger.info(f"Socket.IO client connected: {sid}")
    # Extract client_id from auth or generate/assign if not provided
    # For now, we can use sid as client_id or expect it in auth
    client_id = auth.get("client_id") if auth else sid
    await connection_manager.handle_connect(sid, client_id) # We'll add handle_connect to ConnectionManager

@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO client disconnected: {sid}")
    await connection_manager.handle_disconnect(sid) # We'll add handle_disconnect to ConnectionManager

# Placeholder for client commands - these will be moved/adapted from ConnectionManager.handle_command
# @sio.on("*") # Default handler for any other event
# async def any_event(event, sid, data):
#     logger.debug(f"Socket.IO event received: {event} from {sid} with data: {data}")
#     # This is where commands like 'subscribe_channel' would be handled.
#     # We'll delegate to connection_manager.handle_sio_command(event, sid, data) later.
#     # For now, just log.
#     pass

@sio.on("ping")
async def handle_ping(sid, data: Optional[Dict] = None):
    logger.debug(f"Received 'ping' from SID: {sid}")
    await connection_manager.handle_sio_command("ping", sid, data if data else {})

@sio.on("subscribe_channel")
async def handle_subscribe_channel(sid, data: Dict):
    logger.debug(f"Received 'subscribe_channel' from SID: {sid} with data: {data}")
    await connection_manager.handle_sio_command("subscribe_channel", sid, data)

@sio.on("unsubscribe_channel")
async def handle_unsubscribe_channel(sid, data: Dict):
    logger.debug(f"Received 'unsubscribe_channel' from SID: {sid} with data: {data}")
    await connection_manager.handle_sio_command("unsubscribe_channel", sid, data)

@sio.on("subscribe_minion")
async def handle_subscribe_minion(sid, data: Dict):
    logger.debug(f"Received 'subscribe_minion' from SID: {sid} with data: {data}")
    await connection_manager.handle_sio_command("subscribe_minion", sid, data)

@sio.on("unsubscribe_minion") # Added handler for symmetry with ConnectionManager
async def handle_unsubscribe_minion(sid, data: Dict):
    logger.debug(f"Received 'unsubscribe_minion' from SID: {sid} with data: {data}")
    await connection_manager.handle_sio_command("unsubscribe_minion", sid, data)

@sio.on("get_subscriptions")
async def handle_get_subscriptions(sid, data: Optional[Dict] = None):
    logger.debug(f"Received 'get_subscriptions' from SID: {sid}")
    await connection_manager.handle_sio_command("get_subscriptions", sid, data if data else {})

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


# --- Main Entry Point ---

# Wrap FastAPI app with Socket.IO
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting Gemini Legion Backend on {host}:{port}")
    
    uvicorn.run(
        "gemini_legion_backend.main:asgi_app",  # Use full module path
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )