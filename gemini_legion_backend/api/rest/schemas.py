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


class ChannelTypeEnum(str, Enum):
    """Channel type classification"""
    PUBLIC = "public"
    PRIVATE = "private"
    DM = "dm" # Direct Message


class MessageTypeEnum(str, Enum):
    """Message types"""
    CHAT = "chat"
    SYSTEM = "system"
    TASK = "task"
    STATUS = "status"


class TaskStatusEnum(str, Enum):
    """Task status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    DECOMPOSED = "decomposed"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriorityEnum(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


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
    """Request for a minion to send a message to a channel."""
    # minion_id is implicitly part of the URL path: /api/minions/{minion_id}/send-message
    # However, the body validation was asking for 'sender'.
    # Let's align this. The sender *is* the minion_id from the path.
    # The service layer `minion_service.send_message(minion_id, channel, message)`
    # implies the endpoint should extract these.
    
    # Based on the 422 error for 'sender', and the endpoint trying to use 'request.channel' and 'request.message'
    # A consistent model would be:
    sender: str = Field(..., description="Sender ID (must match the minion_id in the URL path)")
    channel_id: str = Field(..., description="ID of the channel to send the message to")
    content: str = Field(..., min_length=1, max_length=4000, description="The message content")
    
    class Config:
        schema_extra = {
            "example": {
                "sender": "minion_abc123", # This would be the minion_id from the URL
                "channel_id": "general",
                "content": "Reporting for duty in #general!"
            }
        }


class RebootMinionRequest(BaseModel):
    """Request to reboot a minion"""
    hard_reset: bool = Field(default=False, description="Perform hard reset (clear emotional state)")


class CreateTaskRequest(BaseModel):
    """Request to create a new task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    priority: TaskPriorityEnum = Field(default=TaskPriorityEnum.NORMAL)
    assigned_to: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Analyze competitor products",
                "description": "Research and analyze top 5 competitor products in the market",
                "priority": "high",
                "assigned_to": "minion_abc123"
            }
        }


# --- Response Models ---

class MinionPersonaResponse(BaseModel):
    """Nested persona information for a Minion"""
    name: str
    base_personality: str
    quirks: List[str] = Field(default_factory=list)
    catchphrases: List[str] = Field(default_factory=list)
    expertise_areas: List[str] = Field(default_factory=list) # Aligned with domain
    allowed_tools: List[str] = Field(default_factory=list)   # Aligned with domain
    model_name: Optional[str] = "unknown" # Aligned with domain


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
    # name, personality, quirks, catchphrases, expertise are now in the nested persona object
    status: MinionStatusEnum
    emotional_state: EmotionalStateResponse
    persona: MinionPersonaResponse # Added nested persona
    creation_date: str


class ChannelResponse(BaseModel):
    """Channel information"""
    id: str
    name: str
    description: Optional[str] = None # Make description optional to match frontend type
    type: ChannelTypeEnum # Added channel type
    members: List[str]
    is_private: bool # Keep for now, can be used to derive type if domain model uses it
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


class TaskResponse(BaseModel):
    """Task information"""
    id: str
    title: str
    description: str
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    assigned_to: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    parent_id: Optional[str] = None
    subtasks: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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


class TasksListResponse(BaseModel):
    """List of tasks"""
    tasks: List[TaskResponse]
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
