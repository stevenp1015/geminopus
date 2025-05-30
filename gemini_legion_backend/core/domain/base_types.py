"""
Base types for emotional state domain
"""

from enum import Enum


class EntityType(Enum):
    """Types of entities that can be tracked in opinion scores"""
    USER = "user"
    MINION = "minion"
    CONCEPT = "concept"
    TASK = "task"
