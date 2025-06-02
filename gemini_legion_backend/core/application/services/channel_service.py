"""
Channel Service - Application Layer

This service manages communication channels, message persistence, and real-time
message delivery coordination between Minions.
"""

from typing import List, Optional, Dict, Any, Set, Callable
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import asdict
import json
from collections import defaultdict

from ....api.websocket.connection_manager import connection_manager
from ...domain import (
    Channel,
    ChannelType,
    Message,
    MessageType,
    ChannelMember,
    ChannelRole
)
from ...infrastructure.persistence.repositories import ChannelRepository, MessageRepository
from ...infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from .minion_service import MinionService


logger = logging.getLogger(__name__)


class ChannelService:
    """
    Application service for Channel operations
    
    This service manages channels, messages, and coordinates real-time
    communication between Minions through the messaging infrastructure.
    """
    
    def __init__(
        self,
        channel_repository: ChannelRepository,
        message_repository: MessageRepository,
        comm_system: InterMinionCommunicationSystem,
        minion_service: MinionService
    ):
        """
        Initialize the Channel service
        
        Args:
            channel_repository: Repository for persisting channel state
            message_repository: Repository for persisting messages
            comm_system: Communication system for real-time messaging
            minion_service: Service for interacting with Minions
        """
        self.channel_repo = channel_repository
        self.message_repo = message_repository
        self.comm_system = comm_system
        self.minion_service = minion_service
        
        # Active channels cache
        self.active_channels: Dict[str, Channel] = {}
        
        # Message subscribers for real-time updates
        self.channel_subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        
        # Background tasks
        self._message_persist_task: Optional[asyncio.Task] = None
        self._channel_cleanup_task: Optional[asyncio.Task] = None
        
        # Message buffer for batched persistence
        self.message_buffer: List[Message] = []
        self._buffer_lock = asyncio.Lock()
    
    async def start(self):
        """Start the service and background tasks"""
        logger.info("Starting Channel Service...")
        
        # Start background tasks
        self._message_persist_task = asyncio.create_task(self._message_persist_loop())
        self._channel_cleanup_task = asyncio.create_task(self._channel_cleanup_loop())
        
        # Load active channels from repository
        await self._load_active_channels()
        
        # Set up communication system callbacks
        self._setup_comm_system_integration()
        
        logger.info("Channel Service started successfully")
    
    async def stop(self):
        """Stop the service and cleanup"""
        logger.info("Stopping Channel Service...")
        
        # Cancel background tasks
        if self._message_persist_task:
            self._message_persist_task.cancel()
        if self._channel_cleanup_task:
            self._channel_cleanup_task.cancel()
        
        # Persist any buffered messages
        await self._flush_message_buffer()
        
        # Save all active channels
        for channel in self.active_channels.values():
            await self.channel_repo.save(channel)
        
        logger.info("Channel Service stopped")
    
    async def create_channel(
        self,
        channel_id: str,
        name: str,
        channel_type: str = "public",
        description: Optional[str] = None,
        creator: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new channel
        
        Args:
            channel_id: Unique identifier for the channel
            name: Display name of the channel
            channel_type: Type of channel (public, private, direct)
            description: Channel description
            creator: ID of the creator (minion or user)
            metadata: Additional channel metadata
            
        Returns:
            Created channel details
        """
        try:
            # Check if channel already exists
            if channel_id in self.active_channels:
                raise ValueError(f"Channel {channel_id} already exists")
            
            # Create domain channel object
            channel = Channel(
                channel_id=channel_id,
                name=name,
                channel_type=ChannelType(channel_type),
                description=description or "",
                created_at=datetime.now(),
                created_by=creator or "system",
                members=[],
                metadata=metadata or {}
            )
            
            # Add creator as admin member if specified
            if creator:
                member = ChannelMember(
                    member_id=creator,
                    role=ChannelRole.ADMIN,
                    joined_at=datetime.now()
                )
                channel.members.append(member)
            
            # Persist to repository
            await self.channel_repo.save(channel)
            
            # Add to active channels
            self.active_channels[channel_id] = channel
            
            # Register with communication system
            self.comm_system.create_channel(channel_id)
            
            # Auto-add general minions to public channels
            if channel_type == "public":
                await self._auto_add_minions_to_public_channel(channel_id)
            
            logger.info(f"Created channel: {name} ({channel_id})")
            
            channel_dict = self._channel_to_dict(channel)
            asyncio.create_task(connection_manager.broadcast_service_event(
                "channel_created",
                {"channel": channel_dict}
            ))
            return channel_dict
            
        except Exception as e:
            logger.error(f"Failed to create channel {channel_id}: {e}")
            raise
    
    async def add_member(
        self,
        channel_id: str,
        member_id: str,
        role: str = "member",
        added_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a member to a channel
        
        Args:
            channel_id: ID of the channel
            member_id: ID of the member to add (minion or user)
            role: Role in the channel (member, moderator, admin)
            added_by: ID of who is adding the member
            
        Returns:
            Updated channel details
        """
        channel = self.active_channels.get(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")
        
        # Check if already a member
        if any(m.member_id == member_id for m in channel.members):
            raise ValueError(f"{member_id} is already a member of {channel_id}")
        
        # Check permissions if private channel
        if channel.channel_type == ChannelType.PRIVATE and added_by:
            if not self._has_permission(channel, added_by, "add_members"):
                raise ValueError(f"{added_by} doesn't have permission to add members")
        
        # Create member entry
        member = ChannelMember(
            member_id=member_id,
            role=ChannelRole(role),
            joined_at=datetime.now(),
            added_by=added_by
        )
        
        # Add to channel
        channel.members.append(member)
        channel.member_count = len(channel.members)
        channel.last_activity = datetime.now()
        
        # Save channel
        await self.channel_repo.save(channel)
        
        # Notify communication system
        self.comm_system.add_channel_member(channel_id, member_id)
        
        # Send join notification
        await self._send_system_message(
            channel_id,
            f"{member_id} joined the channel",
            metadata={"event": "member_joined", "member_id": member_id}
        )
        
        logger.info(f"Added {member_id} to channel {channel_id}")
        
        updated_channel_dict = self._channel_to_dict(channel)
        asyncio.create_task(connection_manager.broadcast_service_event(
            "channel_member_added",
            {"channel_id": channel_id, "minion_id": member_id}
        ))
        asyncio.create_task(connection_manager.broadcast_service_event(
            "channel_updated",
            {"channel_id": channel_id, "updates": updated_channel_dict}
        ))
        return updated_channel_dict
    
    async def remove_member(
        self,
        channel_id: str,
        member_id: str,
        removed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a member from a channel
        
        Args:
            channel_id: ID of the channel
            member_id: ID of the member to remove
            removed_by: ID of who is removing the member
            
        Returns:
            Updated channel details
        """
        channel = self.active_channels.get(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")
        
        # Find and remove member
        channel.members = [m for m in channel.members if m.member_id != member_id]
        channel.member_count = len(channel.members)
        channel.last_activity = datetime.now()
        
        # Save channel
        await self.channel_repo.save(channel)
        
        # Notify communication system
        self.comm_system.remove_channel_member(channel_id, member_id)
        
        # Send leave notification
        await self._send_system_message(
            channel_id,
            f"{member_id} left the channel",
            metadata={"event": "member_left", "member_id": member_id}
        )
        
        logger.info(f"Removed {member_id} from channel {channel_id}")
        
        updated_channel_dict = self._channel_to_dict(channel)
        asyncio.create_task(connection_manager.broadcast_service_event(
            "channel_member_removed",
            {"channel_id": channel_id, "minion_id": member_id}
        ))
        asyncio.create_task(connection_manager.broadcast_service_event(
            "channel_updated",
            {"channel_id": channel_id, "updates": updated_channel_dict}
        ))
        return updated_channel_dict
    
    async def send_message(
        self,
        channel_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        parent_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a channel
        
        Args:
            channel_id: ID of the channel
            sender_id: ID of the sender
            content: Message content
            message_type: Type of message (text, system, command, etc.)
            metadata: Additional message metadata
            parent_message_id: ID of parent message for threads
            
        Returns:
            Sent message details
        """
        channel = self.active_channels.get(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")
        
        # Check if sender is member
        if not any(m.member_id == sender_id for m in channel.members):
            if channel.channel_type != ChannelType.PUBLIC:
                raise ValueError(f"{sender_id} is not a member of {channel_id}")
        
        # Create message
        message = Message(
            message_id=f"{channel_id}_{datetime.now().timestamp()}",
            channel_id=channel_id,
            sender_id=sender_id,
            content=content,
            message_type=MessageType(message_type),
            timestamp=datetime.now(),
            metadata=metadata or {},
            parent_message_id=parent_message_id
        )
        
        # Add to buffer for persistence
        async with self._buffer_lock:
            self.message_buffer.append(message)
        
        # Update channel activity
        channel.last_activity = datetime.now()
        channel.message_count += 1
        
        # Broadcast through communication system
        await self.comm_system.broadcast_message(
            channel_id,
            sender_id,
            content,
            metadata
        )
        
        # Notify subscribers
        await self._notify_subscribers(channel_id, message)
        
        logger.debug(f"Message sent to {channel_id} by {sender_id}")
        
        message_dict = self._message_to_dict(message)
        asyncio.create_task(connection_manager.broadcast_service_event(
            "message_sent",
            {"channel_id": channel_id, "message": message_dict}
        ))
        return message_dict
    
    async def get_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        sender_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a channel
        
        Args:
            channel_id: ID of the channel
            limit: Maximum number of messages to return
            before: Get messages before this timestamp
            after: Get messages after this timestamp
            sender_filter: Filter by sender ID
            
        Returns:
            List of messages
        """
        # Get from repository
        messages = await self.message_repo.get_channel_messages(
            channel_id,
            limit=limit,
            before=before,
            after=after,
            sender_id=sender_filter
        )
        
        # Include buffered messages
        async with self._buffer_lock:
            buffered = [
                m for m in self.message_buffer
                if m.channel_id == channel_id
            ]
            
            # Apply filters to buffered messages
            if before:
                buffered = [m for m in buffered if m.timestamp < before]
            if after:
                buffered = [m for m in buffered if m.timestamp > after]
            if sender_filter:
                buffered = [m for m in buffered if m.sender_id == sender_filter]
        
        # Combine and sort
        all_messages = messages + buffered
        all_messages.sort(key=lambda m: m.timestamp, reverse=True)
        
        # Apply limit
        all_messages = all_messages[:limit]
        
        return [self._message_to_dict(m) for m in all_messages]
    
    async def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel details by ID"""
        channel = self.active_channels.get(channel_id)
        if not channel:
            channel = await self.channel_repo.get_by_id(channel_id)
            if not channel:
                return None
        
        return self._channel_to_dict(channel)
    
    async def list_channels(
        self,
        member_id: Optional[str] = None,
        channel_type: Optional[str] = None,
        include_private: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List channels with optional filtering
        
        Args:
            member_id: Filter by member
            channel_type: Filter by type
            include_private: Include private channels
            limit: Maximum number to return
            offset: Pagination offset
            
        Returns:
            List of channel details
        """
        # Get from repository
        channels = await self.channel_repo.list_all(limit, offset)
        
        # Apply filters
        if channel_type:
            channels = [c for c in channels if c.channel_type.value == channel_type]
        
        if not include_private:
            channels = [c for c in channels if c.channel_type != ChannelType.PRIVATE]
        
        if member_id:
            channels = [
                c for c in channels
                if any(m.member_id == member_id for m in c.members)
            ]
        
        return [self._channel_to_dict(c) for c in channels]
    
    async def update_channel(
        self,
        channel_id: str,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update channel properties
        
        Args:
            channel_id: ID of channel to update
            updates: Dictionary of updates
            updated_by: ID of who is updating
            
        Returns:
            Updated channel details
        """
        channel = self.active_channels.get(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")
        
        # Check permissions
        if updated_by and not self._has_permission(channel, updated_by, "edit_channel"):
            raise ValueError(f"{updated_by} doesn't have permission to edit channel")
        
        # Apply updates
        if "name" in updates:
            channel.name = updates["name"]
        if "description" in updates:
            channel.description = updates["description"]
        if "metadata" in updates:
            channel.metadata.update(updates["metadata"])
        
        channel.last_activity = datetime.now()
        
        # Save channel
        await self.channel_repo.save(channel)
        
        logger.info(f"Updated channel {channel_id}")
        
        updated_channel_dict = self._channel_to_dict(channel)
        asyncio.create_task(connection_manager.broadcast_service_event(
            "channel_updated",
            {"channel_id": channel_id, "updates": updated_channel_dict}
        ))
        return updated_channel_dict
    
    async def delete_channel(
        self,
        channel_id: str,
        deleted_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a channel
        
        Args:
            channel_id: ID of channel to delete
            deleted_by: ID of who is deleting
            
        Returns:
            Deletion confirmation
        """
        channel = self.active_channels.get(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")
        
        # Check permissions
        if deleted_by and not self._has_permission(channel, deleted_by, "delete_channel"):
            raise ValueError(f"{deleted_by} doesn't have permission to delete channel")
        
        # Don't allow deletion of default channels
        if channel_id in ["general", "announcements"]:
            raise ValueError(f"Cannot delete system channel {channel_id}")
        
        # Send deletion notification
        await self._send_system_message(
            channel_id,
            f"Channel {channel.name} is being deleted",
            metadata={"event": "channel_deleted"}
        )
        
        # Remove from active channels
        del self.active_channels[channel_id]
        
        # Mark as deleted in repository (soft delete)
        channel.is_deleted = True
        channel.deleted_at = datetime.now()
        channel.deleted_by = deleted_by
        await self.channel_repo.save(channel)
        
        # Clean up communication system
        self.comm_system.delete_channel(channel_id)
        
        logger.info(f"Deleted channel {channel_id}")
        
        asyncio.create_task(connection_manager.broadcast_service_event(
            "channel_deleted",
            {"channel_id": channel_id}
        ))

        return {
            "channel_id": channel_id,
            "deleted": True,
            "deleted_at": datetime.now().isoformat()
        }
    
    async def subscribe_to_channel(
        self,
        channel_id: str,
        callback: Callable[[Message], None]
    ) -> str:
        """
        Subscribe to real-time channel messages
        
        Args:
            channel_id: ID of channel to subscribe to
            callback: Function to call when messages arrive
            
        Returns:
            Subscription ID
        """
        self.channel_subscribers[channel_id].add(callback)
        
        subscription_id = f"sub_{channel_id}_{len(self.channel_subscribers[channel_id])}"
        
        logger.debug(f"Added subscription to {channel_id}")
        
        return subscription_id
    
    async def unsubscribe_from_channel(
        self,
        channel_id: str,
        callback: Callable[[Message], None]
    ):
        """Unsubscribe from channel messages"""
        if callback in self.channel_subscribers[channel_id]:
            self.channel_subscribers[channel_id].remove(callback)
    
    async def _message_persist_loop(self):
        """Background task to persist buffered messages"""
        while True:
            try:
                await asyncio.sleep(5)  # Persist every 5 seconds
                await self._flush_message_buffer()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message persist loop: {e}")
    
    async def _flush_message_buffer(self):
        """Flush message buffer to repository"""
        async with self._buffer_lock:
            if not self.message_buffer:
                return
            
            messages_to_save = self.message_buffer.copy()
            self.message_buffer.clear()
        
        # Batch save messages
        for message in messages_to_save:
            try:
                await self.message_repo.save(message)
            except Exception as e:
                logger.error(f"Failed to persist message {message.message_id}: {e}")
        
        logger.debug(f"Persisted {len(messages_to_save)} messages")
    
    async def _channel_cleanup_loop(self):
        """Background task to clean up inactive channels"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                # Clean up empty direct message channels older than 7 days
                cutoff = datetime.now() - timedelta(days=7)
                
                for channel_id, channel in list(self.active_channels.items()):
                    if (channel.channel_type == ChannelType.DIRECT and
                        channel.message_count == 0 and
                        channel.created_at < cutoff):
                        
                        logger.info(f"Cleaning up empty DM channel {channel_id}")
                        await self.delete_channel(channel_id, deleted_by="system")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in channel cleanup loop: {e}")
    
    async def _load_active_channels(self):
        """Load active channels from repository"""
        try:
            # Get all non-deleted channels
            channels = await self.channel_repo.list_active()
            
            for channel in channels:
                self.active_channels[channel.channel_id] = channel
                
                # Register with communication system
                self.comm_system.create_channel(channel.channel_id)
                
                # Re-add members to communication system
                for member in channel.members:
                    self.comm_system.add_channel_member(
                        channel.channel_id, member.member_id
                    )
            
            # Ensure default channels exist
            await self._ensure_default_channels()
            
            logger.info(f"Loaded {len(channels)} active channels")
            
        except Exception as e:
            logger.error(f"Failed to load active channels: {e}")
    
    async def _ensure_default_channels(self):
        """Ensure default system channels exist"""
        default_channels = [
            {
                "channel_id": "general",
                "name": "General",
                "description": "General discussion for all Minions",
                "channel_type": "public"
            },
            {
                "channel_id": "announcements",
                "name": "Announcements",
                "description": "Important system announcements",
                "channel_type": "public"
            },
            {
                "channel_id": "task_coordination",
                "name": "Task Coordination",
                "description": "Task assignment and coordination",
                "channel_type": "public"
            }
        ]
        
        for channel_config in default_channels:
            if channel_config["channel_id"] not in self.active_channels:
                await self.create_channel(**channel_config, creator="system")
    
    def _setup_comm_system_integration(self):
        """Set up callbacks from communication system"""
        # This would integrate with the actual messaging infrastructure
        # For now, it's a placeholder for the integration point
        pass
    
    async def _auto_add_minions_to_public_channel(self, channel_id: str):
        """Automatically add active minions to public channels"""
        try:
            # Get active minions
            minions = await self.minion_service.list_minions(status_filter="active")
            
            for minion in minions:
                try:
                    await self.add_member(
                        channel_id,
                        minion["minion_id"],
                        role="member",
                        added_by="system"
                    )
                except ValueError as ve: # Specifically catch if already a member or other known input issue
                    logger.debug(f"Skipping add_member for {minion.get('minion_id', 'UNKNOWN')} to {channel_id} (already member or input issue): {ve}")
                except Exception as e_add: # Catch other unexpected errors during add_member
                    logger.error(f"Unexpected error auto-adding minion {minion.get('minion_id', 'UNKNOWN')} to {channel_id}: {e_add}")
                    
        except Exception as e:
            logger.error(f"Error auto-adding minions to {channel_id}: {e}")
    
    async def _send_system_message(
        self,
        channel_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Send a system message to a channel"""
        await self.send_message(
            channel_id=channel_id,
            sender_id="system",
            content=content,
            message_type="system",
            metadata=metadata
        )
    
    async def _notify_subscribers(self, channel_id: str, message: Message):
        """Notify all subscribers of a new message"""
        subscribers = self.channel_subscribers.get(channel_id, set())
        
        for callback in subscribers:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error in channel subscriber callback: {e}")
    
    def _has_permission(
        self,
        channel: Channel,
        member_id: str,
        permission: str
    ) -> bool:
        """Check if a member has permission in a channel"""
        member = next((m for m in channel.members if m.member_id == member_id), None)
        
        if not member:
            return False
        
        # Admin has all permissions
        if member.role == ChannelRole.ADMIN:
            return True
        
        # Moderator permissions
        if member.role == ChannelRole.MODERATOR:
            if permission in ["add_members", "remove_members", "edit_channel"]:
                return True
        
        # Regular members can only send messages
        if permission == "send_message":
            return True
        
        return False
    
    def _channel_to_dict(self, channel: Channel) -> Dict[str, Any]:
        """Convert domain Channel to API-friendly dictionary"""
        return {
            "channel_id": channel.channel_id,
            "name": channel.name,
            "channel_type": channel.channel_type.value,
            "description": channel.description,
            "created_at": channel.created_at.isoformat(),
            "created_by": channel.created_by,
            "member_count": len(channel.members),
            "message_count": channel.message_count,
            "last_activity": channel.last_activity.isoformat() if channel.last_activity else None,
            "members": [
                {
                    "member_id": m.member_id,
                    "role": m.role.value,
                    "joined_at": m.joined_at.isoformat()
                }
                for m in channel.members
            ],
            "metadata": channel.metadata
        }
    
    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """Convert domain Message to API-friendly dictionary"""
        return {
            "message_id": message.message_id,
            "channel_id": message.channel_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "message_type": message.message_type.value,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
            "parent_message_id": message.parent_message_id,
            "reactions": message.reactions,
            "edited": message.edited,
            "edited_at": message.edited_at.isoformat() if message.edited_at else None
        }
