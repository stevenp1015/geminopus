"""
Minion Repository Interface

This module defines the repository interface for Minion entities.
"""

from typing import List, Optional
from abc import abstractmethod

from .base import Repository
from ....domain import Minion


class MinionRepository(Repository[Minion]):
    """
    Repository interface for Minion entities
    
    Extends the base repository with Minion-specific operations.
    """
    
    @abstractmethod
    async def list_by_status(self, status: str, limit: int = 100, offset: int = 0) -> List[Minion]:
        """
        List minions by status
        
        Args:
            status: The status to filter by (active, inactive, etc.)
            limit: Maximum number of minions to return
            offset: Number of minions to skip
            
        Returns:
            List of minions with the specified status
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Minion]:
        """
        Get a minion by its name
        
        Args:
            name: The name of the minion
            
        Returns:
            The minion if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_by_expertise(self, expertise: str) -> List[Minion]:
        """
        List minions with a specific expertise
        
        Args:
            expertise: The expertise area to filter by
            
        Returns:
            List of minions with the specified expertise
        """
        pass