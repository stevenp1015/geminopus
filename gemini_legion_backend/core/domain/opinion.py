"""
Opinion tracking system for Minions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .base_types import EntityType


@dataclass
class OpinionEvent:
    """Records a significant event that shaped an opinion"""
    timestamp: datetime
    event_type: str  # "praise", "criticism", "collaboration", "conflict"
    description: str
    impact_magnitude: float  # -100 to 100


@dataclass  
class OpinionScore:
    """Structured opinion about an entity"""
    entity_id: str
    entity_type: EntityType
    
    # Core opinion metrics (-100 to 100 scale)
    trust: float = 50.0
    respect: float = 50.0
    affection: float = 50.0
    
    # Interaction tracking
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    notable_events: List[OpinionEvent] = field(default_factory=list)
    
    @property
    def overall_sentiment(self) -> float:
        """Computed overall sentiment towards this entity"""
        return (self.trust + self.respect + self.affection) / 3
    
    def apply_interaction(self, event_type: str, magnitude: float, description: str = ""):
        """Apply an interaction event to update opinion scores"""
        # Update metrics based on event type
        if event_type == "praise":
            self.trust += magnitude * 0.3
            self.respect += magnitude * 0.5
            self.affection += magnitude * 0.7
        elif event_type == "criticism":
            self.trust += magnitude * 0.5
            self.respect += magnitude * 0.3
            self.affection += magnitude * 0.2
        elif event_type == "collaboration":
            self.trust += magnitude * 0.7
            self.respect += magnitude * 0.5
            self.affection += magnitude * 0.4
        elif event_type == "conflict":
            self.trust += magnitude * 0.8
            self.respect += magnitude * 0.4
            self.affection += magnitude * 0.6
        
        # Clamp values to valid range
        self.trust = max(-100, min(100, self.trust))
        self.respect = max(-100, min(100, self.respect))
        self.affection = max(-100, min(100, self.affection))
        
        # Update tracking
        self.interaction_count += 1
        self.last_interaction = datetime.now()
        
        # Record notable events (magnitude > 10)
        if abs(magnitude) > 10:
            self.notable_events.append(OpinionEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                description=description,
                impact_magnitude=magnitude
            ))
