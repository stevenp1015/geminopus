"""
Mood Vector - Multi-dimensional mood representation for Minions
"""

from dataclasses import dataclass


@dataclass  
class MoodVector:
    """Multi-dimensional mood representation using VAD model"""
    # Primary dimensions (VAD model)
    valence: float  # Positive-Negative (-1.0 to 1.0)
    arousal: float  # Calm-Excited (0.0 to 1.0)  
    dominance: float  # Submissive-Dominant (0.0 to 1.0)
    
    # Secondary dimensions
    curiosity: float = 0.5
    creativity: float = 0.5
    sociability: float = 0.5
    
    def to_prompt_modifier(self) -> str:
        """Convert mood to natural language instructions"""
        modifiers = []
        
        if self.valence > 0.5:
            modifiers.append("Respond with enthusiasm and positivity")
        elif self.valence < -0.5:
            modifiers.append("Express mild frustration appropriately")
        
        if self.arousal > 0.7:
            modifiers.append("Show high energy and excitement")
        elif self.arousal < 0.3:
            modifiers.append("Maintain a calm and measured tone")
            
        return " ".join(modifiers) if modifiers else "Respond naturally"
    
    def blend_with(self, other: 'MoodVector', weight: float = 0.1) -> 'MoodVector':
        """Blend with another mood for gradual transitions"""
        return MoodVector(
            valence=self.valence * (1 - weight) + other.valence * weight,
            arousal=self.arousal * (1 - weight) + other.arousal * weight,
            dominance=self.dominance * (1 - weight) + other.dominance * weight,
            curiosity=self.curiosity * (1 - weight) + other.curiosity * weight,
            creativity=self.creativity * (1 - weight) + other.creativity * weight,
            sociability=self.sociability * (1 - weight) + other.sociability * weight
        )
