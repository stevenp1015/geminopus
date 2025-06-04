"""
Channel-related API endpoints

Handles channel creation, management, and messaging.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging
from datetime import datetime

from ..schemas import (
    CreateChannelRequest,
    SendMessageRequest,
    ChannelResponse,
    ChannelTypeEnum, # Added import for ChannelTypeEnum
    ChannelsListResponse,
    MessageResponse,
    MessagesListResponse,
    OperationResponse,
    MessageTypeEnum,
    AddMemberRequest # Added for add member endpoint
)
from ....core.dependencies import get_channel_service
from ....core.application.services import ChannelService
from ....core.domain import MessageType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/channels", tags=["channels"])


def convert_channel_to_response(channel_data: dict) -> ChannelResponse:
    """Convert channel data to API response format"""
    is_private = channel_data.get("is_private", False)
    
    # Determine channel type based on is_private
    # Assuming no 'dm' type differentiation from this data source for now.
    channel_type = ChannelTypeEnum.PRIVATE if is_private else ChannelTypeEnum.PUBLIC
    
    # Extract members carefully, assuming members can be a list of strings (IDs) or list of dicts
    members_data = channel_data.get("members", [])
    member_ids = []
    if members_data:
        if isinstance(members_data[0], dict): # If it's a list of dicts like {"member_id": "..."}
            member_ids = [str(member_info["member_id"]) for member_info in members_data if isinstance(member_info, dict) and "member_id" in member_info]
        elif isinstance(members_data[0], str): # If it's already a list of strings
            member_ids = [str(member_id) for member_id in members_data]


    return ChannelResponse(
        id=str(channel_data["channel_id"]), # Ensure ID is string
        name=str(channel_data["name"]),
        description=str(channel_data.get("description", "")) if channel_data.get("description") is not None else None,
        type=channel_type, # Set the new type field
        members=member_ids,
        # is_private is no longer part of ChannelResponse schema, derived into 'type'
        created_at=str(channel_data.get("created_at", datetime.now().isoformat()))
        # message_count and last_activity are not in the current ChannelResponse Pydantic model
    )


def convert_message_to_response(message_data: dict) -> MessageResponse:
    """Convert message data to API response format"""
    # Map message type
    type_map = {
        MessageType.CHAT: MessageTypeEnum.CHAT,
        MessageType.SYSTEM: MessageTypeEnum.SYSTEM,
        MessageType.TASK: MessageTypeEnum.TASK,
        MessageType.EMOTIONAL: MessageTypeEnum.EMOTIONAL
    }
    
    message_type = message_data.get("message_type", MessageType.CHAT)
    
    return MessageResponse(
        message_id=message_data["message_id"], # Changed from id to message_id
        sender=message_data["sender_id"],
        content=message_data["content"],
        timestamp=message_data["timestamp"].isoformat() if isinstance(message_data["timestamp"], datetime) else message_data["timestamp"],
        type=type_map.get(message_type, MessageTypeEnum.CHAT),
        channel_id=message_data["channel_id"],
        metadata=message_data.get("metadata", {})
    )


@router.get("/", response_model=ChannelsListResponse)
async def list_channels(
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelsListResponse:
    """List all channels"""
    try:
        channels_data = await channel_service.list_channels()
        channels = [convert_channel_to_response(ch) for ch in channels_data]
        
        return ChannelsListResponse(
            channels=channels,
            total=len(channels)
        )
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail="Error listing channels")


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: str,
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelResponse:
    """Get a specific channel"""
    try:
        channel_data = await channel_service.get_channel(channel_id)
        
        if not channel_data:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return convert_channel_to_response(channel_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving channel")

@router.post("/create", response_model=OperationResponse)
async def create_channel(
    request: CreateChannelRequest,
    channel_service: ChannelService = Depends(get_channel_service)
) -> OperationResponse:
    """Create a new channel"""
    try:
        channel_id = await channel_service.create_channel(
            name=request.name,
            description=request.description,
            is_private=request.is_private,
            initial_members=request.members
        )
        
        logger.info(f"Created channel: {channel_id} - {request.name}")
        
        return OperationResponse(
            status="created",
            id=channel_id,
            message=f"Channel '{request.name}' created successfully!",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{channel_id}", response_model=OperationResponse)
async def delete_channel(
    channel_id: str,
    channel_service: ChannelService = Depends(get_channel_service)
) -> OperationResponse:
    """Delete a channel"""
    try:
        # Don't allow deletion of default channels
        if channel_id in ["general", "minion-banter", "task-coordination"]:
            raise HTTPException(status_code=403, detail="Cannot delete default channels")
        
        success = await channel_service.delete_channel(channel_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return OperationResponse(
            status="deleted",
            id=channel_id,
            message=f"Channel deleted successfully",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting channel")


@router.post("/{channel_id}/members", response_model=OperationResponse)
async def add_channel_member( # Renamed from join_channel
    channel_id: str,
    request: AddMemberRequest, # Changed to use request body
    channel_service: ChannelService = Depends(get_channel_service)
) -> OperationResponse:
    """Add a minion to a channel."""
    try:
        success = await channel_service.add_member(channel_id, request.minion_id)
        
        if not success:
            # Consider more specific errors: channel not found vs minion not found vs already member
            raise HTTPException(status_code=404, detail="Channel or Minion not found, or member already exists.")
        
        return OperationResponse(
            status="member_added",
            id=channel_id,
            message=f"Minion {request.minion_id} added to channel {channel_id}.",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding member {request.minion_id} to channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Error adding member to channel")


@router.delete("/{channel_id}/members/{minion_id}", response_model=OperationResponse)
async def remove_channel_member( # Renamed from leave_channel and changed method to DELETE
    channel_id: str,
    minion_id: str, # Now a path parameter
    channel_service: ChannelService = Depends(get_channel_service)
) -> OperationResponse:
    """Remove a minion from a channel."""
    try:
        success = await channel_service.remove_member(channel_id, minion_id)
        
        if not success:
            # Consider more specific errors
            raise HTTPException(status_code=404, detail="Channel or Minion not found, or member not in channel.")
        
        return OperationResponse(
            status="member_removed",
            id=channel_id, # Or perhaps minion_id to indicate who was removed
            message=f"Minion {minion_id} removed from channel {channel_id}.",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member {minion_id} from channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Error removing member from channel")


@router.get("/{channel_id}/messages", response_model=MessagesListResponse)
async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    offset: int = 0,
    channel_service: ChannelService = Depends(get_channel_service)
) -> MessagesListResponse:
    """Get messages from a channel"""
    try:
        result = await channel_service.get_channel_messages(
            channel_id=channel_id,
            limit=limit,
            offset=offset
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        messages = [convert_message_to_response(msg) for msg in result["messages"]]
        
        return MessagesListResponse(
            messages=messages,
            total=result["total"],
            has_more=result["has_more"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving messages")


@router.post("/{channel_id}/send", response_model=MessageResponse)
async def send_message(
    channel_id: str,
    request: SendMessageRequest,
    channel_service: ChannelService = Depends(get_channel_service)
) -> MessageResponse:
    """Send a message to a channel"""
    try:
        # Determine message type based on content
        message_type = MessageType.CHAT
        if request.sender == "system":
            message_type = MessageType.SYSTEM
        elif "[TASK]" in request.content:
            message_type = MessageType.TASK
        elif "[EMOTIONAL]" in request.content:
            message_type = MessageType.EMOTIONAL
        
        message_data = await channel_service.send_message(
            channel_id=channel_id,
            sender_id=request.sender,
            content=request.content,
            message_type=message_type
        )
        
        if not message_data:
            raise HTTPException(
                status_code=400, 
                detail="Failed to send message - channel not found or safeguards triggered"
            )
        
        logger.info(f"Message sent to {channel_id} from {request.sender}")
        
        return convert_message_to_response(message_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Error sending message")


@router.delete("/{channel_id}/messages", response_model=OperationResponse)
async def clear_channel_messages(
    channel_id: str,
    channel_service: ChannelService = Depends(get_channel_service)
) -> OperationResponse:
    """Clear all messages from a channel"""
    try:
        message_count = await channel_service.clear_messages(channel_id)
        
        if message_count is None:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return OperationResponse(
            status="cleared",
            id=channel_id,
            message=f"Cleared {message_count} messages from channel!",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing channel messages: {e}")
        raise HTTPException(status_code=500, detail="Error clearing messages")


@router.post("/broadcast", response_model=OperationResponse)
async def broadcast_message(
    content: str,
    sender: str = "system",
    channel_service: ChannelService = Depends(get_channel_service)
) -> OperationResponse:
    """Broadcast a message to all channels"""
    try:
        channels = await channel_service.list_channels()
        sent_count = 0
        
        for channel in channels:
            try:
                await channel_service.send_message(
                    channel_id=channel["channel_id"],
                    sender_id=sender,
                    content=content,
                    message_type=MessageType.SYSTEM
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to {channel['channel_id']}: {e}")
        
        return OperationResponse(
            status="broadcast_complete",
            id="broadcast",
            message=f"Broadcast sent to {sent_count} channels",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Error broadcasting message")