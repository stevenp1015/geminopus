"""
Communication Capability for ADK Minions

This module provides ADK tools for Minions to interact with the
communication infrastructure, enabling them to send and receive
messages, participate in channels, and trigger autonomous communication.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

from google.adk.tools import BaseTool
from google.adk.agents import LlmAgent

from ....infrastructure.messaging.communication_system import (
    InterMinionCommunicationSystem,
    ConversationalMessage
)
from ....infrastructure.messaging.autonomous_messaging import (
    AutonomousMessagingEngine,
    AutonomousContext,
    AutonomousMessage
)
from ....infrastructure.messaging.safeguards import CommunicationSafeguards
from ....domain import Minion, EmotionalState


class MessagePriority(Enum):
    """Priority levels for messages"""
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class IncomingMessage:
    """Represents a message received by a Minion"""
    sender: str
    channel: str
    content: str
    timestamp: datetime
    priority: MessagePriority = MessagePriority.NORMAL


class SendMessageTool(BaseTool):
    """
    ADK Tool for sending messages to channels
    
    This tool wraps the communication system's send functionality
    with turn-taking, safeguards, and personality injection.
    """
    
    name = "send_message"
    description = "Send a message to a specific channel or Minion"
    
    def __init__(
        self,
        minion_id: str,
        comm_system: InterMinionCommunicationSystem,
        safeguards: CommunicationSafeguards,
        personality_hints: Optional[Dict[str, Any]] = None
    ):
        self.minion_id = minion_id
        self.comm_system = comm_system
        self.safeguards = safeguards
        self.personality_hints = personality_hints or {}
        super().__init__(name=self.name, description=self.description)
    
    async def execute(
        self,
        channel: str,
        message: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Send a message to a channel
        
        Args:
            channel: Target channel (e.g., "#general", "@minion_name")
            message: Message content
            priority: Message priority (low, normal, high, urgent)
            
        Returns:
            Result of the send operation
        """
        # Check safeguards first
        allowed, reason = await self.safeguards.check_message_allowed(
            self.minion_id, channel, message
        )
        
        if not allowed:
            return {
                "success": False,
                "reason": reason,
                "suggestion": "Wait a moment before sending or vary your message"
            }
        
        # Apply personality hints
        personality_modifiers = self._calculate_personality_modifiers(priority)
        
        # Send through communication system
        sent = await self.comm_system.send_conversational_message(
            from_minion=self.minion_id,
            to_channel=channel,
            message=message,
            personality_modifiers=personality_modifiers
        )
        
        if sent:
            return {
                "success": True,
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "reason": "Turn denied - another Minion is speaking",
                "suggestion": "Wait for your turn or increase priority"
            }
    
    def _calculate_personality_modifiers(self, priority: str) -> Dict[str, Any]:
        """Calculate personality modifiers based on context"""
        modifiers = self.personality_hints.copy()
        
        # Add urgency based on priority
        if priority == "urgent":
            modifiers["urgency"] = 1.0
            modifiers["formality"] = 0.7
        elif priority == "high":
            modifiers["urgency"] = 0.7
        
        return modifiers


class SubscribeChannelTool(BaseTool):
    """
    ADK Tool for subscribing to channels
    
    Allows Minions to listen to specific channels and receive messages.
    """
    
    name = "subscribe_channel"
    description = "Subscribe to receive messages from a channel"
    
    def __init__(
        self,
        minion_id: str,
        comm_system: InterMinionCommunicationSystem,
        message_handler: Callable[[IncomingMessage], None]
    ):
        self.minion_id = minion_id
        self.comm_system = comm_system
        self.message_handler = message_handler
        self.subscriptions: Dict[str, bool] = {}
        super().__init__(name=self.name, description=self.description)
    
    async def execute(self, channel: str) -> Dict[str, Any]:
        """
        Subscribe to a channel
        
        Args:
            channel: Channel to subscribe to
            
        Returns:
            Subscription result
        """
        if channel in self.subscriptions:
            return {
                "success": False,
                "reason": "Already subscribed to this channel"
            }
        
        # Create callback wrapper
        async def channel_callback(message: ConversationalMessage):
            # Filter out own messages
            if message.sender == self.minion_id:
                return
            
            # Convert to IncomingMessage
            incoming = IncomingMessage(
                sender=message.sender,
                channel=message.channel,
                content=message.content,
                timestamp=message.timestamp,
                priority=self._assess_priority(message)
            )
            
            # Call handler
            await self.message_handler(incoming)
        
        # Subscribe through communication system
        self.comm_system.subscribe_to_channel(channel, channel_callback)
        self.subscriptions[channel] = True
        
        return {
            "success": True,
            "channel": channel,
            "active_subscriptions": list(self.subscriptions.keys())
        }
    
    def _assess_priority(self, message: ConversationalMessage) -> MessagePriority:
        """Assess the priority of an incoming message"""
        content_lower = message.content.lower()
        
        # Check for urgency indicators
        if any(word in content_lower for word in ["urgent", "asap", "immediately", "critical"]):
            return MessagePriority.URGENT
        elif any(word in content_lower for word in ["important", "priority", "need"]):
            return MessagePriority.HIGH
        elif any(word in content_lower for word in ["fyi", "casual", "chat"]):
            return MessagePriority.LOW
        
        return MessagePriority.NORMAL


class AutonomousCommunicationTool(BaseTool):
    """
    ADK Tool for autonomous communication decisions
    
    This tool allows Minions to check if they should initiate
    communication based on their state and context.
    """
    
    name = "consider_autonomous_communication"
    description = "Analyze if autonomous communication is appropriate"
    
    def __init__(
        self,
        minion: Minion,
        autonomous_engine: AutonomousMessagingEngine,
        comm_system: InterMinionCommunicationSystem
    ):
        self.minion = minion
        self.autonomous_engine = autonomous_engine
        self.comm_system = comm_system
        super().__init__(name=self.name, description=self.description)
    
    async def execute(
        self,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Consider whether to initiate autonomous communication
        
        Args:
            context_data: Optional context information
            
        Returns:
            Decision result and suggested action
        """
        # Build autonomous context
        context = await self._build_autonomous_context(context_data)
        
        # Let the engine decide
        autonomous_message = await self.autonomous_engine.consider_autonomous_message(
            self.minion, context
        )
        
        if autonomous_message:
            # Initiate the communication
            sent = await self.comm_system.send_conversational_message(
                from_minion=autonomous_message.initiator,
                to_channel=f"#{autonomous_message.recipients[0]}" if autonomous_message.recipients else "#general",
                message=autonomous_message.initial_message
            )
            
            return {
                "should_communicate": True,
                "action_taken": "message_sent" if sent else "message_queued",
                "purpose": autonomous_message.purpose.value,
                "recipients": autonomous_message.recipients,
                "message": autonomous_message.initial_message
            }
        else:
            return {
                "should_communicate": False,
                "reason": "No immediate communication need detected"
            }
    
    async def _build_autonomous_context(
        self,
        context_data: Optional[Dict[str, Any]]
    ) -> AutonomousContext:
        """Build context for autonomous decision making"""
        # Default context
        now = datetime.now()
        default_context = AutonomousContext(
            current_time=now,
            active_tasks=[],
            recent_interactions=[],
            channel_activity={},
            other_minions_status={}
        )
        
        if not context_data:
            return default_context
        
        # Override with provided data
        if "active_tasks" in context_data:
            default_context.active_tasks = context_data["active_tasks"]
        if "recent_interactions" in context_data:
            default_context.recent_interactions = context_data["recent_interactions"]
        
        return default_context


class CommunicationCapability:
    """
    Communication capability suite for Minions
    
    Provides a complete set of communication tools that can be
    added to a MinionAgent to enable rich inter-Minion communication.
    """
    
    def __init__(
        self,
        minion: Minion,
        comm_system: InterMinionCommunicationSystem,
        safeguards: CommunicationSafeguards
    ):
        self.minion = minion
        self.comm_system = comm_system
        self.safeguards = safeguards
        self.autonomous_engine = AutonomousMessagingEngine(comm_system)
        
        # Message queue for incoming messages
        self.message_queue: asyncio.Queue[IncomingMessage] = asyncio.Queue()
        
        # Create tools
        self.send_tool = SendMessageTool(
            minion.minion_id,
            comm_system,
            safeguards,
            self._extract_personality_hints()
        )
        
        self.subscribe_tool = SubscribeChannelTool(
            minion.minion_id,
            comm_system,
            self._handle_incoming_message
        )
        
        self.autonomous_tool = AutonomousCommunicationTool(
            minion,
            self.autonomous_engine,
            comm_system
        )
    
    def get_tools(self) -> List[BaseTool]:
        """Get all communication tools"""
        return [
            self.send_tool,
            self.subscribe_tool,
            self.autonomous_tool
        ]
    
    async def _handle_incoming_message(self, message: IncomingMessage):
        """Handle incoming messages by queueing them"""
        await self.message_queue.put(message)
    
    def _extract_personality_hints(self) -> Dict[str, Any]:
        """Extract personality hints from Minion's persona"""
        hints = {
            "personality": self.minion.persona.base_personality,
            "formality": 0.5,  # Default medium formality
            "verbosity": 0.6,  # Slightly verbose (exhaustive)
            "emotion_expression": 0.7  # High emotional expression
        }
        
        # Adjust based on quirks
        if any("formal" in quirk.lower() for quirk in self.minion.persona.quirks):
            hints["formality"] = 0.8
        if any("brief" in quirk.lower() or "concise" in quirk.lower() for quirk in self.minion.persona.quirks):
            hints["verbosity"] = 0.3
        
        return hints
    
    async def process_message_queue(self, agent: LlmAgent) -> List[str]:
        """
        Process queued messages and generate responses
        
        This method should be called periodically by the agent to handle
        incoming messages.
        
        Args:
            agent: The LlmAgent to use for generating responses
            
        Returns:
            List of responses generated
        """
        responses = []
        
        # Process up to 5 messages at a time
        for _ in range(5):
            try:
                message = self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            
            # Generate response using the agent
            prompt = self._format_message_for_agent(message)
            response = await agent.think(prompt)
            
            # Send response if appropriate
            if response and not response.lower().startswith("[no response]"):
                await self.send_tool.execute(
                    channel=message.channel,
                    message=response,
                    priority=message.priority.value
                )
                responses.append(response)
        
        return responses
    
    def _format_message_for_agent(self, message: IncomingMessage) -> str:
        """Format an incoming message as a prompt for the agent"""
        priority_context = ""
        if message.priority == MessagePriority.URGENT:
            priority_context = " [URGENT MESSAGE]"
        elif message.priority == MessagePriority.HIGH:
            priority_context = " [HIGH PRIORITY]"
        
        return (
            f"You received a message{priority_context}:\n"
            f"From: {message.sender}\n"
            f"Channel: {message.channel}\n"
            f"Message: {message.content}\n\n"
            f"How do you respond? (Reply with '[No response]' if you choose not to respond)"
        )
