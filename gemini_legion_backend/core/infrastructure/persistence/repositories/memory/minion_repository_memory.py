"""
Memory-based Minion Repository Implementation

In-memory implementation of MinionRepository for testing and development.
"""

from typing import List, Optional, Dict
from datetime import datetime
import asyncio
from copy import deepcopy

from ..minion_repository import MinionRepository
from .....domain import Minion, MinionStatus


class MinionRepositoryMemory(MinionRepository):
    """
    In-memory implementation of MinionRepository
    
    Stores minions in memory with efficient lookups by ID and status.
    """
    
    def __init__(self):
        """Initialize the in-memory storage"""
        self._minions: Dict[str, Minion] = {}
        self._lock = asyncio.Lock()
    
    async def save(self, entity: Minion) -> Minion:
        """
        Save or update a minion
        
        Args:
            entity: The minion to save
            
        Returns:
            The saved minion
        """
        async with self._lock:
            # Deep copy to avoid external modifications
            saved_minion = deepcopy(entity)
            
            self._minions[entity.minion_id] = saved_minion
            
            return deepcopy(saved_minion)
    
    async def get_by_id(self, entity_id: str) -> Optional[Minion]:
        """
        Get a minion by its ID
        
        Args:
            entity_id: The ID of the minion
            
        Returns:
            The minion if found, None otherwise
        """
        async with self._lock:
            minion = self._minions.get(entity_id)
            return deepcopy(minion) if minion else None
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Minion]:
        """
        List all minions with pagination
        
        Args:
            limit: Maximum number of minions to return
            offset: Number of minions to skip
            
        Returns:
            List of minions
        """
        async with self._lock:
            # Get all minions sorted by spawn time
            all_minions = sorted(
                self._minions.values(),
                key=lambda m: m.creation_date,
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(m) for m in all_minions[start:end]]
    
    async def delete(self, entity_id: str) -> bool:
        """
        Delete a minion by ID
        
        Args:
            entity_id: The ID of the minion to delete
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if entity_id in self._minions:
                del self._minions[entity_id]
                return True
            return False
    
    async def exists(self, entity_id: str) -> bool:
        """
        Check if a minion exists
        
        Args:
            entity_id: The ID of the minion
            
        Returns:
            True if exists, False otherwise
        """
        async with self._lock:
            return entity_id in self._minions
    
    async def list_by_status(
        self,
        status: MinionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[Minion]:
        """
        List minions by status
        
        Args:
            status: The status to filter by
            limit: Maximum number of minions to return
            offset: Number of minions to skip
            
        Returns:
            List of minions with the specified status
        """
        async with self._lock:
            # Filter by status
            filtered_minions = [
                m for m in self._minions.values()
                if m.status == status
            ]
            
            # Sort by last activity
            filtered_minions.sort(
                key=lambda m: m.last_activity or m.creation_date,
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(m) for m in filtered_minions[start:end]]
    
    async def get_by_name(self, name: str) -> Optional[Minion]:
        """
        Get a minion by its name
        
        Args:
            name: The name of the minion
            
        Returns:
            The minion if found, None otherwise
        """
        async with self._lock:
            for minion in self._minions.values():
                if minion.persona.name == name:
                    return deepcopy(minion)
            return None
    
    async def update_status(
        self,
        minion_id: str,
        status: MinionStatus
    ) -> Optional[Minion]:
        """
        Update a minion's status
        
        Args:
            minion_id: The ID of the minion
            status: The new status
            
        Returns:
            The updated minion if found, None otherwise
        """
        async with self._lock:
            minion = self._minions.get(minion_id)
            if not minion:
                return None
            
            minion.status = status
            minion.last_activity = datetime.now()
            
            return deepcopy(minion)
    
    async def update_emotional_state(
        self,
        minion_id: str,
        emotional_state_data: Dict
    ) -> Optional[Minion]:
        """
        Update a minion's emotional state
        
        Args:
            minion_id: The ID of the minion
            emotional_state_data: The new emotional state data
            
        Returns:
            The updated minion if found, None otherwise
        """
        async with self._lock:
            minion = self._minions.get(minion_id)
            if not minion:
                return None
            
            # Update emotional state from data
            # This would typically deserialize the data into EmotionalState
            # For now, we'll just update the timestamp
            minion.emotional_state.last_updated = datetime.now()
            minion.last_activity = datetime.now()
            
            return deepcopy(minion)
    
    async def list_by_expertise(self, expertise: str) -> List[Minion]:
        """
        List minions with a specific expertise
        
        Args:
            expertise: The expertise area to filter by
            
        Returns:
            List of minions with the specified expertise
        """
        async with self._lock:
            # Filter by expertise (case-insensitive)
            expertise_lower = expertise.lower()
            filtered_minions = [
                m for m in self._minions.values()
                if any(exp.lower() == expertise_lower for exp in m.persona.expertise)
            ]
            
            # Sort by last activity
            filtered_minions.sort(
                key=lambda m: m.last_activity or m.creation_date,
                reverse=True
            )
            
            return [deepcopy(m) for m in filtered_minions]
    
    async def clear(self):
        """Clear all minions from memory (for testing)"""
        async with self._lock:
            self._minions.clear()