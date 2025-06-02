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


class ChannelType(Enum):
    """Types of communication channels"""
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "dm"  # For direct messages


class ChannelRole(Enum):
    """Roles within a channel"""
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"


@dataclass
class ChannelMember:
    """Represents a member in a channel"""
    member_id: str
    role: ChannelRole = ChannelRole.MEMBER
    joined_at: datetime = field(default_factory=datetime.now)
    added_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
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
    parent_message_id: Optional[str] = None  # For threaded conversations
    
    # Additional fields for rich messaging
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> list of reactor IDs
    edited: bool = False
    edited_at: Optional[datetime] = None
    

@dataclass
class Channel:
    """Represents a communication channel"""
    channel_id: str
    name: str
    channel_type: ChannelType = ChannelType.PUBLIC
    description: str = ""
    members: List[ChannelMember] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    # Channel statistics
    member_count: int = 0
    message_count: int = 0
    last_activity: Optional[datetime] = None
    
    # Channel settings
    allow_minion_initiated: bool = True
    max_message_rate: int = 60  # messages per minute
    auto_archive_after_days: int = 30
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Soft delete fields
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
