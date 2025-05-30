"""
Communication Domain Models

Handles channels, messages, and inter-agent communication protocols.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class MessageType(Enum):
    """Types of messages in the system"""
    CHAT = "chat"
    SYSTEM = "system"
    TASK = "task"
    REFLECTION = "reflection"
    STATUS = "status"


@dataclass
class Message:
    """Represents a message in the communication system"""
    message_id: str
    channel_id: str
    sender_id: str  # "commander" or minion_id
    content: str
    message_type: MessageType = MessageType.CHAT
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None  # For threaded conversations
    

@dataclass
class Channel:
    """Represents a communication channel"""
    channel_id: str
    name: str
    description: str = ""
    members: List[str] = field(default_factory=list)
    is_private: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    # Channel settings
    allow_minion_initiated: bool = True
    max_message_rate: int = 60  # messages per minute
    auto_archive_after_days: int = 30
