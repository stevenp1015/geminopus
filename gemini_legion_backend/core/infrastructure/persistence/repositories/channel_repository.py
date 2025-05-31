"""
Channel Repository Interface

This module defines the repository interface for Channel entities.
"""

from typing import List, Optional
from abc import abstractmethod

from .base import Repository
from ....domain import Channel, ChannelType


class ChannelRepository(Repository[Channel]):
    """
    Repository interface for Channel entities
    
    Extends the base repository with Channel-specific operations.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def list_active(self, limit: int = 100, offset: int = 0) -> List[Channel]:
        """
        List active (non-deleted) channels
        
        Args:
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            List of active channels
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Channel]:
        """
        Get a channel by its name
        
        Args:
            name: The name of the channel
            
        Returns:
            The channel if found, None otherwise
        """
        pass