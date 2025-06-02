"""
Memory-based Message Repository Implementation

In-memory implementation of MessageRepository for testing and development.
"""

from typing import List, Optional, Dict
from datetime import datetime
import asyncio
from copy import deepcopy
from collections import defaultdict

from ..message_repository import MessageRepository
from .....domain import Message, MessageType


class MessageRepositoryMemory(MessageRepository):
    """
    In-memory implementation of MessageRepository
    
    Stores messages organized by channel for efficient retrieval.
    """
    
    def __init__(self):
        """Initialize the in-memory storage"""
        # Messages stored by channel_id for efficient channel queries
        self._messages_by_channel: Dict[str, List[Message]] = defaultdict(list)
        # Also store by message_id for direct lookups
        self._messages_by_id: Dict[str, Message] = {}
        self._lock = asyncio.Lock()
    
    async def save(self, entity: Message) -> Message:
        """
        Save or update a message
        
        Args:
            entity: The message to save
            
        Returns:
            The saved message
        """
        async with self._lock:
            # Deep copy to avoid external modifications
            saved_message = deepcopy(entity)
            
            # Update or add to channel list
            channel_messages = self._messages_by_channel[entity.channel_id]
            
            # Check if updating existing message
            existing_index = None
            for i, msg in enumerate(channel_messages):
                if msg.message_id == entity.message_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing message
                channel_messages[existing_index] = saved_message
            else:
                # Add new message
                channel_messages.append(saved_message)
                # Sort by timestamp
                channel_messages.sort(key=lambda m: m.timestamp)
            
            # Update ID lookup
            self._messages_by_id[entity.message_id] = saved_message
            
            return deepcopy(saved_message)
    
    async def get_by_id(self, entity_id: str) -> Optional[Message]:
        """
        Get a message by its ID
        
        Args:
            entity_id: The ID of the message
            
        Returns:
            The message if found, None otherwise
        """
        async with self._lock:
            message = self._messages_by_id.get(entity_id)
            return deepcopy(message) if message else None
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Message]:
        """
        List all messages with pagination
        
        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of messages
        """
        async with self._lock:
            # Get all messages sorted by timestamp
            all_messages = list(self._messages_by_id.values())
            all_messages.sort(key=lambda m: m.timestamp, reverse=True)
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(m) for m in all_messages[start:end]]
    
    async def delete(self, entity_id: str) -> bool:
        """
        Delete a message by ID
        
        Args:
            entity_id: The ID of the message to delete
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            message = self._messages_by_id.get(entity_id)
            if not message:
                return False
            
            # Remove from channel list
            channel_messages = self._messages_by_channel[message.channel_id]
            self._messages_by_channel[message.channel_id] = [
                m for m in channel_messages if m.message_id != entity_id
            ]
            
            # Remove from ID lookup
            del self._messages_by_id[entity_id]
            
            return True
    
    async def exists(self, entity_id: str) -> bool:
        """
        Check if a message exists
        
        Args:
            entity_id: The ID of the message
            
        Returns:
            True if exists, False otherwise
        """
        async with self._lock:
            return entity_id in self._messages_by_id
    
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
        async with self._lock:
            messages = self._messages_by_channel.get(channel_id, [])
            
            # Apply filters
            filtered = messages
            
            if before:
                filtered = [m for m in filtered if m.timestamp < before]
            
            if after:
                filtered = [m for m in filtered if m.timestamp > after]
            
            if sender_id:
                filtered = [m for m in filtered if m.sender_id == sender_id]
            
            # Sort by timestamp descending (newest first)
            filtered.sort(key=lambda m: m.timestamp, reverse=True)
            
            # Apply limit
            filtered = filtered[:limit]
            
            return [deepcopy(m) for m in filtered]
    
    async def get_thread_messages(
        self,
        parent_message_id: str,
        limit: int = 50
    ) -> List[Message]:
        """
        Get messages in a thread (replies to a parent message)
        
        Args:
            parent_message_id: The ID of the parent message
            limit: Maximum number of messages to return
            
        Returns:
            List of reply messages
        """
        async with self._lock:
            # Find all messages with this parent
            thread_messages = [
                m for m in self._messages_by_id.values()
                if m.parent_message_id == parent_message_id
            ]
            
            # Sort by timestamp
            thread_messages.sort(key=lambda m: m.timestamp)
            
            # Apply limit
            thread_messages = thread_messages[:limit]
            
            return [deepcopy(m) for m in thread_messages]
    
    async def search_messages(
        self,
        query: str,
        channel_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """
        Search messages by content
        
        Args:
            query: Search query string
            channel_id: Limit search to specific channel
            sender_id: Limit search to specific sender
            limit: Maximum number of messages to return
            
        Returns:
            List of messages matching the search criteria
        """
        async with self._lock:
            # Start with all messages or channel-specific
            if channel_id:
                messages = self._messages_by_channel.get(channel_id, [])
            else:
                messages = list(self._messages_by_id.values())
            
            # Filter by sender if specified
            if sender_id:
                messages = [m for m in messages if m.sender_id == sender_id]
            
            # Simple text search in content
            query_lower = query.lower()
            matching = [
                m for m in messages
                if query_lower in m.content.lower()
            ]
            
            # Sort by timestamp descending
            matching.sort(key=lambda m: m.timestamp, reverse=True)
            
            # Apply limit
            matching = matching[:limit]
            
            return [deepcopy(m) for m in matching]
    
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
        async with self._lock:
            messages = self._messages_by_channel.get(channel_id, [])
            
            # Count messages after 'since' timestamp that aren't from the member
            unread_count = sum(
                1 for m in messages 
                if m.timestamp > since and m.sender_id != member_id
            )
            
            return unread_count
    
    async def clear(self):
        """Clear all messages from memory (for testing)"""
        async with self._lock:
            self._messages_by_channel.clear()
            self._messages_by_id.clear()