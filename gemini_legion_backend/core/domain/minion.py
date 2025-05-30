"""
Minion Domain Model - Core entity representing an AI agent
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from .emotional_state import EmotionalState
from .memory import WorkingMemory


@dataclass
class MinionPersona:
    """Defines the core personality and configuration of a Minion"""
    name: str
    base_personality: str  # e.g., "grumpy hacker", "cheerful helper" 
    quirks: List[str] = field(default_factory=list)
    catchphrases: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    
    # Model configuration
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class MinionStatus:
    """Current operational status of a Minion"""
    is_active: bool = True
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    health_status: str = "operational"  # operational, degraded, error
    
    
@dataclass
class Minion:
    """Core Minion entity with personality, state, and memory"""
    minion_id: str
    persona: MinionPersona
    emotional_state: EmotionalState
    working_memory: WorkingMemory
    status: MinionStatus = field(default_factory=MinionStatus)
    creation_date: datetime = field(default_factory=datetime.now)
