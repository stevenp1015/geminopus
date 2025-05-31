"""
WebSocket handler for real-time communication

Manages WebSocket connections and real-time updates.
"""

from fastapi import WebSocket
from typing import Dict, Set, Optional, List
import asyncio
import logging
import json
from datetime import datetime

from ..schemas import WebSocketMessage, WebSocketCommand
from ....core.dependencies import ServiceContainer

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        # Active connections: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Channel subscriptions: channel_id -> Set[client_id]
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        
        # Client subscriptions: client_id -> Set[channel_id]
        self.client_subscriptions: Dict[str, Set[str]] = {}
        
        # Minion subscriptions: minion_id -> Set[client_id]
        self.minion_subscriptions: Dict[str, Set[str]] = {}
        
        # Service container (set during app startup)
        self.services: Optional[ServiceContainer] = None
    
    def set_services(self, services: ServiceContainer):
        """Set the service container for event broadcasting"""
        self.services = services
        logger.info("Services connected to WebSocket manager")
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send connection confirmation
        await self.send_personal_message(
            client_id,
            {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all subscriptions
        if client_id in self.client_subscriptions:
            for channel_id in self.client_subscriptions[client_id]:
                if channel_id in self.channel_subscriptions:
                    self.channel_subscriptions[channel_id].discard(client_id)
            del self.client_subscriptions[client_id]
        
        # Remove from minion subscriptions
        for minion_id, subscribers in self.minion_subscriptions.items():
            subscribers.discard(client_id)
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, client_id: str, message: dict):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_channel(self, channel_id: str, message: dict, exclude_client: Optional[str] = None):
        """Broadcast a message to all clients subscribed to a channel"""
        if channel_id not in self.channel_subscriptions:
            return
        
        ws_message = WebSocketMessage(
            type="channel_message",
            channel=channel_id,
            data=message
        )
        
        disconnected = []
        for client_id in self.channel_subscriptions[channel_id]:
            if client_id == exclude_client:
                continue
            
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(ws_message.dict())
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        ws_message = WebSocketMessage(
            type="broadcast",
            data=message
        )
        
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(ws_message.dict())
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def subscribe_to_channel(self, client_id: str, channel_id: str):
        """Subscribe a client to a channel"""
        if client_id not in self.active_connections:
            return
        
        # Add to channel subscriptions
        if channel_id not in self.channel_subscriptions:
            self.channel_subscriptions[channel_id] = set()
        self.channel_subscriptions[channel_id].add(client_id)
        
        # Add to client subscriptions
        self.client_subscriptions[client_id].add(channel_id)
        
        logger.info(f"Client {client_id} subscribed to channel {channel_id}")
        
        # Send confirmation
        await self.send_personal_message(
            client_id,
            {
                "type": "subscription_confirmed",
                "channel": channel_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def unsubscribe_from_channel(self, client_id: str, channel_id: str):
        """Unsubscribe a client from a channel"""
        if client_id not in self.active_connections:
            return
        
        # Remove from channel subscriptions
        if channel_id in self.channel_subscriptions:
            self.channel_subscriptions[channel_id].discard(client_id)
        
        # Remove from client subscriptions
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(channel_id)
        
        logger.info(f"Client {client_id} unsubscribed from channel {channel_id}")
        
        # Send confirmation
        await self.send_personal_message(
            client_id,
            {
                "type": "unsubscription_confirmed",
                "channel": channel_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def subscribe_to_minion(self, client_id: str, minion_id: str):
        """Subscribe a client to minion updates"""
        if client_id not in self.active_connections:
            return
        
        if minion_id not in self.minion_subscriptions:
            self.minion_subscriptions[minion_id] = set()
        self.minion_subscriptions[minion_id].add(client_id)
        
        logger.info(f"Client {client_id} subscribed to minion {minion_id}")
    
    async def broadcast_minion_update(self, minion_id: str, update_type: str, data: dict):
        """Broadcast updates about a specific minion"""
        if minion_id not in self.minion_subscriptions:
            return
        
        ws_message = WebSocketMessage(
            type="minion_update",
            data={
                "minion_id": minion_id,
                "update_type": update_type,
                **data
            }
        )
        
        disconnected = []
        for client_id in self.minion_subscriptions[minion_id]:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(ws_message.dict())
                except Exception as e:
                    logger.error(f"Error sending minion update to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def handle_command(self, client_id: str, command: WebSocketCommand):
        """Handle a command from a client"""
        try:
            if command.command == "ping":
                await self.send_personal_message(
                    client_id,
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            elif command.command == "subscribe_channel":
                channel_id = command.params.get("channel_id")
                if channel_id:
                    await self.subscribe_to_channel(client_id, channel_id)
            
            elif command.command == "unsubscribe_channel":
                channel_id = command.params.get("channel_id")
                if channel_id:
                    await self.unsubscribe_from_channel(client_id, channel_id)
            
            elif command.command == "subscribe_minion":
                minion_id = command.params.get("minion_id")
                if minion_id:
                    await self.subscribe_to_minion(client_id, minion_id)
            
            elif command.command == "get_subscriptions":
                await self.send_personal_message(
                    client_id,
                    {
                        "type": "subscriptions",
                        "channels": list(self.client_subscriptions.get(client_id, set())),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            else:
                logger.warning(f"Unknown command from {client_id}: {command.command}")
                await self.send_personal_message(
                    client_id,
                    {
                        "type": "error",
                        "message": f"Unknown command: {command.command}",
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        except Exception as e:
            logger.error(f"Error handling command from {client_id}: {e}")
            await self.send_personal_message(
                client_id,
                {
                    "type": "error",
                    "message": "Error processing command",
                    "timestamp": datetime.now().isoformat()
                }
            )


# Global connection manager instance
connection_manager = ConnectionManager()    
    async def broadcast_service_event(self, event_type: str, event_data: dict):
        """Broadcast a service event to all relevant clients"""
        try:
            # Handle different types of service events
            if event_type == "minion_spawned":
                await self.broadcast_to_all({
                    "type": "minion_event",
                    "event": "spawned",
                    "data": event_data
                })
            
            elif event_type == "minion_despawned":
                await self.broadcast_to_all({
                    "type": "minion_event",
                    "event": "despawned",
                    "data": event_data
                })
            
            elif event_type == "emotional_state_updated":
                minion_id = event_data.get("minion_id")
                if minion_id:
                    await self.broadcast_minion_update(
                        minion_id,
                        "emotional_state",
                        event_data
                    )
            
            elif event_type == "message_sent":
                channel_id = event_data.get("channel_id")
                if channel_id:
                    await self.broadcast_to_channel(
                        channel_id,
                        {
                            "type": "new_message",
                            "message": event_data
                        }
                    )
            
            elif event_type == "task_created":
                await self.broadcast_to_all({
                    "type": "task_event",
                    "event": "created",
                    "data": event_data
                })
            
            elif event_type == "task_assigned":
                minion_id = event_data.get("assigned_to")
                if minion_id:
                    await self.broadcast_minion_update(
                        minion_id,
                        "task_assigned",
                        event_data
                    )
            
            elif event_type == "task_completed":
                await self.broadcast_to_all({
                    "type": "task_event",
                    "event": "completed",
                    "data": event_data
                })
            
            elif event_type == "channel_created":
                await self.broadcast_to_all({
                    "type": "channel_event",
                    "event": "created",
                    "data": event_data
                })
            
            elif event_type == "channel_deleted":
                await self.broadcast_to_all({
                    "type": "channel_event",
                    "event": "deleted",
                    "data": event_data
                })
                
        except Exception as e:
            logger.error(f"Error broadcasting service event {event_type}: {e}")
    
    def setup_service_callbacks(self):
        """Set up callbacks so services can trigger broadcasts"""
        if not self.services:
            logger.warning("Cannot set up service callbacks - services not initialized")
            return
        
        # Set up event handlers for each service
        minion_service = self.services.get_minion_service()
        task_service = self.services.get_task_service()
        channel_service = self.services.get_channel_service()
        
        # Register callbacks (services would need to support this)
        # This is a placeholder for now - services would need event emitter support
        logger.info("Service callbacks configured for WebSocket broadcasting")