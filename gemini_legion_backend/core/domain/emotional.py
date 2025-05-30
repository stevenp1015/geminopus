"""
Emotional State Domain Models - Base Types

This module implements the structured emotional state management system for Minions,
moving beyond diary-parsing to robust, structured emotional state representation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class EntityType(Enum):
    """Types of entities that can be tracked in opinion scores"""
    USER = "user"
    MINION = "minion"
    CONCEPT = "concept"
    TASK = "task"


@dataclass
class MoodVector:
    """
    Multi-dimensional mood representation
    
    Primary dimensions based on the VAD (Valence-Arousal-Dominance) model,
    with additional dimensions for nuanced personality expression.
    """
    # Primary dimensions (VAD model)
    valence: float  # Positive-Negative (-1.0 to 1.0)
    arousal: float  # Calm-Excited (0.0 to 1.0)
    dominance: float  # Submissive-Dominant (0.0 to 1.0)
    
    # Secondary dimensions for personality richness
    curiosity: float = 0.5  # 0.0 to 1.0
    creativity: float = 0.5  # 0.0 to 1.0
    sociability: float = 0.5  # 0.0 to 1.0
    
    def to_prompt_modifier(self) -> str:
        """
        Convert mood vector to natural language prompt instructions
        
        Returns:
            String containing mood-based behavioral instructions for the LLM
        """
        modifiers = []
        
        # Valence modifiers
        if self.valence > 0.5:
            modifiers.append("Respond with enthusiasm and positivity")
        elif self.valence < -0.5:
            modifiers.append("Express mild frustration or disappointment appropriately")
