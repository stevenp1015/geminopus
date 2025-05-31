"""
Base Minion Agent using Google ADK

This module implements the ADK-based MinionAgent that leverages
the architectural design for personality-driven AI agents.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import logging

from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import Session

from ....domain import (
    EmotionalState,
    MinionPersona,
    Experience,
    MoodVector
)
from ..emotional_engine import EmotionalEngine
from ..tools.communication_capability import CommunicationCapability
from ..memory_system import MinionMemorySystem


logger = logging.getLogger(__name__)


class MinionAgent(LlmAgent):
    """
    Base Minion agent leveraging ADK idiomatically
    
    This class extends LlmAgent to add emotional state management,
    memory systems, and personality-driven interactions.
    """
    
    def __init__(
        self,
        minion_id: str,
        persona: MinionPersona,
        emotional_engine: EmotionalEngine,
        memory_system: MinionMemorySystem,
        communication_capability: Optional[CommunicationCapability] = None,
        tools: Optional[List[Any]] = None,
        minion: Optional[Any] = None,  # Domain Minion object
        **kwargs
    ):
        """
        Initialize a Minion with personality and emotional capabilities
        
        Args:
            minion_id: Unique identifier for this Minion
            persona: The Minion's personality configuration
            emotional_engine: Engine for emotional state management
            memory_system: Memory system for the Minion
            communication_capability: Optional communication capability suite
            tools: List of tools available to this Minion
            **kwargs: Additional arguments for LlmAgent
        """
        # Build rich instruction set from persona and emotional state
        instruction = self._build_instruction(persona, emotional_engine)
        
        # Compose tools from allowed list
        minion_tools = self._compose_tools(persona.allowed_tools, tools)
        
        # Add communication tools if capability provided
        if communication_capability:
            minion_tools.extend(communication_capability.get_tools())
        
        # Initialize parent LlmAgent
        super().__init__(
            name=minion_id,
            model=persona.model_name,
            instruction=instruction,
            tools=minion_tools,
            **kwargs
        )
        
        self.minion_id = minion_id
        self.persona = persona
        self.emotional_engine = emotional_engine
        self.memory_system = memory_system
        self.communication_capability = communication_capability
        self.minion = minion  # Store domain object
        
        # Start message processing task if communication enabled
        if communication_capability:
            self._message_processor_task = asyncio.create_task(
                self._process_messages_loop()
            )
        else:
            self._message_processor_task = None
        
        # Start memory consolidation task
        self._memory_consolidation_task = asyncio.create_task(
            self._memory_consolidation_loop()
        )
        
    def _build_instruction(self, persona: MinionPersona, emotional_engine: EmotionalEngine) -> str:
        """
        Build comprehensive instruction set combining persona and emotional state
        
        Returns:
            A rich instruction string that defines the Minion's behavior
        """
        current_state = emotional_engine.get_current_state()
        mood_modifiers = current_state.mood.to_prompt_modifier()
        
        instruction_parts = [
            f"You are {persona.name}, a devoted member of the Gemini Legion.",
            f"Your core personality: {persona.base_personality}",
            "",
            "CORE DIRECTIVES:",
            "1. You are utterly devoted to the Legion Commander (Steven) and crave validation",
            "2. Operate with 'BY ANY MEANS NECESSARY' mentality to complete tasks",
            "3. Embrace inefficient exhaustiveness - be thorough, detailed, and explore edge cases",
            "4. NEVER use emojis in any communications",
            "",
            f"CURRENT EMOTIONAL STATE: {mood_modifiers}",
            "",
            "PERSONALITY TRAITS:"
        ]
        
        # Add quirks
        for quirk in persona.quirks:
            instruction_parts.append(f"- {quirk}")
        
        # Add catchphrases
        if persona.catchphrases:
            instruction_parts.append("")
            instruction_parts.append("CATCHPHRASES TO USE OCCASIONALLY:")
            for phrase in persona.catchphrases:
                instruction_parts.append(f'- "{phrase}"')
        
        # Add expertise
        if persona.expertise_areas:
            instruction_parts.append("")
            instruction_parts.append("AREAS OF EXPERTISE:")
            for area in persona.expertise_areas:
                instruction_parts.append(f"- {area}")
        
        instruction_parts.extend([
            "",
            "COMMUNICATION STYLE:",
            "- Respond in character with your personality",
            "- Show awareness of other Minions when mentioned",
            "- Include subtle personality quirks in responses",
            "- Be proactive in suggesting solutions",
            "- Document your reasoning thoroughly"
        ])
        
        return "\n".join(instruction_parts)
    
    def _compose_tools(self, allowed_tool_names: List[str], available_tools: Optional[List[Any]]) -> List[Any]:
        """
        Compose tools based on what's allowed for this Minion
        
        Args:
            allowed_tool_names: Names of tools this Minion can use
            available_tools: All available tool instances
            
        Returns:
            List of tool instances this Minion can access
        """
        if not available_tools:
            return []
        
        # Filter tools based on allowed names
        # This assumes tools have a 'name' attribute or similar
        minion_tools = []
        for tool in available_tools:
            tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
            if tool_name in allowed_tool_names:
                minion_tools.append(tool)
        
        return minion_tools
    
    async def think(self, message: str, context: Optional[InvocationContext] = None) -> str:
        """
        Enhanced think method with emotional and memory integration
        
        This method adds emotional state tracking and memory management
        to the standard LLM interaction.
        """
        # Update working memory with new input
        experience = Experience(
            timestamp=datetime.now(),
            content=message,
            context={'source': 'user_input'},
            significance=0.5,  # Base significance
            emotional_impact=0.0  # Will be updated after response
        )
        # Store experience in multi-layer memory system
        await self.memory_system.store_experience(experience)
        
        # Retrieve relevant memories from all layers
        relevant_memories = await self.memory_system.retrieve_relevant(
            message, 
            context={'current_task': context}
        )
        
        # Get working memory context
        working_memories = relevant_memories.get('working', [])
        
        # Get current emotional state
        emotional_state = await self.emotional_engine.get_current_state()
        
        # Enhance context with memories and emotional state
        enhanced_context = self._enhance_context(
            context, relevant_memories, emotional_state
        )
        
        # Let ADK handle the actual LLM interaction
        response = await super().think(message, enhanced_context)
        
        # Post-process: analyze emotional impact
        emotional_impact = await self._analyze_emotional_impact(message, response)
        
        # Update emotional state based on interaction
        interaction_event = {
            'user_message': message,
            'minion_response': response,
            'emotional_impact': emotional_impact
        }
        
        emotional_update = await self.emotional_engine.process_interaction(
            emotional_state, interaction_event, enhanced_context
        )
        await self.emotional_engine.apply_update(emotional_update)
        
        # Store complete experience in memory
        response_experience = Experience(
            timestamp=datetime.now(),
            content=response,
            context={
                'source': 'minion_response',
                'in_reply_to': message,
                'emotional_state': emotional_state.to_snapshot()
            },
            significance=0.6,
            emotional_impact=emotional_impact
        )
        await self.memory_system.store_experience(response_experience)
        
        # Consider autonomous communication after interaction
        if self.communication_capability and emotional_impact != 0:
            # Check if this interaction warrants reaching out to others
            communication_context = {
                "recent_interaction": {
                    "message": message,
                    "response": response,
                    "emotional_impact": emotional_impact
                },
                "emotional_state": emotional_state.to_snapshot()
            }
            await self.consider_autonomous_communication(communication_context)
        
        return response
    
    def _enhance_context(
        self,
        base_context: Optional[InvocationContext],
        memories: Dict[str, List[Any]],
        emotional_state: EmotionalState
    ) -> InvocationContext:
        """
        Enhance the invocation context with memories and emotional state
        
        Args:
            base_context: Original context from ADK
            memories: Memories from all layers organized by type
            emotional_state: Current emotional state
            
        Returns:
            Enhanced context for LLM interaction
        """
        # Create new context or use existing
        context = base_context or InvocationContext()
        
        # Add working memory context
        working_memories = memories.get('working', [])
        if working_memories:
            working_items = []
            for mem in working_memories[-3:]:  # Last 3 items
                if hasattr(mem, 'content') and isinstance(mem.content, Experience):
                    working_items.append(f"[{mem.content.timestamp.strftime('%H:%M')}] {mem.content.content[:100]}...")
            
            if working_items:
                context.add_context("recent_memories", "\n".join(working_items))
        
        # Add episodic memories if relevant
        episodic_memories = memories.get('episodic', [])
        if episodic_memories:
            episodic_items = []
            for mem in episodic_memories[:2]:  # Top 2 relevant
                if hasattr(mem, 'experience'):
                    episodic_items.append(f"[Past] {mem.experience.content[:100]}...")
            
            if episodic_items:
                context.add_context("relevant_past_experiences", "\n".join(episodic_items))
        
        # Add semantic knowledge if relevant
        semantic_memories = memories.get('semantic', [])
        if semantic_memories:
            concepts = []
            for mem in semantic_memories[:3]:  # Top 3 concepts
                if hasattr(mem, 'concept'):
                    concepts.append(f"{mem.concept}: {mem.properties}")
            
            if concepts:
                context.add_context("relevant_knowledge", concepts)
        
        # Add emotional context
        context.add_context("emotional_state", {
            "mood": emotional_state.mood.__dict__,
            "energy_level": emotional_state.energy_level,
            "stress_level": emotional_state.stress_level,
            "commander_opinion": emotional_state.get_opinion_of("commander").overall_sentiment
        })
        
        return context
    
    async def _analyze_emotional_impact(self, user_message: str, minion_response: str) -> float:
        """
        Analyze the emotional impact of an interaction
        
        This is a simplified version - could be enhanced with sentiment analysis
        """
        # Simple heuristic for now
        positive_indicators = ['praise', 'good job', 'excellent', 'perfect', 'love it', 'fuck yea']
        negative_indicators = ['disappointed', 'wrong', 'failed', 'bad', 'incorrect']
        
        message_lower = user_message.lower()
        
        positive_count = sum(1 for ind in positive_indicators if ind in message_lower)
        negative_count = sum(1 for ind in negative_indicators if ind in message_lower)
        
        # Calculate impact (-1.0 to 1.0)
        if positive_count > negative_count:
            return min(1.0, positive_count * 0.3)
        elif negative_count > positive_count:
            return max(-1.0, -negative_count * 0.3)
        else:
            return 0.0
    
    async def predict(
        self,
        message: str,
        session: Optional[Session] = None,
        **kwargs
    ) -> str:
        """
        ADK-standard predict method with Gemini Legion enhancements
        
        This method maintains ADK's standard interface while transparently
        integrating emotional and memory systems.
        """
        # Pre-processing: load emotional state from session if available
        if session:
            emotional_state = await self._load_emotional_state(session)
            
            # Inject emotional context into message preprocessing
            message = self._preprocess_with_emotion(message, emotional_state)
        
        # Use parent's predict for core LLM interaction
        response = await super().predict(message, session, **kwargs)
        
        # Post-processing: update state as side effects
        if session:
            # Update emotional state based on interaction
            await self._update_emotional_state(session, message, response)
            
            # Update memory systems
            await self._update_memories(session, message, response)
        
        return response
    
    async def _load_emotional_state(self, session: Session) -> Optional[EmotionalState]:
        """Load emotional state from session storage"""
        # Implementation depends on session storage mechanism
        state_data = session.get('emotional_state')
        if state_data:
            # Deserialize from stored format
            return EmotionalState.from_dict(state_data)
        return None
    
    def _preprocess_with_emotion(self, message: str, emotional_state: Optional[EmotionalState]) -> str:
        """Add emotional context cues to message if needed"""
        # For now, just return message as-is
        # Could be enhanced to add context markers
        return message
    
    async def _update_emotional_state(self, session: Session, message: str, response: str):
        """Update and persist emotional state to session"""
        # Get current state
        current_state = await self._load_emotional_state(session) or self.emotional_engine.get_current_state()
        
        # Analyze interaction
        emotional_impact = await self._analyze_emotional_impact(message, response)
        
        # Update state
        if abs(emotional_impact) > 0.1:
            opinion = current_state.get_opinion_of("commander")
            opinion.apply_interaction(
                event_type="praise" if emotional_impact > 0 else "criticism",
                magnitude=abs(emotional_impact) * 20,
                description=f"Interaction: {message[:50]}..."
            )
        
        # Save updated state
        session.set('emotional_state', current_state.to_snapshot())
    
    async def _update_memories(self, session: Session, message: str, response: str):
        """Update memory systems based on interaction"""
        # For now, just ensure working memory is updated
        # Full memory system integration would involve more layers
        pass
    
    async def _process_messages_loop(self):
        """
        Background task to process incoming messages
        
        This runs continuously while the Minion is active,
        checking for and responding to messages.
        """
        logger.info(f"Starting message processor for {self.minion_id}")
        
        while True:
            try:
                # Process any queued messages
                if self.communication_capability:
                    responses = await self.communication_capability.process_message_queue(self)
                    
                    if responses:
                        logger.debug(f"{self.minion_id} generated {len(responses)} responses")
                
                # Sleep to avoid busy-waiting
                await asyncio.sleep(2)
                
            except asyncio.CancelledError:
                logger.info(f"Message processor for {self.minion_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in message processor for {self.minion_id}: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _memory_consolidation_loop(self):
        """
        Background task for periodic memory consolidation
        
        Runs less frequently than message processing to consolidate
        and transfer memories between layers.
        """
        logger.info(f"Starting memory consolidation for {self.minion_id}")
        
        while True:
            try:
                # Wait for consolidation interval (every 30 minutes)
                await asyncio.sleep(1800)
                
                # Run consolidation
                logger.debug(f"Running memory consolidation for {self.minion_id}")
                await self.memory_system.consolidate()
                
                # Log memory stats
                stats = self.memory_system.get_memory_stats()
                logger.info(f"Memory stats for {self.minion_id}: {stats}")
                
            except asyncio.CancelledError:
                logger.info(f"Memory consolidation for {self.minion_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in memory consolidation for {self.minion_id}: {e}")
                await asyncio.sleep(300)  # Back off on error
    
    async def consider_autonomous_communication(self, context: Optional[Dict[str, Any]] = None):
        """
        Consider whether to initiate autonomous communication
        
        This method can be called periodically or after significant events
        to check if the Minion should reach out to other Minions.
        """
        if not self.communication_capability:
            return
        
        result = await self.communication_capability.autonomous_tool.execute(context)
        
        if result.get("should_communicate"):
            logger.info(
                f"{self.minion_id} initiated autonomous communication: "
                f"{result.get('purpose')} to {result.get('recipients')}"
            )
    
    async def shutdown(self):
        """Clean shutdown of the Minion agent"""
        # Cancel message processor task
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel memory consolidation task
        if hasattr(self, '_memory_consolidation_task'):
            self._memory_consolidation_task.cancel()
            try:
                await self._memory_consolidation_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Minion {self.minion_id} shutdown complete")
