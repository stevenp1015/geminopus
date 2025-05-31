"""
Memory-based Channel Repository Implementation

In-memory implementation of ChannelRepository for testing and development.
"""

from typing import List, Optional, Dict
from datetime import datetime
import asyncio
from copy import deepcopy

from ..channel_repository import ChannelRepository
from .....domain import Channel, ChannelType


class ChannelRepositoryMemory(ChannelRepository):
    """
    In-memory implementation of ChannelRepository
    
    Stores channels in a dictionary for fast lookups.
    All operations are async to match the interface.
    """
    
    def __init__(self):
        """Initialize the in-memory storage"""
        self._channels: Dict[str, Channel] = {}
        self._lock = asyncio.Lock()
    
    async def save(self, entity: Channel) -> Channel:
        """
        Save or update a channel
        
        Args:
            entity: The channel to save
            
        Returns:
            The saved channel
        """
        async with self._lock:
            # Deep copy to avoid external modifications
            saved_channel = deepcopy(entity)
            saved_channel.updated_at = datetime.now()
            
            self._channels[entity.channel_id] = saved_channel
            
            return deepcopy(saved_channel)
    
    async def get_by_id(self, entity_id: str) -> Optional[Channel]:
        """
        Get a channel by its ID
        
        Args:
            entity_id: The ID of the channel
            
        Returns:
            The channel if found, None otherwise
        """
        async with self._lock:
            channel = self._channels.get(entity_id)
            return deepcopy(channel) if channel else None
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Channel]:
        """
        List all channels with pagination
        
        Args:
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            List of channels
        """
        async with self._lock:
            # Get all channels sorted by creation time
            all_channels = sorted(
                self._channels.values(),
                key=lambda c: c.created_at,
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(c) for c in all_channels[start:end]]
    
    async def delete(self, entity_id: str) -> bool:
        """
        Delete a channel by ID
        
        Args:
            entity_id: The ID of the channel to delete
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if entity_id in self._channels:
                del self._channels[entity_id]
                return True
            return False
    
    async def exists(self, entity_id: str) -> bool:
        """
        Check if a channel exists
        
        Args:
            entity_id: The ID of the channel
            
        Returns:
            True if exists, False otherwise
        """
        async with self._lock:
            return entity_id in self._channels
    
    async def list_by_type(self, channel_type: ChannelType, limit: int = 100, offset: int = 0) -> List[Channel]:
        """
        List channels by type
        
        Args:
            channel_type: The type of channels to filter by
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            List of channels with the specified type
        """
        async with self._lock:
            # Filter by type
            filtered_channels = [
                c for c in self._channels.values()
                if c.channel_type == channel_type
            ]
            
            # Sort by creation time
            filtered_channels.sort(key=lambda c: c.created_at, reverse=True)
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(c) for c in filtered_channels[start:end]]
    
    async def list_by_member(self, member_id: str, limit: int = 100, offset: int = 0) -> List[Channel]:
        """
        List channels that a member belongs to
        
        Args:
            member_id: The ID of the member
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            List of channels the member belongs to
        """
        async with self._lock:
            # Filter channels where member exists
            member_channels = [
                c for c in self._channels.values()
                if any(m.member_id == member_id for m in c.members)
            ]
            
            # Sort by last activity
            member_channels.sort(
                key=lambda c: c.last_activity or c.created_at,
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(c) for c in member_channels[start:end]]
    
    async def list_active(self, limit: int = 100, offset: int = 0) -> List[Channel]:
        """
        List active (non-deleted) channels
        
        Args:
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            List of active channels
        """
        async with self._lock:
            # Filter non-deleted channels
            active_channels = [
                c for c in self._channels.values()
                if not getattr(c, 'is_deleted', False)
            ]
            
            # Sort by last activity
            active_channels.sort(
                key=lambda c: c.last_activity or c.created_at,
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(c) for c in active_channels[start:end]]
    
    async def get_by_name(self, name: str) -> Optional[Channel]:
        """
        Get a channel by its name
        
        Args:
            name: The name of the channel
            
        Returns:
            The channel if found, None otherwise
        """
        async with self._lock:
            for channel in self._channels.values():
                if channel.name == name:
                    return deepcopy(channel)
            return None
    
    async def clear(self):
        """Clear all channels from memory (for testing)"""
        async with self._lock:
            self._channels.clear()