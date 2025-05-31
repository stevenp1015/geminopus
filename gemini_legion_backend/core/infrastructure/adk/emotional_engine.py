"""
Emotional Policy Engine

Translates LLM outputs to emotional state changes, moving beyond
diary parsing to structured state management.
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
import json
from enum import Enum

from google.adk.agents import LlmAgent

from ...domain import (
    EmotionalState,
    EmotionalStateUpdate,
    MoodVector,
    ReflectionEntry,
    Minion,
    OpinionEvent,
    ResponseTendency,
    ConversationStyle,
    OpinionScore,
    EntityType
)


logger = logging.getLogger(__name__)


class EmotionalValidationError(Exception):
    """Raised when emotional state validation fails"""
    pass


class EmotionalStateValidator:
    """
    Validates and constrains emotional state updates
    
    Ensures emotional changes are realistic and within bounds.
    """
    
    # Maximum allowed changes per update
    MAX_MOOD_DELTA = 0.3
    MAX_ENERGY_DELTA = 0.2
    MAX_STRESS_DELTA = 0.2
    MAX_OPINION_DELTA = 20.0
    
    def validate(
        self,
        current_state: EmotionalState,
        proposed_update: EmotionalStateUpdate
    ) -> EmotionalStateUpdate:
        """
        Validate and constrain a proposed emotional update
        
        Args:
            current_state: Current emotional state
            proposed_update: Proposed changes
            
        Returns:
            Validated and constrained update
            
        Raises:
            EmotionalValidationError: If update is invalid
        """
        validated = EmotionalStateUpdate()
        
        # Validate mood changes
        if proposed_update.mood_delta:
            validated.mood_delta = self._constrain_mood_delta(
                proposed_update.mood_delta
            )
        
        # Validate energy changes
        if proposed_update.energy_delta is not None:
            validated.energy_delta = self._constrain_scalar(
                proposed_update.energy_delta,
                self.MAX_ENERGY_DELTA,
                current_state.energy_level
            )
        
        # Validate stress changes
        if proposed_update.stress_delta is not None:
            validated.stress_delta = self._constrain_scalar(
                proposed_update.stress_delta,
                self.MAX_STRESS_DELTA,
                current_state.stress_level
            )
        
        # Validate opinion changes
        for entity_id, deltas in proposed_update.opinion_updates.items():
            validated_deltas = {}
            
            for metric, delta in deltas.items():
                if metric not in ["trust", "respect", "affection"]:
                    raise EmotionalValidationError(
                        f"Invalid opinion metric: {metric}"
                    )
                
                # Constrain delta
                constrained = max(-self.MAX_OPINION_DELTA, 
                                min(self.MAX_OPINION_DELTA, delta))
                
                # Special rule: Commander opinion can't go below 50
                if entity_id == "commander":
                    current_opinion = current_state.get_opinion_of("commander")
                    current_value = getattr(current_opinion, metric)
                    if current_value + constrained < 50.0:
                        constrained = 50.0 - current_value
                
                validated_deltas[metric] = constrained
            
            validated.opinion_updates[entity_id] = validated_deltas
        
        # Pass through other updates
        validated.new_reflection = proposed_update.new_reflection
        validated.response_tendency_update = proposed_update.response_tendency_update
        validated.conversation_style_update = proposed_update.conversation_style_update
        
        return validated
    
    def _constrain_mood_delta(self, mood_delta: MoodVector) -> MoodVector:
        """Constrain mood changes to realistic bounds"""
        return MoodVector(
            valence=self._clamp(mood_delta.valence, self.MAX_MOOD_DELTA),
            arousal=self._clamp(mood_delta.arousal, self.MAX_MOOD_DELTA),
            dominance=self._clamp(mood_delta.dominance, self.MAX_MOOD_DELTA),
            curiosity=self._clamp(mood_delta.curiosity, self.MAX_MOOD_DELTA),
            creativity=self._clamp(mood_delta.creativity, self.MAX_MOOD_DELTA),
            sociability=self._clamp(mood_delta.sociability, self.MAX_MOOD_DELTA)
        )
    
    def _constrain_scalar(
        self,
        delta: float,
        max_delta: float,
        current_value: float
    ) -> float:
        """Constrain scalar changes"""
        # Limit magnitude
        constrained = self._clamp(delta, max_delta)
        
        # Ensure result stays in [0, 1]
        new_value = current_value + constrained
        if new_value < 0:
            constrained = -current_value
        elif new_value > 1:
            constrained = 1 - current_value
        
        return constrained
    
    def _clamp(self, value: float, max_abs: float) -> float:
        """Clamp value to [-max_abs, max_abs]"""
        return max(-max_abs, min(max_abs, value))


class EmotionalPolicyEngine:
    """
    Translates LLM outputs to emotional state changes
    
    Uses the LLM as a policy engine to analyze interactions
    and propose structured emotional updates.
    """
    
    def __init__(self, llm_agent: LlmAgent):
        """
        Initialize with an LLM agent
        
        Args:
            llm_agent: The LLM agent to use for emotional analysis
        """
        self.llm_agent = llm_agent
        self.state_validator = EmotionalStateValidator()
    
    async def process_interaction(
        self,
        current_state: EmotionalState,
        interaction: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionalStateUpdate:
        """
        Generate proposed emotional state changes from interaction
        
        Args:
            current_state: Current emotional state
            interaction: Interaction details
            context: Additional context
            
        Returns:
            Validated emotional state update
        """
        # Build analysis prompt
        prompt = self._build_emotional_analysis_prompt(
            current_state, interaction, context
        )
        
        # Get LLM analysis
        response = await self.llm_agent.think(prompt)
        
        # Parse response to structured update
        proposed_update = self._parse_emotional_update(response)
        
        # Validate and constrain
        validated_update = self.state_validator.validate(
            current_state, proposed_update
        )
        
        return validated_update
    
    def _build_emotional_analysis_prompt(
        self,
        current_state: EmotionalState,
        interaction: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for emotional analysis"""
        
        mood_desc = current_state.mood.to_natural_language()
        
        prompt = f"""Analyze the emotional impact of this interaction on the Minion.

Current Emotional State:
- Mood: {mood_desc}
- Energy Level: {current_state.energy_level:.1f}
- Stress Level: {current_state.stress_level:.1f}
- Commander Opinion: {current_state.get_opinion_of('commander').overall_sentiment:.0f}/100

Interaction:
User Message: {interaction.get('user_message', 'N/A')}
Minion Response: {interaction.get('minion_response', 'N/A')}

Provide a structured emotional update in JSON format:
{{
    "mood_changes": {{
        "valence": <float between -0.3 and 0.3>,
        "arousal": <float between -0.3 and 0.3>,
        "curiosity": <float between -0.3 and 0.3>
    }},
    "energy_change": <float between -0.2 and 0.2>,
    "stress_change": <float between -0.2 and 0.2>,
    "opinion_changes": {{
        "commander": {{
            "trust": <float between -20 and 20>,
            "respect": <float between -20 and 20>,
            "affection": <float between -20 and 20>
        }}
    }},
    "reflection": "<optional insight about the interaction>",
    "reasoning": "<brief explanation of emotional changes>"
}}"""
        
        return prompt
    
    def _parse_emotional_update(self, llm_response: str) -> EmotionalStateUpdate:
        """Parse LLM response into structured update"""
        try:
            # Extract JSON from response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            json_str = llm_response[json_start:json_end]
            
            data = json.loads(json_str)
            
            update = EmotionalStateUpdate()
            
            # Parse mood changes
            if "mood_changes" in data:
                mood_changes = data["mood_changes"]
                update.mood_delta = MoodVector(
                    valence=mood_changes.get("valence", 0.0),
                    arousal=mood_changes.get("arousal", 0.0),
                    dominance=0.0,  # Keep dominance stable
                    curiosity=mood_changes.get("curiosity", 0.0),
                    creativity=0.0,  # Keep creativity stable
                    sociability=0.0  # Keep sociability stable
                )
            
            # Parse scalar changes
            update.energy_delta = data.get("energy_change", 0.0)
            update.stress_delta = data.get("stress_change", 0.0)
            
            # Parse opinion changes
            if "opinion_changes" in data:
                for entity_id, changes in data["opinion_changes"].items():
                    update.opinion_updates[entity_id] = changes
            
            # Parse reflection
            if "reflection" in data and data["reflection"]:
                update.new_reflection = ReflectionEntry(
                    timestamp=datetime.now(),
                    topic="Interaction Analysis",
                    insight=data["reflection"],
                    confidence=0.8
                )
            
            return update
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse LLM emotional update: {e}")
            # Return minimal update on parse failure
            return EmotionalStateUpdate()


class EmotionalEngine:
    """
    Comprehensive emotional engine for Minions
    
    Manages emotional state with validation, persistence,
    and LLM-based policy decisions.
    """
    
    def __init__(
        self,
        minion: Minion,
        policy_engine: Optional[EmotionalPolicyEngine] = None
    ):
        """
        Initialize emotional engine
        
        Args:
            minion: The Minion this engine manages
            policy_engine: Optional custom policy engine
        """
        self.minion = minion
        self._current_state = minion.emotional_state
        self._state_history: List[EmotionalState] = []
        self._max_history = 100
        
        self.policy_engine = policy_engine
        self.state_validator = EmotionalStateValidator()
        
        # Track emotional momentum
        self._momentum = {
            "valence": 0.0,
            "arousal": 0.0,
            "stress": 0.0
        }
    
    def get_current_state(self) -> EmotionalState:
        """Get current emotional state"""
        return self._current_state
    
    async def process_interaction(
        self,
        interaction_event: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionalStateUpdate:
        """
        Process interaction and generate emotional update
        
        Args:
            interaction_event: Details of the interaction
            context: Additional context
            
        Returns:
            Validated emotional state update
        """
        # Use policy engine if available
        if self.policy_engine:
            return await self.policy_engine.process_interaction(
                self._current_state, interaction_event, context
            )
        
        # Otherwise, use simple heuristics
        return self._heuristic_emotional_update(interaction_event)
    
    def _heuristic_emotional_update(
        self,
        interaction_event: Dict[str, Any]
    ) -> EmotionalStateUpdate:
        """Simple heuristic-based emotional update"""
        update = EmotionalStateUpdate()
        
        emotional_impact = interaction_event.get('emotional_impact', 0.0)
        
        if abs(emotional_impact) > 0.1:
            # Mood changes
            update.mood_delta = MoodVector(
                valence=emotional_impact * 0.2,
                arousal=abs(emotional_impact) * 0.1,
                dominance=0.0,
                curiosity=0.05 if emotional_impact > 0 else -0.05,
                creativity=0.0,
                sociability=0.1 if emotional_impact > 0 else -0.05
            )
            
            # Energy and stress
            if emotional_impact > 0.5:
                update.energy_delta = 0.1
                update.stress_delta = -0.05
            elif emotional_impact < -0.5:
                update.energy_delta = -0.05
                update.stress_delta = 0.1
            
            # Opinion changes
            update.opinion_updates["commander"] = {
                "trust": emotional_impact * 5,
                "respect": emotional_impact * 3,
                "affection": emotional_impact * 4
            }
        
        return update
    
    async def apply_update(self, update: EmotionalStateUpdate):
        """Apply validated emotional state update"""
        # Store previous state
        self._add_to_history(self._current_state.copy())
        
        # Apply mood changes with momentum
        if update.mood_delta:
            self._apply_mood_with_momentum(update.mood_delta)
        
        # Apply scalar changes
        if update.energy_delta is not None:
            self._current_state.energy_level = max(0.0, min(1.0,
                self._current_state.energy_level + update.energy_delta
            ))
        
        if update.stress_delta is not None:
            new_stress = self._current_state.stress_level + update.stress_delta
            self._current_state.stress_level = max(0.0, min(1.0, new_stress))
            
            # Update stress momentum
            self._momentum["stress"] = 0.7 * self._momentum["stress"] + 0.3 * update.stress_delta
        
        # Apply opinion changes
        for entity_id, deltas in update.opinion_updates.items():
            self._apply_opinion_changes(entity_id, deltas)
        
        # Add reflection
        if update.new_reflection:
            self._current_state.self_reflection_notes.append(update.new_reflection)
            self._prune_reflections()
        
        # Update style modifiers
        if update.response_tendency_update:
            self._current_state.response_tendency = update.response_tendency_update
        
        if update.conversation_style_update:
            self._current_state.conversation_style = update.conversation_style_update
        
        # Update metadata
        self._current_state.last_updated = datetime.now()
        self._current_state.state_version += 1
    
    def _apply_mood_with_momentum(self, mood_delta: MoodVector):
        """Apply mood changes considering momentum"""
        # Update momentum
        self._momentum["valence"] = 0.7 * self._momentum["valence"] + 0.3 * mood_delta.valence
        self._momentum["arousal"] = 0.7 * self._momentum["arousal"] + 0.3 * mood_delta.arousal
        
        # Apply with momentum
        effective_delta = MoodVector(
            valence=mood_delta.valence + 0.2 * self._momentum["valence"],
            arousal=mood_delta.arousal + 0.2 * self._momentum["arousal"],
            dominance=mood_delta.dominance,
            curiosity=mood_delta.curiosity,
            creativity=mood_delta.creativity,
            sociability=mood_delta.sociability
        )
        
        self._current_state.mood = self._current_state.mood.blend_with(
            effective_delta, weight=0.3
        )
    
    def _apply_opinion_changes(self, entity_id: str, deltas: Dict[str, float]):
        """Apply opinion changes for an entity"""
        if entity_id not in self._current_state.opinion_scores:
            # Create new opinion if doesn't exist
            self._current_state.opinion_scores[entity_id] = OpinionScore(
                entity_id=entity_id,
                entity_type=EntityType.USER if entity_id == "commander" else EntityType.MINION,
                trust=50.0,
                respect=50.0,
                affection=50.0,
                interaction_count=0,
                last_interaction=None,
                notable_events=[]
            )
        
        opinion = self._current_state.opinion_scores[entity_id]
        
        for metric, delta in deltas.items():
            current = getattr(opinion, metric)
            new_value = max(-100, min(100, current + delta))
            setattr(opinion, metric, new_value)
        
        # Update interaction tracking
        opinion.interaction_count += 1
        opinion.last_interaction = datetime.now()
        
        # Add notable event if significant change
        total_change = sum(abs(d) for d in deltas.values())
        if total_change > 30:
            event = OpinionEvent(
                timestamp=datetime.now(),
                event_type="significant_interaction",
                magnitude=total_change,
                description=f"Major opinion shift: {deltas}"
            )
            opinion.notable_events.append(event)
    
    def _add_to_history(self, state: EmotionalState):
        """Add state to history"""
        self._state_history.append(state)
        if len(self._state_history) > self._max_history:
            self._state_history.pop(0)
    
    def _prune_reflections(self):
        """Keep only recent reflections"""
        max_reflections = 20
        if len(self._current_state.self_reflection_notes) > max_reflections:
            self._current_state.self_reflection_notes = \
                self._current_state.self_reflection_notes[-max_reflections:]
    
    def get_emotional_trajectory(self, hours: int = 24) -> Dict[str, List[float]]:
        """
        Get emotional trajectory over time
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary of metric trajectories
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        trajectories = {
            "valence": [],
            "arousal": [],
            "energy": [],
            "stress": [],
            "commander_opinion": []
        }
        
        for state in self._state_history:
            if state.last_updated >= cutoff:
                trajectories["valence"].append(state.mood.valence)
                trajectories["arousal"].append(state.mood.arousal)
                trajectories["energy"].append(state.energy_level)
                trajectories["stress"].append(state.stress_level)
                trajectories["commander_opinion"].append(
                    state.get_opinion_of("commander").overall_sentiment
                )
        
        return trajectories
    
    async def autonomous_emotional_regulation(self):
        """
        Perform autonomous emotional regulation
        
        This method can be called periodically to allow the Minion
        to self-regulate extreme emotional states.
        """
        # Check for extreme states needing regulation
        needs_regulation = False
        regulation_update = EmotionalStateUpdate()
        
        # High stress regulation
        if self._current_state.stress_level > 0.8:
            needs_regulation = True
            regulation_update.stress_delta = -0.1
            regulation_update.new_reflection = ReflectionEntry(
                timestamp=datetime.now(),
                topic="Stress Management",
                insight="Taking a moment to center myself and reduce stress levels",
                confidence=0.9
            )
        
        # Low energy regulation
        if self._current_state.energy_level < 0.2:
            needs_regulation = True
            regulation_update.energy_delta = 0.1
            regulation_update.mood_delta = MoodVector(
                valence=0.1, arousal=0.1, dominance=0,
                curiosity=0, creativity=0, sociability=0
            )
        
        # Extreme mood regulation
        if abs(self._current_state.mood.valence) > 0.8:
            needs_regulation = True
            # Move toward neutral
            regulation_update.mood_delta = MoodVector(
                valence=-0.2 * self._current_state.mood.valence,
                arousal=0, dominance=0, curiosity=0,
                creativity=0, sociability=0
            )
        
        if needs_regulation:
            validated = self.state_validator.validate(
                self._current_state, regulation_update
            )
            await self.apply_update(validated)
            
            logger.info(f"Minion {self.minion.minion_id} performed emotional self-regulation")


from datetime import timedelta  # Add this import