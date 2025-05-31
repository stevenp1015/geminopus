"""
Base Repository Interface

This module defines the base repository interface that all repositories
should implement.
"""

from typing import Generic, TypeVar, List, Optional
from abc import ABC, abstractmethod

# Generic type for domain entities
T = TypeVar('T')


class Repository(Generic[T], ABC):
    """
    Base repository interface for domain entities
    
    This interface defines the standard CRUD operations that all
    repositories should support.
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Save or update an entity
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get an entity by its ID
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        List all entities with pagination
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            True if exists, False otherwise
        """
        pass