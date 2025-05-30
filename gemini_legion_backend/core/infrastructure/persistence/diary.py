"""
Personal Diary System

Rich narrative logs that supplement structured emotional state,
providing searchable context and personality depth.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class DiaryEntryType(Enum):
    """Types of diary entries"""
    REFLECTION = "reflection"
    INTERACTION = "interaction"
    TASK_COMPLETION = "task_completion"
    EMOTIONAL_EVENT = "emotional_event"
    LEARNING = "learning"
    SYSTEM = "system"


@dataclass
class DiaryEntry:
    """A single diary entry with full context"""
    minion_id: str
    timestamp: datetime
    entry_type: DiaryEntryType
    content: str
    emotional_snapshot: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'minion_id': self.minion_id,
            'timestamp': self.timestamp.isoformat(),
            'entry_type': self.entry_type.value,
            'content': self.content,
            'emotional_snapshot': self.emotional_snapshot,
            'metadata': self.metadata,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiaryEntry':
        """Create from dictionary"""
        return cls(
            minion_id=data['minion_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            entry_type=DiaryEntryType(data['entry_type']),
            content=data['content'],
            emotional_snapshot=data['emotional_snapshot'],
            metadata=data.get('metadata', {}),
            tags=data.get('tags', [])
        )


class PersonalDiary:
    """
    Rich narrative log supplementing structured emotional state
    
    Provides a searchable, narrative record of a Minion's experiences
    and thoughts, complementing the structured emotional state.
    """
    
    def __init__(self, minion_id: str, storage_path: Optional[str] = None):
        """
        Initialize diary for a specific Minion
        
        Args:
            minion_id: The Minion this diary belongs to
            storage_path: Optional path for persistent storage
        """
        self.minion_id = minion_id
        self.storage_path = storage_path
        self.entries: List[DiaryEntry] = []
        
        # Load existing entries if storage path provided
        if storage_path:
            self._load_entries()
    
    async def record_entry(
        self,
        entry_type: DiaryEntryType,
        content: str,
        emotional_state: 'EmotionalState',
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> DiaryEntry:
        """
        Record a new diary entry
        
        Args:
            entry_type: Type of entry being recorded
            content: The narrative content
            emotional_state: Current emotional state for snapshot
            metadata: Additional metadata
            tags: Tags for searchability
            
        Returns:
            The created diary entry
        """
        entry = DiaryEntry(
            minion_id=self.minion_id,
            timestamp=datetime.now(),
            entry_type=entry_type,
            content=content,
            emotional_snapshot=emotional_state.to_snapshot(),
            metadata=metadata or {},
            tags=tags or []
        )
        
        self.entries.append(entry)
        
        # Persist if storage configured
        if self.storage_path:
            self._save_entry(entry)
        
        return entry
    
    async def search_memories(
        self,
        query: str,
        entry_type: Optional[DiaryEntryType] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        limit: int = 10
    ) -> List[DiaryEntry]:
        """
        Search through diary entries
        
        Args:
            query: Search query (matched against content)
            entry_type: Filter by entry type
            time_range: Filter by time range (start, end)
            limit: Maximum number of results
            
        Returns:
            List of matching diary entries
        """
        results = []
        
        for entry in reversed(self.entries):  # Most recent first
            # Type filter
            if entry_type and entry.entry_type != entry_type:
                continue
            
            # Time filter
            if time_range:
                start, end = time_range
                if not (start <= entry.timestamp <= end):
                    continue
            
            # Content search (simple substring for now)
            if query.lower() in entry.content.lower():
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent_entries(self, count: int = 5) -> List[DiaryEntry]:
        """Get the most recent diary entries"""
        return self.entries[-count:] if self.entries else []
    
    def _load_entries(self):
        """Load entries from storage"""
        try:
            with open(f"{self.storage_path}/{self.minion_id}_diary.json", 'r') as f:
                data = json.load(f)
                self.entries = [DiaryEntry.from_dict(entry) for entry in data]
        except FileNotFoundError:
            # No existing diary, start fresh
            self.entries = []
    
    def _save_entry(self, entry: DiaryEntry):
        """Save a single entry to storage"""
        # In production, this would append to a database
        # For now, we'll save the entire diary
        all_entries = [e.to_dict() for e in self.entries]
        with open(f"{self.storage_path}/{self.minion_id}_diary.json", 'w') as f:
            json.dump(all_entries, f, indent=2)
