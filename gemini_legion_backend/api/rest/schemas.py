"""
API Request/Response Schemas

Pydantic models for API validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal # Added Union, Literal
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


class UpdateMinionPersonaRequest(BaseModel):
    """Request to update a minion's persona details"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    base_personality: Optional[str] = Field(default=None, min_length=1, max_length=200)
    quirks: Optional[List[str]] = Field(default=None, max_items=10)
    catchphrases: Optional[List[str]] = Field(default=None, max_items=5)
    expertise_areas: Optional[List[str]] = Field(default=None, max_items=10)
    allowed_tools: Optional[List[str]] = Field(default=None)
    model_name: Optional[str] = Field(default=None)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)

    class Config:
        schema_extra = {
            "example": {
                "name": "ByteCrusher v2",
                "base_personality": "Slightly less grumpy, but still brilliant hacker.",
                "model_name": "gemini-1.5-pro-latest",
                "temperature": 0.8
            }
        }

class AddMemberRequest(BaseModel):
    """Request to add a member (minion) to a channel."""
    minion_id: str = Field(..., description="The ID of the minion to add to the channel.")

    class Config:
        schema_extra = {
            "example": {
                "minion_id": "minion_xyz789"
            }
        }

# Moved MoodVectorResponse earlier to resolve NameError
class MoodVectorResponse(BaseModel):
    """Mood vector representation"""
    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=0.0, le=1.0)
    dominance: float = Field(..., ge=0.0, le=1.0)
    curiosity: float = Field(..., ge=0.0, le=1.0)
    creativity: float = Field(..., ge=0.0, le=1.0)
    sociability: float = Field(..., ge=0.0, le=1.0)

class UpdateEmotionalStateRequest(BaseModel):
    """Request to update specific parts of a minion's emotional state."""
    mood: Optional[MoodVectorResponse] = Field(default=None, description="Full new mood vector or specific deltas for mood.")
    energy_level: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="New energy level (0.0 to 1.0).")
    stress_level: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="New stress level (0.0 to 1.0).")
    # opinion_updates could be Dict[entity_id, Partial[OpinionScoreResponse]]
    # For a more robust API, define a specific OpinionScoreUpdateRequest.
    # For now, allowing flexible Dict for partial updates to existing OpinionScores by entity_id.
    opinion_updates: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="Updates to opinion scores for specific entities, e.g., {'entity_id_1': {'trust': 10.5}}.")
    # new_reflection: Optional[ReflectionEntryRequest] # Placeholder if we add a request model for ReflectionEntry

    class Config:
        schema_extra = {
            "example": {
                "mood": {"valence": 0.6, "arousal": 0.7, "dominance": 0.5, "curiosity": 0.8, "creativity": 0.7, "sociability": 0.7},
                "energy_level": 0.85,
                "stress_level": 0.1,
                "opinion_updates": {
                    "user_commander_steven": {"trust": 10.0, "affection": 5.0}, # Example: Increase trust and affection for commander
                    "minion_bob": {"respect": -2.0} # Example: Decrease respect for minion_bob
                }
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
    model_name: Optional[str] = "unknown", # Aligned with domain
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0),
    max_tokens: Optional[int] = Field(default=4096, gt=0)


# MoodVectorResponse was moved before UpdateEmotionalStateRequest


class EntityTypeEnum(str, Enum):
    """Type of entity an opinion is about, mirroring frontend and ideal architecture."""
    USER = "USER"
    MINION = "MINION"
    CONCEPT = "CONCEPT"
    TASK = "TASK"
    UNKNOWN = "UNKNOWN" # Fallback

class OpinionEventResponse(BaseModel):
    """A notable event influencing an opinion score."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the event.")
    description: str = Field(..., description="Description of the notable event.")
    timestamp: datetime = Field(..., description="Timestamp of when the event occurred.")
    impact_on_trust: Optional[float] = Field(default=None, description="Perceived impact on trust score.")
    impact_on_respect: Optional[float] = Field(default=None, description="Perceived impact on respect score.")
    impact_on_affection: Optional[float] = Field(default=None, description="Perceived impact on affection score.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Any additional metadata about the event.")

class OpinionScoreResponse(BaseModel):
    """
    Comprehensive opinion score for an entity, aligned with Ideal Architecture and frontend types.
    The 'entity_id' will be the key in the Dict within EmotionalStateResponse.
    """
    entity_type: EntityTypeEnum = Field(..., description="Type of the entity this opinion is about.")
    trust: float = Field(..., ge=-100.0, le=100.0, description="Trust score towards the entity.")
    respect: float = Field(..., ge=-100.0, le=100.0, description="Respect score towards the entity.")
    affection: float = Field(..., ge=-100.0, le=100.0, description="Affection score towards the entity.")
    interaction_count: int = Field(default=0, ge=0, description="Number of interactions with the entity.")
    last_interaction_timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the last interaction with the entity.")
    notable_events: List[OpinionEventResponse] = Field(default_factory=list, description="List of notable events influencing this opinion.")
    overall_sentiment: float = Field(..., ge=-100.0, le=100.0, description="Overall sentiment score, computed by the backend based on trust, respect, and affection.")
    # Additional fields for future depth, if needed from Ideal Spec or discovered
    # e.g., specific positive_interactions_count, negative_interactions_count, etc.

class EmotionalStateResponse(BaseModel):
    """Emotional state snapshot"""
    minion_id: str
    mood: MoodVectorResponse
    energy_level: float = Field(..., ge=0.0, le=1.0)
    stress_level: float = Field(..., ge=0.0, le=1.0)
    opinion_scores: Dict[str, OpinionScoreResponse]
    last_updated: str
    state_version: int

# --- Memory System Schemas ---

class BaseMemoryEntryContents(BaseModel):
    """Base content structure for different memory types, can be extended."""
    content: str = Field(..., description="The textual content of the memory.")

class WorkingMemoryEntryDetails(BaseMemoryEntryContents):
    """Specific details for a working memory entry."""
    significance: Optional[float] = Field(default=None, description="Significance score of the working memory item.")
    emotional_impact: Optional[float] = Field(default=None, description="Emotional impact score.")

class EpisodicMemoryEntryDetails(BaseMemoryEntryContents):
    """Specific details for an episodic memory entry."""
    context: Optional[Dict[str, Any]] = Field(default=None, description="Contextual information about the episode.")
    emotional_state_snapshot_data: Optional[Dict[str, Any]] = Field(default=None, description="Raw dictionary data of emotional state during the episode.")
    actors: Optional[List[str]] = Field(default_factory=list, description="Entities involved in the episode.")
    location: Optional[str] = Field(default=None, description="Location where the episode occurred.")

class SemanticMemoryEntryDetails(BaseMemoryEntryContents):
    """Specific details for a semantic memory entry (knowledge graph concept)."""
    concept_id: str = Field(..., description="Unique ID of the concept.")
    relations: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Relationships to other concepts (e.g., [{'type': 'is_a', 'target_id': 'entity_X'}]).")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Properties of the concept.")
    confidence: Optional[float] = Field(default=None, description="Confidence score of this semantic knowledge.")

class ProceduralMemoryEntryDetails(BaseMemoryEntryContents):
    """Specific details for a procedural memory entry (skill/pattern)."""
    skill_name: str = Field(..., description="Name of the learned skill or pattern.")
    trigger_conditions: Optional[List[str]] = Field(default_factory=list, description="Conditions that trigger this procedure.")
    action_sequence: Optional[List[str]] = Field(default_factory=list, description="Sequence of actions for this procedure.")
    effectiveness_score: Optional[float] = Field(default=None, description="Effectiveness of this procedure.")

class WorkingMemoryEntryResponse(BaseModel):
    memory_type: Literal["working"] = "working"
    memory_id: str = Field(..., description="Unique ID of the memory entry.")
    minion_id: str = Field(..., description="ID of the Minion this memory belongs to.")
    timestamp: datetime = Field(..., description="Timestamp of when the memory was recorded or last accessed.")
    details: WorkingMemoryEntryDetails

class EpisodicMemoryEntryResponse(BaseModel):
    memory_type: Literal["episodic"] = "episodic"
    memory_id: str = Field(..., description="Unique ID of the memory entry.")
    minion_id: str = Field(..., description="ID of the Minion this memory belongs to.")
    timestamp: datetime = Field(..., description="Timestamp of when the memory was recorded.")
    details: EpisodicMemoryEntryDetails

class SemanticMemoryEntryResponse(BaseModel):
    memory_type: Literal["semantic"] = "semantic"
    memory_id: str = Field(..., description="Unique ID of the memory entry (could be concept ID).")
    minion_id: str = Field(..., description="ID of the Minion this memory belongs to.")
    timestamp: datetime = Field(..., description="Timestamp of when the knowledge was learned or last updated.")
    details: SemanticMemoryEntryDetails

class ProceduralMemoryEntryResponse(BaseModel):
    memory_type: Literal["procedural"] = "procedural"
    memory_id: str = Field(..., description="Unique ID of the memory entry (could be skill ID).")
    minion_id: str = Field(..., description="ID of the Minion this memory belongs to.")
    timestamp: datetime = Field(..., description="Timestamp of when the procedure was learned or last modified.")
    details: ProceduralMemoryEntryDetails

AnyMemoryEntryResponse = Union[
    WorkingMemoryEntryResponse,
    EpisodicMemoryEntryResponse,
    SemanticMemoryEntryResponse,
    ProceduralMemoryEntryResponse,
]

class MemoryListResponse(BaseModel):
    """List of memory entries for a minion."""
    memories: List[AnyMemoryEntryResponse] = Field(..., description="A list of memory entries of various types.")
    minion_id: str = Field(..., description="ID of the Minion these memories belong to.")
    memory_type_filter: Optional[str] = Field(default=None, description="The type of memory requested, if filtered.")
    total_returned: int = Field(..., description="Number of memory entries returned in this response.")

# --- End Memory System Schemas ---

class MinionResponse(BaseModel):
    """Minion information"""
    minion_id: str # Changed from id to minion_id
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
    type: ChannelTypeEnum
    members: List[str]
    # is_private is now derived into 'type', so it's removed from response.
    created_at: Optional[str] = None


class MessageResponse(BaseModel):
    """Message information"""
    message_id: str # Changed from id to message_id
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
    task_id: str # Changed from id to task_id
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
