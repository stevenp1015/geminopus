"""
Core Emotional State for Minions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any # Added Any
from dataclasses import asdict # Added asdict
from .base_types import EntityType
from .mood import MoodVector
from .opinion import OpinionScore, OpinionEvent # Added OpinionEvent
    

@dataclass
class ResponseTendency:
    """Defines how a Minion tends to respond based on emotional state"""
    verbosity: float = 0.5  # 0.0 (terse) to 1.0 (verbose)
    formality: float = 0.5  # 0.0 (casual) to 1.0 (formal)
    helpfulness: float = 0.8  # 0.0 (unhelpful) to 1.0 (eager to help)
    humor_usage: float = 0.3  # 0.0 (serious) to 1.0 (comedic)


@dataclass
class ConversationStyle:
    """Defines conversational preferences and patterns"""
    greeting_style: str = "professional"  # casual, professional, quirky
    sign_off_style: str = "standard"  # standard, affectionate, humorous
    emoji_usage: float = 0.0  # NEVER USE EMOJIS per requirements
    catchphrases: List[str] = field(default_factory=list)
    forbidden_topics: List[str] = field(default_factory=list)


@dataclass
class ReflectionEntry:
    """Meta-cognitive self-reflection notes"""
    timestamp: datetime
    topic: str
    insight: str
    confidence: float  # 0.0 to 1.0


@dataclass
class GoalPriority:
    """Represents a Minion's current goal priorities"""
    goal_id: str
    description: str
    priority_level: float  # 0.0 to 1.0
    deadline: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0


@dataclass
class RelationshipGraph:
    """Tracks relationships between entities in the Minion's world"""
    edges: Dict[tuple[str, str], float] = field(default_factory=dict)
    
    def add_relationship(self, entity1: str, entity2: str, strength: float):
        """Add or update a relationship between two entities"""
        key = tuple(sorted([entity1, entity2]))
        self.edges[key] = max(-1.0, min(1.0, strength))
    
    def get_relationship(self, entity1: str, entity2: str) -> float:
        """Get the strength of relationship between two entities"""
        key = tuple(sorted([entity1, entity2]))
        return self.edges.get(key, 0.0)


@dataclass
class EmotionalStateUpdate:
    """
    Represents a set of proposed changes to an EmotionalState.
    All fields are optional, indicating no change if not provided.
    """
    mood_delta: Optional[MoodVector] = None
    energy_delta: Optional[float] = None
    stress_delta: Optional[float] = None
    opinion_updates: Dict[str, Dict[str, float]] = field(default_factory=dict)
    new_reflection: Optional[ReflectionEntry] = None
    response_tendency_update: Optional[ResponseTendency] = None
    conversation_style_update: Optional[ConversationStyle] = None


@dataclass
class EmotionalState:
    """
    Core emotional state for a Minion
    
    Central state object that replaces diary-based emotion tracking
    with structured, observable, and modifiable state system.
    """
    minion_id: str
    
    # Core emotional metrics
    mood: MoodVector
    energy_level: float = 0.7  # 0.0 to 1.0
    stress_level: float = 0.3  # 0.0 to 1.0
    
    # Relationship tracking
    opinion_scores: Dict[str, OpinionScore] = field(default_factory=dict)
    relationship_graph: RelationshipGraph = field(default_factory=RelationshipGraph)
    
    # Behavioral modifiers
    response_tendency: ResponseTendency = field(default_factory=ResponseTendency)
    conversation_style: ConversationStyle = field(default_factory=ConversationStyle)
    
    # Meta-cognitive state
    self_reflection_notes: List[ReflectionEntry] = field(default_factory=list)
    goal_priorities: List[GoalPriority] = field(default_factory=list)
    
    # Temporal tracking
    last_updated: datetime = field(default_factory=datetime.now)
    state_version: int = 1
    
    def get_opinion_of(self, entity_id: str) -> OpinionScore:
        """Get opinion score for an entity, creating if necessary"""
        if entity_id not in self.opinion_scores:
            # Determine entity type (simplified for now)
            entity_type = EntityType.USER if entity_id == "commander" else EntityType.MINION
            self.opinion_scores[entity_id] = OpinionScore(
                entity_id=entity_id,
                entity_type=entity_type
            )
        return self.opinion_scores[entity_id]
    
    def to_snapshot(self) -> dict:
        """Create a serializable snapshot of the emotional state"""
        return {
            "minion_id": self.minion_id,
            "mood": {
                "valence": self.mood.valence,
                "arousal": self.mood.arousal,
                "dominance": self.mood.dominance,
                "curiosity": self.mood.curiosity,
                "creativity": self.mood.creativity,
                "sociability": self.mood.sociability
            },
            "energy_level": self.energy_level,
            "stress_level": self.stress_level,
            "opinion_scores": {
                entity_id: {
                    "entity_type": score.entity_type.value if score.entity_type else None, # Assuming EntityType is an Enum
                    "trust": score.trust,
                    "respect": score.respect,
                    "affection": score.affection,
                    "interaction_count": score.interaction_count,
                    "last_interaction_timestamp": score.last_interaction.isoformat() if score.last_interaction else None,
                    "notable_events": [asdict(event) for event in score.notable_events],
                    "overall_sentiment": score.overall_sentiment # This is a property, will be computed
                }
                for entity_id, score in self.opinion_scores.items()
            },
            "last_updated": self.last_updated.isoformat(),
            "state_version": self.state_version
        }
    
    def apply_stress(self, stress_delta: float):
        """Apply stress change and propagate effects"""
        self.stress_level = max(0.0, min(1.0, self.stress_level + stress_delta))
        
        # Stress affects mood
        if self.stress_level > 0.7:
            self.mood.valence -= 0.1
            self.mood.arousal += 0.1
            self.energy_level -= 0.05
        
        self.last_updated = datetime.now()
        self.state_version += 1
