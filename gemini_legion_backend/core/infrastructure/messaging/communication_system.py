"""
Inter-Minion Communication System

Handles multi-modal communication between Minions including
conversational, structured data exchange, and event-driven messaging.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CommunicationMode(Enum):
    """Modes of inter-Minion communication"""
    CONVERSATIONAL = "conversational"  # Natural language chat
    STRUCTURED = "structured"  # Structured data exchange
    EVENT = "event"  # Event notifications
    RPC = "rpc"  # Direct remote procedure calls


@dataclass
class TurnRequest:
    """Request to take a conversational turn"""
    minion_id: str
    channel_id: str
    urgency: float = 0.5  # 0.0 to 1.0
    estimated_length: int = 1  # Estimated messages


class TurnTakingEngine:
    """
    Manages conversational turn-taking to ensure natural flow
    
    Implements sophisticated turn-taking logic from AeroChat to prevent
    spam and ensure realistic multi-agent conversations.
    """
    
    def __init__(self):
        self.current_speakers: Dict[str, str] = {}  # channel_id -> minion_id
        self.turn_queue: Dict[str, List[TurnRequest]] = defaultdict(list)
        self.recent_speakers: Dict[str, List[tuple[str, datetime]]] = defaultdict(list)
        self.cooldown_seconds = 2.0
    
    async def request_turn(self, minion_id: str, channel_id: str, urgency: float = 0.5) -> bool:
        """
        Request permission to speak in a channel
        
        Returns:
            True if turn granted, False if should wait
        """
        # Check if someone else is currently speaking
        current_speaker = self.current_speakers.get(channel_id)
        if current_speaker and current_speaker != minion_id:
            # Add to queue
            request = TurnRequest(minion_id, channel_id, urgency)
            self.turn_queue[channel_id].append(request)
            return False
        
        # Check cooldown
        if not self._check_cooldown(minion_id, channel_id):
            return False
        
        # Grant turn
        self.current_speakers[channel_id] = minion_id
        self._record_speaker(minion_id, channel_id)
        return True
    
    def release_turn(self, minion_id: str, channel_id: str):
        """Release speaking turn in a channel"""
        if self.current_speakers.get(channel_id) == minion_id:
            del self.current_speakers[channel_id]
            
            # Process queue
            if self.turn_queue[channel_id]:
                # Sort by urgency
                self.turn_queue[channel_id].sort(key=lambda x: x.urgency, reverse=True)
                # Grant to next in line
                next_request = self.turn_queue[channel_id].pop(0)
                self.current_speakers[channel_id] = next_request.minion_id
    
    def _check_cooldown(self, minion_id: str, channel_id: str) -> bool:
        """Check if Minion has waited enough since last speaking"""
        recent = self.recent_speakers[channel_id]
        now = datetime.now()
        
        # Clean old entries
        self.recent_speakers[channel_id] = [
            (mid, ts) for mid, ts in recent 
            if (now - ts).total_seconds() < 60
        ]
        
        # Check cooldown
        for mid, ts in self.recent_speakers[channel_id]:
            if mid == minion_id and (now - ts).total_seconds() < self.cooldown_seconds:
                return False
        
        return True
    
    def _record_speaker(self, minion_id: str, channel_id: str):
        """Record that a Minion spoke"""
        self.recent_speakers[channel_id].append((minion_id, datetime.now()))


@dataclass
class ConversationalMessage:
    """Message for natural language communication"""
    sender: str
    channel: str
    content: str
    personality_hints: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MessageRouter:
    """Routes messages between Minions"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to messages on a channel"""
        self.subscribers[channel].append(callback)
    
    async def route(self, message: ConversationalMessage):
        """Route a message to all subscribers"""
        callbacks = self.subscribers.get(message.channel, [])
        
        # Notify all subscribers asynchronously
        tasks = [callback(message) for callback in callbacks]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class ConversationalLayer:
    """Natural language communication between Minions"""
    
    def __init__(self):
        self.turn_taking_engine = TurnTakingEngine()
        self.message_router = MessageRouter()
    
    async def send_message(
        self,
        from_minion: str,
        to_channel: str,
        message: str,
        personality_modifiers: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a conversational message with personality
        
        Returns:
            True if message sent, False if turn denied
        """
        # Apply turn-taking logic
        can_speak = await self.turn_taking_engine.request_turn(
            from_minion, to_channel
        )
        
        if not can_speak:
            # Could queue or wait
            return False
        
        try:
            # Route message
            msg = ConversationalMessage(
                sender=from_minion,
                channel=to_channel,
                content=message,
                personality_hints=personality_modifiers
            )
            await self.message_router.route(msg)
            
            return True
        finally:
            # Always release turn
            self.turn_taking_engine.release_turn(from_minion, to_channel)


class InterMinionCommunicationSystem:
    """
    Comprehensive inter-Minion communication framework
    
    Provides multiple layers of communication for different needs.
    """
    
    def __init__(self):
        # Layer 1: Conversational (AeroChat style)
        self.conversational_layer = ConversationalLayer()
        
        # Layer 2: Structured Data Exchange (simplified for now)
        self.data_exchange = {}  # Will implement MessageBus
        
        # Layer 3: Event-Driven Notifications
        self.event_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Layer 4: Direct RPC (for time-critical)
        self.rpc_handlers: Dict[str, Callable] = {}
    
    async def send_conversational_message(
        self,
        from_minion: str,
        to_channel: str,
        message: str,
        **kwargs
    ) -> bool:
        """Send a natural language message"""
        return await self.conversational_layer.send_message(
            from_minion, to_channel, message, **kwargs
        )
    
    def subscribe_to_channel(self, channel: str, callback: Callable):
        """Subscribe to messages on a channel"""
        self.conversational_layer.message_router.subscribe(channel, callback)

    # Methods required by ChannelService
    def create_channel(self, channel_id: str):
        """
        Recognize a new channel in the communication system.
        Currently, channels are implicitly handled by subscriptions in MessageRouter.
        """
        logger.debug(f"CommunicationSystem: Channel '{channel_id}' recognized/created.")
        # No specific action needed for MessageRouter if channels are implicit.

    def add_channel_member(self, channel_id: str, member_id: str):
        """
        Recognize a member being added to a channel.
        MessageRouter does not track members, only subscribers (callbacks).
        """
        logger.debug(f"CommunicationSystem: Member '{member_id}' noted for channel '{channel_id}'.")
        # No specific action needed for MessageRouter.

    def remove_channel_member(self, channel_id: str, member_id: str):
        """
        Recognize a member being removed from a channel.
        MessageRouter does not track members.
        """
        logger.debug(f"CommunicationSystem: Member '{member_id}' removal noted for channel '{channel_id}'.")
        # No specific action needed for MessageRouter.

    def delete_channel(self, channel_id: str):
        """
        Clean up a channel from the communication system, e.g., clear subscribers.
        """
        if channel_id in self.conversational_layer.message_router.subscribers:
            del self.conversational_layer.message_router.subscribers[channel_id]
            logger.info(f"CommunicationSystem: Cleared subscribers for deleted channel '{channel_id}'.")
        else:
            logger.debug(f"CommunicationSystem: No subscribers to clear for non-existent/inactive channel '{channel_id}'.")

    async def broadcast_message(
        self,
        channel_id: str,
        sender_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Broadcasts a message directly via the MessageRouter, bypassing turn-taking.
        Suitable for system messages or when turn-taking is handled externally.
        """
        logger.debug(f"CommunicationSystem: Broadcasting message from '{sender_id}' to channel '{channel_id}'.")
        msg = ConversationalMessage(
            sender=sender_id,
            channel=channel_id,
            content=content,
            personality_hints=metadata if metadata else {} # Or map specific metadata keys
        )
        await self.conversational_layer.message_router.route(msg)
    
    async def emit_event(self, event_type: str, data: Any):
        """Emit an event to all subscribers"""
        callbacks = self.event_subscribers.get(event_type, [])
        tasks = [callback(data) for callback in callbacks]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe_to_event(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        self.event_subscribers[event_type].append(callback)
