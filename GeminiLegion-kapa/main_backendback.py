# main_backend.py
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
import logging

from config import settings
from minion_core import MinionAgent

# Configure logging for main_backend
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gemini Legion C&C Backend",
    description="The Python ADK-powered backend for managing the Legion of AI Minions.",
    version="0.1.1" # Incremented version
)

# --- Data Models (Pydantic) ---
# These should mirror the TypeScript types for API consistency

class MinionParams(BaseModel):
    temperature: float = Field(default=0.7, ge=0, le=1.0) # Max 1.0 for Gemini

class MinionConfigPayload(BaseModel): # For POST/PUT requests
    id: Optional[str] = None
    name: str
    # provider: str = "google" # This is implicit by using this backend
    model_id: str
    system_prompt_persona: str # This is the 'persona_prompt' for MinionAgent
    params: MinionParams = Field(default_factory=MinionParams)
    # opinionScores are managed internally by MinionAgent instances
    status: Optional[str] = "Idle"
    currentTask: Optional[str] = None

class MinionConfigResponse(BaseModel): # For GET responses
    id: str
    name: str
    provider: str = "google" # Constant for this backend
    model_id: str
    system_prompt_persona: str
    params: MinionParams
    opinionScores: Dict[str, int] = {}
    status: str
    currentTask: Optional[str] = None

    @field_validator('id', mode='before')
    @classmethod
    def ensure_id_is_string(cls, value): # Ensure ID is always string, even if UUID obj
        return str(value)


class ChannelPayload(BaseModel): # For POST/PUT requests
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    type: str = Field(default="user_minion_group", pattern="^(user_minion_group|user_minion_dm|minion_minion_group|system_log)$")
    members: Optional[List[str]] = Field(default_factory=list) # List of Minion names or User name
    isPrivate: Optional[bool] = False

class ChannelResponse(ChannelPayload): # For GET responses
    id: str
    
    @field_validator('id', mode='before')
    @classmethod
    def ensure_id_is_string_ch(cls, value):
        return str(value)


class MessageSenderType(BaseModel): # Equivalent to enum MessageSender
    User: str = "User"
    AI: str = "AI"
    System: str = "System"

SENDER_TYPE = MessageSenderType()

class ChatMessageBase(BaseModel):
    channelId: str
    senderType: str # "User", "AI", "System"
    senderName: str
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    internalDiary: Optional[str] = None
    isError: Optional[bool] = False
    replyToMessageId: Optional[str] = None

class ChatMessageResponse(ChatMessageBase): # For GET responses
    id: str

    @field_validator('id', mode='before')
    @classmethod
    def ensure_id_is_string_msg(cls, value):
        return str(value)


class UserMessageToChannel(BaseModel): # Payload from Frontend for new message
    channelId: str
    userInput: str # Renamed from 'content' to distinguish from ChatMessageData.content
    # current_messages_for_context: Optional[List[ChatMessageBase]] = None # Frontend might send this if context window is small

# --- In-memory storage (temporary - will be replaced by DB/ADK services) ---
# MinionAgent instances, not just configs
minion_agents: Dict[str, MinionAgent] = {}

# Channel data
channels_db: Dict[str, ChannelResponse] = {}

# Messages, keyed by channel_id
messages_db: Dict[str, List[ChatMessageResponse]] = {}


# --- Initialization ---
def initialize_default_data():
    global channels_db, messages_db, minion_agents

    logger.info("Initializing default backend data...")
    
    # Default Channels
    default_channels_data = [
        {"id": "general", "name": "#general", "description": "General discussion with all Minions.", "type": "user_minion_group", "members": [settings.LEGION_COMMANDER_NAME]},
        {"id": "random", "name": "#random_bullshit", "description": "Off-topic banter and delightful chaos.", "type": "user_minion_group", "members": [settings.LEGION_COMMANDER_NAME]},
        {"id": "legion_ops_log", "name": "#legion_ops_log", "description": "Automated Legion operational logs.", "type": "system_log", "members": []},
    ]
    for ch_data in default_channels_data:
        ch_id = ch_data["id"]
        channels_db[ch_id] = ChannelResponse(**ch_data) #type: ignore
        if ch_id not in messages_db:
            messages_db[ch_id] = []

    if "legion_ops_log" in messages_db and not messages_db["legion_ops_log"]:
         messages_db["legion_ops_log"].append(ChatMessageResponse(
            id=str(uuid.uuid4()), channelId="legion_ops_log", senderType=SENDER_TYPE.System,
            senderName="LegionOS", content="Legion Command Interface Backend Initialized.",
            timestamp=datetime.now(timezone.utc).timestamp()
        ))

    # Default Minion (for testing, if none exist)
    if not minion_agents:
        logger.info("No Minions found. Initializing a default 'Alpha' Minion...")
        alpha_config_payload = MinionConfigPayload(
            id="alpha-default", # Specify ID for predictability in testing
            name="Alpha",
            model_id="gemini-2.5-flash-preview-04-17",
            system_prompt_persona="You are Alpha, a highly efficient and slightly sarcastic Minion. You get things done with precision and a witty remark. You secretly enjoy puns.",
            params=MinionParams(temperature=0.7)
        )
        try:
            alpha_agent = MinionAgent(
                minion_id=alpha_config_payload.id, # type: ignore
                name=alpha_config_payload.name,
                model_id=alpha_config_payload.model_id,
                persona_prompt=alpha_config_payload.system_prompt_persona,
                temperature=alpha_config_payload.params.temperature
            )
            minion_agents[alpha_agent.minion_id] = alpha_agent
            
            # Add Alpha to general channel members
            if "general" in channels_db and channels_db["general"].members:
                if "Alpha" not in channels_db["general"].members: # type: ignore
                     channels_db["general"].members.append("Alpha") # type: ignore
            logger.info(f"Default Minion '{alpha_agent.name}' initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize default Minion Alpha: {e}")

    logger.info("Default data initialization complete.")
    logger.info(f"Channels loaded: {list(channels_db.keys())}")
    logger.info(f"Minions loaded: {list(minion_agents.keys())}")


@app.on_event("startup")
async def startup_event():
    initialize_default_data()

# --- Helper Functions ---
def get_channel_history_string(channel_id: str, max_messages: int = 20) -> str:
    channel_messages = messages_db.get(channel_id, [])
    history_slice = channel_messages[-max_messages:] # Get the most recent N messages
    lines = []
    for msg in history_slice:
        prefix = f"[{msg.senderName}]"
        if msg.senderType == SENDER_TYPE.User:
            prefix = f"[COMMANDER {msg.senderName}]"
        elif msg.senderType == SENDER_TYPE.AI:
             prefix = f"[MINION {msg.senderName}]"
        lines.append(f"{prefix}: {msg.content}")
    if not lines:
        return f"This is the beginning of the conversation in channel {channels_db.get(channel_id, ChannelResponse(id=channel_id, name='Unknown', description=None)).name}."
    return "\n".join(lines)

# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": f"Welcome to the Gemini Legion C&C Backend, Commander {settings.LEGION_COMMANDER_NAME}!",
