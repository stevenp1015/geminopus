"""
Domain Models for Gemini Legion

This package contains all core domain entities and value objects.
"""

from .base_types import EntityType
from .mood import MoodVector
from .opinion import OpinionEvent, OpinionScore
from .emotional_state import (
    ResponseTendency,
    ConversationStyle,
    ReflectionEntry,
    GoalPriority,
    RelationshipGraph,
    EmotionalState,
    EmotionalStateUpdate
)
from .memory import MemoryType, Experience, WorkingMemory
from .minion import MinionPersona, MinionStatus, Minion
from .communication import MessageType, Message, Channel, ChannelType, ChannelRole, ChannelMember
from .task import (
    TaskStatus, TaskPriority, Task, TaskResult,
    TaskOrchestrationStrategy, SubTask, TaskDecomposition, TaskAssignment
)

__all__ = [
    # Base types
    'EntityType',
    
    # Mood
    'MoodVector',
    
    # Opinion
    'OpinionEvent',
    'OpinionScore',
    
    # Emotional state
    'ResponseTendency',
    'ConversationStyle',
    'ReflectionEntry', 
    'GoalPriority',
    'RelationshipGraph',
    'EmotionalState',
    'EmotionalStateUpdate',
    
    # Memory
    'MemoryType',
    'Experience',
    'WorkingMemory',
    
    # Minion
    'MinionPersona',
    'MinionStatus',
    'Minion',
    
    # Communication
    'MessageType',
    'Message',
    'Channel',
    'ChannelType',
    'ChannelRole',
    'ChannelMember',
    
    # Task
    'TaskStatus',
    'TaskPriority',
    'Task',
    'TaskResult',
    'TaskOrchestrationStrategy',
    'SubTask',
    'TaskDecomposition',
    'TaskAssignment',
]
