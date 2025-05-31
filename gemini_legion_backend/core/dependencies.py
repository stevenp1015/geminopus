"""
Service initialization and dependency injection

This module provides functions to initialize and access the application services
with all their dependencies properly configured.
"""

from typing import Optional
import logging
from pathlib import Path

from .infrastructure.persistence.repositories.memory import (
    ChannelRepositoryMemory,
    MessageRepositoryMemory,
    MinionRepositoryMemory,
    TaskRepositoryMemory
)
from .infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from ..infrastructure.messaging.safeguards import CommunicationSafeguards
from .application.services import (
    MinionService,
    TaskService,
    ChannelService
)


logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Container for all application services
    
    This class manages the lifecycle of all services and their dependencies.
    """
    
    def __init__(self):
        """Initialize the service container"""
        # Repositories (using in-memory for now)
        self.minion_repository = MinionRepositoryMemory()
        self.task_repository = TaskRepositoryMemory()
        self.channel_repository = ChannelRepositoryMemory()
        self.message_repository = MessageRepositoryMemory()
        
        # Infrastructure
        self.comm_system = InterMinionCommunicationSystem()
        self.safeguards = CommunicationSafeguards()
        
        # Services
        self.minion_service: Optional[MinionService] = None
        self.task_service: Optional[TaskService] = None
        self.channel_service: Optional[ChannelService] = None
        
        # Configuration
        self.config = {
            "diary_storage_path": Path("/tmp/gemini_legion/diaries"),
            "memory_storage_path": Path("/tmp/gemini_legion/memories"),
            "max_minions": 50,
            "enable_autonomous_messaging": True
        }
    
    async def initialize(self):
        """Initialize all services"""
        logger.info("Initializing service container...")
        
        # Ensure storage directories exist
        self.config["diary_storage_path"].mkdir(parents=True, exist_ok=True)
        self.config["memory_storage_path"].mkdir(parents=True, exist_ok=True)
        
        # Initialize MinionService
        self.minion_service = MinionService(
            minion_repository=self.minion_repository,
            diary_storage_path=str(self.config["diary_storage_path"]),
            memory_storage_path=str(self.config["memory_storage_path"]),
            comm_system=self.comm_system,
            safeguards=self.safeguards
        )
        
        # Initialize TaskService
        self.task_service = TaskService(
            task_repository=self.task_repository,
            minion_service=self.minion_service
        )
        
        # Initialize ChannelService
        self.channel_service = ChannelService(
            channel_repository=self.channel_repository,
            message_repository=self.message_repository,
            comm_system=self.comm_system,
            minion_service=self.minion_service
        )
        
        # Start services
        await self.minion_service.start()
        await self.task_service.start()
        await self.channel_service.start()
        
        logger.info("Service container initialized successfully")
    
    async def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down service container...")
        
        # Stop services in reverse order
        if self.channel_service:
            await self.channel_service.stop()
        
        if self.task_service:
            await self.task_service.stop()
        
        if self.minion_service:
            await self.minion_service.stop()
        
        logger.info("Service container shutdown complete")
    
    def get_minion_service(self) -> MinionService:
        """Get the minion service instance"""
        if not self.minion_service:
            raise RuntimeError("Service container not initialized")
        return self.minion_service
    
    def get_task_service(self) -> TaskService:
        """Get the task service instance"""
        if not self.task_service:
            raise RuntimeError("Service container not initialized")
        return self.task_service
    
    def get_channel_service(self) -> ChannelService:
        """Get the channel service instance"""
        if not self.channel_service:
            raise RuntimeError("Service container not initialized")
        return self.channel_service


# Global service container instance
_service_container: Optional[ServiceContainer] = None


async def initialize_services():
    """
    Initialize the global service container
    
    This should be called once at application startup.
    """
    global _service_container
    
    if _service_container is not None:
        logger.warning("Services already initialized")
        return
    
    _service_container = ServiceContainer()
    await _service_container.initialize()


async def shutdown_services():
    """
    Shutdown the global service container
    
    This should be called at application shutdown.
    """
    global _service_container
    
    if _service_container is None:
        logger.warning("Services not initialized")
        return
    
    await _service_container.shutdown()
    _service_container = None


def get_service_container() -> ServiceContainer:
    """
    Get the global service container
    
    Returns:
        The initialized service container
        
    Raises:
        RuntimeError: If services have not been initialized
    """
    if _service_container is None:
        raise RuntimeError(
            "Services not initialized. Call initialize_services() first."
        )
    
    return _service_container


# Dependency injection functions for FastAPI
def get_minion_service() -> MinionService:
    """FastAPI dependency for MinionService"""
    return get_service_container().get_minion_service()


def get_task_service() -> TaskService:
    """FastAPI dependency for TaskService"""
    return get_service_container().get_task_service()


def get_channel_service() -> ChannelService:
    """FastAPI dependency for ChannelService"""
    return get_service_container().get_channel_service()