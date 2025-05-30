"""
Main FastAPI Application

The Python ADK-powered backend for managing the Legion of AI Minions.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import asyncio
import uuid
from datetime import datetime

# Domain imports
from ..core.domain import (
    MinionPersona,
    EmotionalState,
    MoodVector,
    WorkingMemory,
    Channel,
    Message,
    MessageType
)

# Infrastructure imports
from ..core.infrastructure.adk.agents.minion_agent import MinionAgent
from ..core.infrastructure.adk.emotional_engine import EmotionalEngine
from ..core.infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from ..core.infrastructure.messaging.safeguards import CommunicationSafeguards


# Global state (will be replaced with proper persistence)
minions: Dict[str, MinionAgent] = {}
channels: Dict[str, Channel] = {}
messages: Dict[str, List[Message]] = {}
websocket_connections: Dict[str, WebSocket] = {}

# Core systems
communication_system = InterMinionCommunicationSystem()
safeguards = CommunicationSafeguards()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("🚀 Gemini Legion Backend starting...")
    
    # Initialize default channels
    channels["general"] = Channel(
        channel_id="general",
        name="General",
        description="Main communication channel for the Legion",
        members=[]
    )
    channels["minion-banter"] = Channel(
        channel_id="minion-banter",
        name="Minion Banter",
        description="Where Minions chat amongst themselves",
        members=[]
    )
    channels["task-coordination"] = Channel(
        channel_id="task-coordination",
        name="Task Coordination",
        description="For coordinating on tasks",
        members=[]
    )
    
    yield
    
    # Shutdown
    print("🛑 Gemini Legion Backend shutting down...")


# Create app
app = FastAPI(
    title="Gemini Legion Backend",
    description="The Python ADK-powered backend for managing the Legion of AI Minions",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST Endpoints ---

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "minion_count": len(minions),
        "active_channels": len(channels)
    }


@app.get("/api/minions")
async def get_minions():
    """Get all active minions"""
    return {
        "minions": [
            {
                "id": minion_id,
                "name": agent.persona.name,
                "personality": agent.persona.base_personality,
                "status": "active",  # Simplified for now
                "emotional_state": agent.emotional_engine.get_current_state().to_snapshot()
            }
            for minion_id, agent in minions.items()
        ]
    }


@app.post("/api/minions")
async def create_minion(persona_config: dict):
    """Create a new minion"""
    try:
        # Generate ID
        minion_id = f"minion_{uuid.uuid4().hex[:8]}"
        
        # Create persona
        persona = MinionPersona(
            name=persona_config["name"],
            base_personality=persona_config["personality"],
            quirks=persona_config.get("quirks", []),
            catchphrases=persona_config.get("catchphrases", []),
            expertise_areas=persona_config.get("expertise", []),
            allowed_tools=persona_config.get("tools", [])
        )
        
        # Create initial emotional state
        initial_mood = MoodVector(
            valence=0.0,
            arousal=0.5,
            dominance=0.5
        )
        emotional_state = EmotionalState(
            minion_id=minion_id,
            mood=initial_mood
        )
        
        # Create emotional engine
        emotional_engine = EmotionalEngine(emotional_state)
        
        # Create memory system
        memory_system = WorkingMemory()
        
        # Create minion agent
        minion_agent = MinionAgent(
            minion_id=minion_id,
            persona=persona,
            emotional_engine=emotional_engine,
            memory_system=memory_system
        )
        
        # Store in global state
        minions[minion_id] = minion_agent
        
        # Add to default channels
        for channel in channels.values():
            if channel.channel_id in ["general", "minion-banter"]:
                channel.members.append(minion_id)
        
        # Subscribe to channels
        async def handle_message(msg):
            # Handle incoming messages for this minion
            pass
        
        communication_system.subscribe_to_channel("general", handle_message)
        communication_system.subscribe_to_channel("minion-banter", handle_message)
        
        return {
            "id": minion_id,
            "name": persona.name,
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/minions/{minion_id}")
async def delete_minion(minion_id: str):
    """Remove a minion"""
    if minion_id not in minions:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    # Remove from channels
    for channel in channels.values():
        if minion_id in channel.members:
            channel.members.remove(minion_id)
    
    # Remove minion
    del minions[minion_id]
    
    return {"status": "deleted", "id": minion_id}


@app.get("/api/channels")
async def get_channels():
    """Get all channels"""
    return {
        "channels": [
            {
                "id": channel.channel_id,
                "name": channel.name,
                "description": channel.description,
                "members": channel.members,
                "is_private": channel.is_private
            }
            for channel in channels.values()
        ]
    }


@app.post("/api/channels")
async def create_channel(channel_config: dict):
    """Create a new channel"""
    channel_id = f"channel_{uuid.uuid4().hex[:8]}"
    
    channel = Channel(
        channel_id=channel_id,
        name=channel_config["name"],
        description=channel_config.get("description", ""),
        members=channel_config.get("members", []),
        is_private=channel_config.get("is_private", False)
    )
    
    channels[channel_id] = channel
    messages[channel_id] = []
    
    return {
        "id": channel_id,
        "name": channel.name,
        "status": "created"
    }


@app.get("/api/channels/{channel_id}/messages")
async def get_channel_messages(channel_id: str, limit: int = 50):
    """Get messages from a channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    channel_messages = messages.get(channel_id, [])
    
    return {
        "messages": [
            {
                "id": msg.message_id,
                "sender": msg.sender_id,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "type": msg.message_type.value
            }
            for msg in channel_messages[-limit:]
        ]
    }


@app.post("/api/channels/{channel_id}/messages")
async def send_message(channel_id: str, message_data: dict):
    """Send a message to a channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Create message
    message = Message(
        message_id=str(uuid.uuid4()),
        channel_id=channel_id,
        sender_id=message_data["sender"],
        content=message_data["content"],
        message_type=MessageType.CHAT
    )
    
    # Check safeguards (only for minion senders)
    if message_data["sender"] != "commander":
        allowed, reason = await safeguards.check_message_allowed(
            message_data["sender"],
            channel_id,
            message_data["content"]
        )
        
        if not allowed:
            raise HTTPException(status_code=429, detail=reason)
    
    # Store message
    if channel_id not in messages:
        messages[channel_id] = []
    messages[channel_id].append(message)
    
    # Route through communication system
    if message_data["sender"] != "commander":
        await communication_system.send_conversational_message(
            from_minion=message_data["sender"],
            to_channel=channel_id,
            message=message_data["content"]
        )
    
    # Broadcast to websockets
    await broadcast_message(channel_id, message)
    
    # Process with minions if from commander
    if message_data["sender"] == "commander":
        await process_commander_message(channel_id, message)
    
    return {
        "id": message.message_id,
        "status": "sent"
    }


# --- WebSocket Endpoints ---

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection for real-time updates"""
    await websocket.accept()
    websocket_connections[client_id] = websocket
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Could handle commands here
            
    except WebSocketDisconnect:
        del websocket_connections[client_id]


# --- Helper Functions ---

async def broadcast_message(channel_id: str, message: Message):
    """Broadcast a message to all connected websockets"""
    message_data = {
        "type": "new_message",
        "channel": channel_id,
        "message": {
            "id": message.message_id,
            "sender": message.sender_id,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        }
    }
    
    disconnected = []
    for client_id, ws in websocket_connections.items():
        try:
            await ws.send_json(message_data)
        except:
            disconnected.append(client_id)
    
    # Clean up disconnected clients
    for client_id in disconnected:
        del websocket_connections[client_id]


async def process_commander_message(channel_id: str, message: Message):
    """Process a message from the commander with relevant minions"""
    channel = channels.get(channel_id)
    if not channel:
        return
    
    # Get minions in channel
    channel_minions = [
        minions[mid] for mid in channel.members
        if mid in minions
    ]
    
    if not channel_minions:
        return
    
    # Simple turn-based response (for now)
    # In production, would use the turn-taking engine
    for minion in channel_minions[:1]:  # Just first minion responds for now
        try:
            # Generate response
            response = await minion.think(message.content)
            
            # Create response message
            response_message = Message(
                message_id=str(uuid.uuid4()),
                channel_id=channel_id,
                sender_id=minion.minion_id,
                content=response,
                message_type=MessageType.CHAT
            )
            
            # Store and broadcast
            messages[channel_id].append(response_message)
            await broadcast_message(channel_id, response_message)
            
            # Small delay to feel natural
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Error processing message with {minion.minion_id}: {e}")


@app.post("/api/minions/{minion_id}/reboot")
async def reboot_minion(minion_id: str, hard_reset: bool = False):
    """Reboot a misbehaving minion"""
    if minion_id not in minions:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    minion = minions[minion_id]
    
    if hard_reset:
        # Hard reset - clear emotional state
        initial_mood = MoodVector(
            valence=0.0,
            arousal=0.5,
            dominance=0.5
        )
        new_emotional_state = EmotionalState(
            minion_id=minion_id,
            mood=initial_mood
        )
        minion.emotional_engine = EmotionalEngine(new_emotional_state)
        minion.memory_system = WorkingMemory()
        
        status = "hard_reset_complete"
    else:
        # Soft reset - just clear working memory
        minion.memory_system = WorkingMemory()
        status = "soft_reset_complete"
    
    return {
        "id": minion_id,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
