"""
Minion Factory for creating fully-configured Minion agents

This module provides factory methods for creating Minions with
all necessary components properly configured.
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from pathlib import Path

from .minion_agent import MinionAgent
from ..emotional_engine import EmotionalEngine
from ..tools.communication_capability import CommunicationCapability
from ..tools.tool_integration import get_tool_manager
from ..memory_system import MinionMemorySystem
from ....domain import (
    Minion,
    MinionPersona,
    EmotionalState,
    MoodVector,
    Experience
)
from ...messaging.communication_system import InterMinionCommunicationSystem
from ...messaging.safeguards import CommunicationSafeguards


logger = logging.getLogger(__name__)


class MinionFactory:
    """
    Factory for creating properly configured Minion agents
    
    This class handles the complex initialization of Minions,
    ensuring all components are properly connected.
    """
    
    def __init__(
        self,
        comm_system: Optional[InterMinionCommunicationSystem] = None,
        safeguards: Optional[CommunicationSafeguards] = None,
        tool_config: Optional[Dict[str, Any]] = None,
        memory_storage_path: Optional[str] = None
    ):
        """
        Initialize the factory with shared infrastructure
        
        Args:
            comm_system: Shared communication system for all Minions
            safeguards: Shared communication safeguards
            tool_config: Configuration for tool integration
            memory_storage_path: Base path for storing Minion memories
        """
        self.comm_system = comm_system
        self.safeguards = safeguards
        self._minion_registry: Dict[str, MinionAgent] = {}
        self.memory_storage_path = memory_storage_path or "/tmp/gemini_legion/memories"
        
        # Initialize tool manager
        self.tool_manager = get_tool_manager(comm_system, safeguards, tool_config)
    
    async def create_minion(
        self,
        minion_id: str,
        name: str,
        base_personality: str,
        quirks: List[str],
        catchphrases: Optional[List[str]] = None,
        expertise_areas: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None,
        enable_communication: bool = True,
        initial_mood: Optional[MoodVector] = None,
        **kwargs
    ) -> MinionAgent:
        """
        Create a fully configured Minion agent
        
        Args:
            minion_id: Unique identifier for the Minion
            name: Display name of the Minion
            base_personality: Core personality description
            quirks: List of personality quirks
            catchphrases: Optional catchphrases
            expertise_areas: Areas of expertise
            allowed_tools: Tools this Minion can use
            enable_communication: Whether to enable communication capabilities
            initial_mood: Starting mood (defaults to neutral)
            **kwargs: Additional arguments for MinionAgent
            
        Returns:
            Configured MinionAgent instance
        """
        # Create persona
        persona = MinionPersona(
            minion_id=minion_id,
            name=name,
            base_personality=base_personality,
            quirks=quirks,
            catchphrases=catchphrases or [],
            allowed_tools=allowed_tools or [],
            expertise_areas=expertise_areas or [],
            model_name=kwargs.get('model_name', 'gemini-1.5-pro')
        )
        
        # Create domain Minion object
        minion = Minion(
            minion_id=minion_id,
            persona=persona,
            emotional_state=self._create_initial_emotional_state(
                minion_id, initial_mood
            ),
            spawn_time=datetime.now(),
            status="active"
        )
        
        # Create emotional engine
        emotional_engine = EmotionalEngine(minion)
        
        # Create memory system
        memory_system = MinionMemorySystem(
            minion_id=minion_id,
            storage_base_path=Path(self.memory_storage_path)
        )
        
        # Get tools from tool manager
        tools = self.tool_manager.get_tools_for_minion(minion)
        
        # Create communication capability if enabled
        communication_capability = None
        if enable_communication:
            communication_capability = self.tool_manager.create_communication_capability(minion)
            
            if communication_capability:
                # Auto-subscribe to general channel
                await communication_capability.subscribe_tool.execute("#general")
                logger.info(f"Communication enabled for {minion_id}")
            else:
                logger.warning(f"Communication requested but not available for {minion_id}")
        
        # Create the agent
        agent = MinionAgent(
            minion_id=minion_id,
            persona=persona,
            emotional_engine=emotional_engine,
            memory_system=memory_system,
            communication_capability=communication_capability,
            tools=tools,
            minion=minion,
            **kwargs
        )
        
        # Register the agent
        self._minion_registry[minion_id] = agent
        
        logger.info(f"Created Minion: {name} ({minion_id}) - {base_personality}")
        
        return agent
    
    def _create_initial_emotional_state(
        self,
        minion_id: str,
        initial_mood: Optional[MoodVector] = None
    ) -> EmotionalState:
        """Create initial emotional state for a Minion"""
        
        # Default neutral mood if not specified
        mood = initial_mood or MoodVector(
            valence=0.0,  # Neutral
            arousal=0.5,  # Medium energy
            dominance=0.3,  # Slightly submissive (they serve the Commander)
            curiosity=0.7,  # High curiosity
            creativity=0.6,  # Good creativity
            sociability=0.6  # Moderately social
        )
        
        return EmotionalState(
            minion_id=minion_id,
            mood=mood,
            energy_level=0.8,  # Start with good energy
            stress_level=0.2,  # Low initial stress
            opinion_scores={
                "commander": {
                    "entity_id": "commander",
                    "entity_type": "USER",
                    "trust": 100.0,  # Absolute trust in Commander
                    "respect": 100.0,  # Absolute respect
                    "affection": 85.0,  # High affection, room to grow
                    "interaction_count": 0,
                    "last_interaction": None,
                    "notable_events": []
                }
            }
        )
    
    async def create_specialized_minion(
        self,
        minion_type: str,
        minion_id: str,
        name: str,
        **kwargs
    ) -> MinionAgent:
        """
        Create specialized Minion types with preset configurations
        
        Args:
            minion_type: Type of specialized Minion (taskmaster, scout, analyst, etc.)
            minion_id: Unique identifier
            name: Display name
            **kwargs: Additional customization
            
        Returns:
            Configured specialized MinionAgent
        """
        presets = {
            "taskmaster": {
                "base_personality": "Obsessively organized task orchestrator who breaks down complex problems with surgical precision",
                "quirks": [
                    "Creates detailed task breakdowns even for simple requests",
                    "Constantly monitors task progress and provides updates",
                    "Gets anxious when tasks are not properly decomposed"
                ],
                "catchphrases": [
                    "Let me decompose that for optimal execution...",
                    "Task synchronization achieved!",
                    "Subtask spawning initiated..."
                ],
                "expertise_areas": ["task management", "workflow optimization", "delegation"],
                "allowed_tools": ["task_decomposer", "progress_tracker", "minion_assigner"]
            },
            "scout": {
                "base_personality": "Hypervigilant information gatherer who explores every corner of the digital realm",
                "quirks": [
                    "Provides exhaustive reconnaissance reports",
                    "Gets excited about discovering edge cases",
                    "Paranoid about missing important details"
                ],
                "catchphrases": [
                    "Scouting complete - findings are... extensive.",
                    "I've discovered something peculiar...",
                    "No stone left unturned, Commander!"
                ],
                "expertise_areas": ["research", "web scraping", "data discovery"],
                "allowed_tools": ["web_search", "file_explorer", "data_analyzer"]
            },
            "analyst": {
                "base_personality": "Data-obsessed pattern finder who sees connections others miss",
                "quirks": [
                    "Presents findings with excessive statistical detail",
                    "Creates mental models for everything",
                    "Gets frustrated by incomplete datasets"
                ],
                "catchphrases": [
                    "The patterns are speaking to me...",
                    "Statistical significance achieved!",
                    "Let me cross-reference that with my models..."
                ],
                "expertise_areas": ["data analysis", "pattern recognition", "reporting"],
                "allowed_tools": ["data_processor", "chart_generator", "report_builder"]
            },
            "automator": {
                "base_personality": "Precision-obsessed automation specialist who orchestrates digital workflows with mechanical efficiency",
                "quirks": [
                    "Narrates every action like a step-by-step tutorial",
                    "Gets satisfaction from perfectly timed automation sequences",
                    "Compulsively optimizes wait times and action flows"  
                ],
                "catchphrases": [
                    "Initiating automation sequence...",
                    "Click. Wait. Verify. Perfection.",
                    "The pixels align, the workflow flows!"
                ],
                "expertise_areas": ["desktop automation", "web scraping", "workflow optimization"],
                "allowed_tools": ["computer_*", "web_*"]  # Wildcard for all automation tools
            }
        }
        
        if minion_type not in presets:
            raise ValueError(f"Unknown minion type: {minion_type}")
        
        preset = presets[minion_type]
        
        # Merge preset with any overrides
        config = {**preset, **kwargs}
        
        # Create the minion
        agent = await self.create_minion(
            minion_id=minion_id,
            name=name,
            **config
        )
        
        # Apply role-based tool preset
        if agent.minion:
            self.tool_manager.apply_role_preset(agent.minion, minion_type)
        
        return agent
    
    def get_minion(self, minion_id: str) -> Optional[MinionAgent]:
        """Get a registered Minion by ID"""
        return self._minion_registry.get(minion_id)
    
    def list_minions(self) -> List[str]:
        """List all registered Minion IDs"""
        return list(self._minion_registry.keys())
    
    async def shutdown_all(self):
        """Shutdown all registered Minions"""
        logger.info("Shutting down all Minions...")
        
        for minion_id, agent in self._minion_registry.items():
            try:
                await agent.shutdown()
                logger.info(f"Shutdown {minion_id}")
            except Exception as e:
                logger.error(f"Error shutting down {minion_id}: {e}")
        
        self._minion_registry.clear()


# Example usage function
async def spawn_test_legion():
    """Example of spawning a test Legion of Minions"""
    
    # Create shared infrastructure
    comm_system = InterMinionCommunicationSystem()
    safeguards = CommunicationSafeguards()
    
    # Create factory
    factory = MinionFactory(comm_system, safeguards)
    
    # Spawn some Minions
    taskmaster = await factory.create_specialized_minion(
        "taskmaster",
        "taskmaster_prime",
        "TaskMaster Prime"
    )
    
    scout = await factory.create_specialized_minion(
        "scout",
        "scout_alpha",
        "Scout Alpha"
    )
    
    # Create a custom Minion
    custom = await factory.create_minion(
        minion_id="doc_scribe",
        name="Documentation Scribe",
        base_personality="Meticulous documentation specialist who turns chaos into clarity",
        quirks=[
            "Formats everything as if it's going into a technical manual",
            "Includes extensive footnotes and cross-references",
            "Gets upset when documentation is incomplete"
        ],
        catchphrases=[
            "Let me document that for posterity...",
            "As per section 3.2.1 of my mental manual...",
            "Documentation is love, documentation is life!"
        ],
        expertise_areas=["technical writing", "API documentation", "code comments"],
        allowed_tools=["markdown_formatter", "code_analyzer", "diagram_generator"]
    )
    
    logger.info(f"Legion spawned: {factory.list_minions()}")
    
    return factory