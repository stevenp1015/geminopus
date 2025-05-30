"""
Memory Domain Models for Minions

Implements multi-layered memory system for true learning and adaptation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class MemoryType(Enum):
    """Types of memories in the system"""
    WORKING = "working"
    SHORT_TERM = "short_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class Experience:
    """Represents a single experience to be stored in memory"""
    timestamp: datetime
    content: str
    context: Dict[str, Any]
    significance: float  # 0.0 to 1.0
    emotional_impact: float  # -1.0 to 1.0
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_significant(self) -> bool:
        """Check if experience is significant enough for long-term storage"""
        return self.significance > 0.5 or abs(self.emotional_impact) > 0.7


@dataclass
class WorkingMemory:
    """Immediate context - follows Miller's Law (7±2 items)"""
    capacity: int = 7
    items: List[Experience] = field(default_factory=list)
    
    def add(self, experience: Experience):
        """Add item to working memory, removing oldest if at capacity"""
        self.items.append(experience)
        if len(self.items) > self.capacity:
            self.items.pop(0)
