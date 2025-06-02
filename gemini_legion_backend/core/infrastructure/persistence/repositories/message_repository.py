"""
Message Repository Interface

This module defines the repository interface for Message entities.
"""

from typing import List, Optional
from datetime import datetime
from abc import abstractmethod

from .base import Repository
from ....domain import Message, MessageType


class MessageRepository(Repository[Message]):
    """
    Repository interface for Message entities
    
    Extends the base repository with Message-specific operations.
    """
    
    @abstractmethod
    async def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        sender_id: Optional[str] = None
    ) -> List[Message]:
        """
        Get messages from a specific channel with filtering
        
        Args:
            channel_id: The ID of the channel
            limit: Maximum number of messages to return
            before: Get messages before this timestamp
            after: Get messages after this timestamp
            sender_id: Filter by sender ID
            
        Returns:
            List of messages matching the criteria
        """
        pass
    
    @abstractmethod
    async def get_thread_messages(self, parent_message_id: str) -> List[Message]:
        """
        Get all messages in a thread
        
        Args:
            parent_message_id: The ID of the parent message
            
        Returns:
            List of messages in the thread
        """
        pass
    
    @abstractmethod
    async def search_messages(
        self,
        query: str,
        channel_ids: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Message]:
        """
        Search messages by content
        
        Args:
            query: The search query
            channel_ids: Optional list of channels to search in
            limit: Maximum number of results
            
        Returns:
            List of messages matching the query
        """
        pass
    
    @abstractmethod
    async def get_unread_count(self, channel_id: str, member_id: str, since: datetime) -> int:
        """
        Get count of unread messages for a member in a channel
        
        Args:
            channel_id: The ID of the channel
            member_id: The ID of the member
            since: Count messages after this timestamp
            
        Returns:
            Number of unread messages
        """
        pass