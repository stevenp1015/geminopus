"""
API Request/Response Schemas

Pydantic models for API validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# --- Enums ---

class MinionStatusEnum(str, Enum):
    """Minion operational status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    REBOOTING = "rebooting"


class MessageTypeEnum(str, Enum):
    """Message types"""
    CHAT = "chat"
    SYSTEM = "system"
    TASK = "task"
    STATUS = "status"


# --- Request Models ---

class CreateMinionRequest(BaseModel):
    """Request to create a new minion"""
    name: str = Field(..., min_length=1, max_length=50)
    personality: str = Field(..., min_length=1, max_length=200)
    quirks: List[str] = Field(default_factory=list, max_items=10)
    catchphrases: List[str] = Field(default_factory=list, max_items=5)
    expertise: List[str] = Field(default_factory=list, max_items=10)
    tools: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "ByteCrusher",
                "personality": "Grumpy but brilliant hacker who secretly cares",
                "quirks": ["Complains about inefficient code", "References obscure Unix commands"],
                "catchphrases": ["BY ANY MEANS NECESSARY", "This is suboptimal but..."],
                "expertise": ["Python", "System Architecture", "Security"],
                "tools": ["file_system", "code_execution"]
            }
        }


class CreateChannelRequest(BaseModel):
    """Request to create a new channel"""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    members: List[str] = Field(default_factory=list)
    is_private: bool = Field(default=False)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "project-alpha",
                "description": "Coordination for Project Alpha",
                "members": ["minion_abc123", "minion_def456"],
                "is_private": False
            }
        }


class SendMessageRequest(BaseModel):
    """Request to send a message"""
    sender: str = Field(..., description="Sender ID (commander or minion_id)")
    content: str = Field(..., min_length=1, max_length=4000)
    
    class Config:
        schema_extra = {
            "example": {
                "sender": "commander",
                "content": "Great work on the analysis, team! What's our next priority?"
            }
        }


class RebootMinionRequest(BaseModel):
    """Request to reboot a minion"""
    hard_reset: bool = Field(default=False, description="Perform hard reset (clear emotional state)")


# --- Response Models ---

class MoodVectorResponse(BaseModel):
    """Mood vector representation"""
    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=0.0, le=1.0)
    dominance: float = Field(..., ge=0.0, le=1.0)
    curiosity: float = Field(..., ge=0.0, le=1.0)
    creativity: float = Field(..., ge=0.0, le=1.0)
    sociability: float = Field(..., ge=0.0, le=1.0)


class OpinionScoreResponse(BaseModel):
    """Opinion score for an entity"""
    trust: float = Field(..., ge=-100.0, le=100.0)
    respect: float = Field(..., ge=-100.0, le=100.0)
    affection: float = Field(..., ge=-100.0, le=100.0)
    overall_sentiment: float = Field(..., ge=-100.0, le=100.0)


class EmotionalStateResponse(BaseModel):
    """Emotional state snapshot"""
    minion_id: str
    mood: MoodVectorResponse
    energy_level: float = Field(..., ge=0.0, le=1.0)
    stress_level: float = Field(..., ge=0.0, le=1.0)
    opinion_scores: Dict[str, OpinionScoreResponse]
    last_updated: str
    state_version: int


class MinionResponse(BaseModel):
    """Minion information"""
    id: str
    name: str
    personality: str
    status: MinionStatusEnum
    emotional_state: EmotionalStateResponse
    quirks: List[str] = Field(default_factory=list)
    catchphrases: List[str] = Field(default_factory=list)
    expertise: List[str] = Field(default_factory=list)


class ChannelResponse(BaseModel):
    """Channel information"""
    id: str
    name: str
    description: str
    members: List[str]
    is_private: bool
    created_at: Optional[str] = None


class MessageResponse(BaseModel):
    """Message information"""
    id: str
    sender: str
    content: str
    timestamp: str
    type: MessageTypeEnum
    channel_id: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    minion_count: int
    active_channels: int


class OperationResponse(BaseModel):
    """Generic operation response"""
    status: str
    id: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None


# --- List Response Models ---

class MinionsListResponse(BaseModel):
    """List of minions"""
    minions: List[MinionResponse]
    total: Optional[int] = None


class ChannelsListResponse(BaseModel):
    """List of channels"""
    channels: List[ChannelResponse]
    total: Optional[int] = None


class MessagesListResponse(BaseModel):
    """List of messages"""
    messages: List[MessageResponse]
    total: Optional[int] = None
    has_more: bool = False


# --- WebSocket Models ---

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type (new_message, status_update, etc.)")
    channel: Optional[str] = None
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebSocketCommand(BaseModel):
    """WebSocket command from client"""
    command: str = Field(..., description="Command type")
    params: Optional[Dict[str, Any]] = None
