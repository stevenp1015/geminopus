"""
Channel-related API endpoints

Handles channel creation, management, and messaging.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from ..schemas import (
    CreateChannelRequest,
    SendMessageRequest,
    ChannelResponse,
    ChannelsListResponse,
    MessageResponse,
    MessagesListResponse,
    OperationResponse,
    MessageTypeEnum
)
from ....core.domain import Channel, Message, MessageType
from ....core.infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from ....core.infrastructure.messaging.safeguards import CommunicationSafeguards

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/channels", tags=["channels"])


# In-memory storage (would be replaced with proper persistence)
channels_store: Dict[str, Channel] = {}
messages_store: Dict[str, List[Message]] = {}


# Dependency injection
def get_comm_system() -> InterMinionCommunicationSystem:
    """Get the communication system instance"""
    if not hasattr(get_comm_system, "_instance"):
        get_comm_system._instance = InterMinionCommunicationSystem()
    return get_comm_system._instance


def get_safeguards() -> CommunicationSafeguards:
    """Get the safeguards instance"""
    if not hasattr(get_safeguards, "_instance"):
        get_safeguards._instance = CommunicationSafeguards()
    return get_safeguards._instance


# Initialize default channels
def init_default_channels():
    """Initialize default channels"""
    if not channels_store:
        channels_store["general"] = Channel(
            channel_id="general",
            name="General",
            description="Main communication channel for the Legion",
            members=[],
            is_private=False
        )
        messages_store["general"] = []
        
        channels_store["minion-banter"] = Channel(
            channel_id="minion-banter",
            name="Minion Banter",
            description="Where Minions chat amongst themselves",
            members=[],
            is_private=False
        )
        messages_store["minion-banter"] = []
        
        channels_store["task-coordination"] = Channel(
            channel_id="task-coordination",
            name="Task Coordination",
            description="For coordinating on tasks",
            members=[],
            is_private=False
        )
        messages_store["task-coordination"] = []
        
        logger.info("Initialized default channels")


# Call init on module load
init_default_channels()


def convert_channel_to_response(channel: Channel) -> ChannelResponse:
    """Convert a Channel to API response format"""
    return ChannelResponse(
        id=channel.channel_id,
        name=channel.name,
        description=channel.description,
        members=channel.members,
        is_private=channel.is_private,
        created_at=channel.created_at.isoformat() if hasattr(channel, 'created_at') else None
    )


def convert_message_to_response(message: Message) -> MessageResponse:
    """Convert a Message to API response format"""
    return MessageResponse(
        id=message.message_id,
        sender=message.sender_id,
        content=message.content,
        timestamp=message.timestamp.isoformat(),
        type=MessageTypeEnum(message.message_type.value),
        channel_id=message.channel_id
    )


@router.get("/", response_model=ChannelsListResponse)
async def list_channels() -> ChannelsListResponse:
    """List all channels"""
    channels = [convert_channel_to_response(ch) for ch in channels_store.values()]
    
    return ChannelsListResponse(
        channels=channels,
        total=len(channels)
    )


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str) -> ChannelResponse:
    """Get a specific channel"""
    channel = channels_store.get(channel_id)
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return convert_channel_to_response(channel)


@router.post("/", response_model=OperationResponse)
async def create_channel(
    request: CreateChannelRequest
) -> OperationResponse:
    """Create a new channel"""
    try:
        # Generate channel ID
        channel_id = f"channel_{uuid.uuid4().hex[:8]}"
        
        # Create channel
        channel = Channel(
            channel_id=channel_id,
            name=request.name,
            description=request.description,
            members=request.members,
            is_private=request.is_private
        )
        
        # Store channel
        channels_store[channel_id] = channel
        messages_store[channel_id] = []
        
        logger.info(f"Created channel: {channel_id} - {request.name}")
        
        return OperationResponse(
            status="created",
            id=channel_id,
            message=f"Channel '{request.name}' created successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{channel_id}", response_model=OperationResponse)
async def delete_channel(channel_id: str) -> OperationResponse:
    """Delete a channel"""
    # Don't allow deletion of default channels
    if channel_id in ["general", "minion-banter", "task-coordination"]:
        raise HTTPException(status_code=403, detail="Cannot delete default channels")
    
    channel = channels_store.get(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Remove channel and its messages
    del channels_store[channel_id]
    if channel_id in messages_store:
        del messages_store[channel_id]
    
    return OperationResponse(
        status="deleted",
        id=channel_id,
        message=f"Channel '{channel.name}' deleted",
        timestamp=datetime.now().isoformat()
    )


@router.post("/{channel_id}/join", response_model=OperationResponse)
async def join_channel(
    channel_id: str,
    minion_id: str
) -> OperationResponse:
    """Add a minion to a channel"""
    channel = channels_store.get(channel_id)
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    if minion_id not in channel.members:
        channel.members.append(minion_id)
        
        return OperationResponse(
            status="joined",
            id=channel_id,
            message=f"Minion {minion_id} joined channel '{channel.name}'",
            timestamp=datetime.now().isoformat()
        )
    else:
        return OperationResponse(
            status="already_member",
            id=channel_id,
            message=f"Minion {minion_id} is already in channel '{channel.name}'",
            timestamp=datetime.now().isoformat()
        )


@router.post("/{channel_id}/leave", response_model=OperationResponse)
async def leave_channel(
    channel_id: str,
    minion_id: str
) -> OperationResponse:
    """Remove a minion from a channel"""
    channel = channels_store.get(channel_id)
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    if minion_id in channel.members:
        channel.members.remove(minion_id)
        
        return OperationResponse(
            status="left",
            id=channel_id,
            message=f"Minion {minion_id} left channel '{channel.name}'",
            timestamp=datetime.now().isoformat()
        )
    else:
        return OperationResponse(
            status="not_member",
            id=channel_id,
            message=f"Minion {minion_id} was not in channel '{channel.name}'",
            timestamp=datetime.now().isoformat()
        )


@router.get("/{channel_id}/messages", response_model=MessagesListResponse)
async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    offset: int = 0
) -> MessagesListResponse:
    """Get messages from a channel"""
    if channel_id not in channels_store:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    messages = messages_store.get(channel_id, [])
    
    # Apply pagination
    start = max(0, len(messages) - offset - limit)
    end = len(messages) - offset
    paginated_messages = messages[start:end]
    
    return MessagesListResponse(
        messages=[convert_message_to_response(msg) for msg in paginated_messages],
        total=len(messages),
        has_more=start > 0
    )


@router.post("/{channel_id}/messages", response_model=MessageResponse)
async def send_message(
    channel_id: str,
    request: SendMessageRequest,
    comm_system: InterMinionCommunicationSystem = Depends(get_comm_system),
    safeguards: CommunicationSafeguards = Depends(get_safeguards)
) -> MessageResponse:
    """Send a message to a channel"""
    if channel_id not in channels_store:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check safeguards for minion senders
    if request.sender != "commander":
        allowed, reason = await safeguards.check_message_allowed(
            request.sender,
            channel_id,
            request.content
        )
        
        if not allowed:
            raise HTTPException(status_code=429, detail=reason)
    
    # Create message
    message = Message(
        message_id=str(uuid.uuid4()),
        channel_id=channel_id,
        sender_id=request.sender,
        content=request.content,
        message_type=MessageType.CHAT,
        timestamp=datetime.now()
    )
    
    # Store message
    if channel_id not in messages_store:
        messages_store[channel_id] = []
    messages_store[channel_id].append(message)
    
    # Route through communication system for minion messages
    if request.sender != "commander":
        try:
            await comm_system.send_conversational_message(
                from_minion=request.sender,
                to_channel=channel_id,
                message=request.content
            )
        except Exception as e:
            logger.error(f"Error routing message through comm system: {e}")
    
    logger.info(f"Message sent to {channel_id} from {request.sender}")
    
    return convert_message_to_response(message)


@router.delete("/{channel_id}/messages", response_model=OperationResponse)
async def clear_channel_messages(channel_id: str) -> OperationResponse:
    """Clear all messages from a channel"""
    if channel_id not in channels_store:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    message_count = len(messages_store.get(channel_id, []))
    messages_store[channel_id] = []
    
    return OperationResponse(
        status="cleared",
        id=channel_id,
        message=f"Cleared {message_count} messages from channel",
        timestamp=datetime.now().isoformat()
    )