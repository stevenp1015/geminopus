"""
Minion Service - Application Layer

This service mediates between the API endpoints and the domain logic,
handling use cases related to minion lifecycle, state management, and operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
from dataclasses import asdict

from ...domain import (
    Minion,
    MinionPersona,
    EmotionalState,
    MoodVector,
    WorkingMemory,
    Experience
)
from ...infrastructure.adk.agents import MinionAgent, MinionFactory
from ...infrastructure.adk.emotional_engine import EmotionalEngine
from ...infrastructure.adk.memory_system import MinionMemorySystem
from ...infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from ...infrastructure.messaging.safeguards import CommunicationSafeguards
from ...infrastructure.persistence.repositories import MinionRepository

from ....api.websocket.connection_manager import connection_manager


logger = logging.getLogger(__name__)


class MinionService:
    """
    Application service for Minion operations
    
    This service orchestrates the creation, management, and interaction
    with Minions, coordinating between domain objects, infrastructure,
    and external systems.
    """
    
    def __init__(
        self,
        minion_repository: MinionRepository,
        comm_system: InterMinionCommunicationSystem,
        safeguards: CommunicationSafeguards
    ):
        """
        Initialize the Minion service
        
        Args:
            minion_repository: Repository for persisting minion state
            comm_system: Communication system for inter-minion messaging
            safeguards: Communication safeguards for preventing loops
        """
        self.repository = minion_repository
        self.comm_system = comm_system
        self.safeguards = safeguards
        
        # Factory for creating agents
        self.minion_factory = MinionFactory(comm_system, safeguards)
        
        # Registry of active agents
        self.active_agents: Dict[str, MinionAgent] = {}
        
        # Background tasks
        self._state_sync_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the service and background tasks"""
        logger.info("Starting Minion Service...")
        
        # Start background tasks
        self._state_sync_task = asyncio.create_task(self._state_sync_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Load existing minions from repository
        await self._load_existing_minions()
        
        logger.info("Minion Service started successfully")
    
    async def stop(self):
        """Stop the service and cleanup"""
        logger.info("Stopping Minion Service...")
        
        # Cancel background tasks
        if self._state_sync_task:
            self._state_sync_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()
        
        # Shutdown all active agents
        await self.minion_factory.shutdown_all()
        
        logger.info("Minion Service stopped")
    
    async def spawn_minion(
        self,
        minion_id: str,
        name: str,
        base_personality: str,
        quirks: List[str],
        catchphrases: Optional[List[str]] = None,
        expertise_areas: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None,
        initial_mood: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Spawn a new Minion
        
        This is the primary use case for creating new Minions.
        
        Returns:
            Dictionary containing minion details and status
        """
        try:
            # Check if minion already exists
            if minion_id in self.active_agents:
                raise ValueError(f"Minion {minion_id} already exists")
            
            # Create mood vector from dict if provided
            mood = None
            if initial_mood:
                mood = MoodVector(**initial_mood)
            
            # Create the agent through factory
            agent = await self.minion_factory.create_minion(
                minion_id=minion_id,
                name=name,
                base_personality=base_personality,
                quirks=quirks,
                catchphrases=catchphrases,
                expertise_areas=expertise_areas,
                allowed_tools=allowed_tools,
                initial_mood=mood
            )
            
            # Register as active
            self.active_agents[minion_id] = agent
            
            # Get the domain minion object
            minion = agent.minion if hasattr(agent, 'minion') else None
            
            # Persist to repository
            if minion:
                await self.repository.save(minion)
            
            # Log spawn event
            logger.info(f"Spawned Minion: {name} ({minion_id})")

            if minion: # Ensure minion object exists before broadcasting
                minion_data_for_broadcast = self._minion_to_dict(minion)
                asyncio.create_task(connection_manager.broadcast_service_event(
                    "minion_spawned",
                    {"minion": minion_data_for_broadcast}
                ))
                asyncio.create_task(connection_manager.broadcast_service_event(
                    "minion_status_changed",
                    {"minion_id": minion_id, "status": minion.status} # Use status from domain object
                ))
            
            # Return minion details
            # Ensure the returned status is consistent with what was broadcast
            current_status = minion.status if minion else "active"
            spawn_time_iso = minion.spawn_time.isoformat() if minion and hasattr(minion, 'spawn_time') else datetime.now().isoformat()
            emotional_state_dict = asdict(minion.emotional_state) if minion and minion.emotional_state else None

            return {
                "minion_id": minion_id,
                "name": name, # This comes from method args, persona.name would be from minion object
                "status": current_status,
                "personality": base_personality, # From method args
                "quirks": quirks, # From method args
                "spawn_time": spawn_time_iso,
                "emotional_state": emotional_state_dict
            }
            
        except Exception as e: # This is the correct end of the try-except for spawn_minion
            logger.error(f"Failed to spawn minion {minion_id}: {e}")
            raise
    
    async def get_minion(self, minion_id: str) -> Optional[Dict[str, Any]]:
        """
        Get minion details by ID
        
        Returns:
            Minion details or None if not found
        """
        # Check active agents first
        if agent := self.active_agents.get(minion_id):
            minion = agent.minion if hasattr(agent, 'minion') else None
            if minion:
                return self._minion_to_dict(minion)
        
        # Fall back to repository
        minion = await self.repository.get_by_id(minion_id)
        if minion:
            return self._minion_to_dict(minion)
        
        return None
    
    async def list_minions(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all minions with optional filtering
        
        Args:
            status_filter: Filter by status (active, inactive, all)
            limit: Maximum number to return
            offset: Pagination offset
            
        Returns:
            List of minion details
        """
        # Get from repository (includes inactive)
        all_minions = await self.repository.list_all(limit, offset)
        
        # Apply status filter
        if status_filter == "active":
            minions = [m for m in all_minions if m.minion_id in self.active_agents]
        elif status_filter == "inactive":
            minions = [m for m in all_minions if m.minion_id not in self.active_agents]
        else:
            minions = all_minions
        
        return [self._minion_to_dict(m) for m in minions]
    
    async def update_minion_personality(
        self,
        minion_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a minion's personality traits
        
        Args:
            minion_id: ID of minion to update
            updates: Dictionary of updates (quirks, catchphrases, etc.)
            
        Returns:
            Updated minion details
        """
        # Get active agent
        agent = self.active_agents.get(minion_id)
        if not agent:
            raise ValueError(f"Minion {minion_id} is not active")
        
        # Update persona
        persona = agent.persona
        
        if "quirks" in updates:
            persona.quirks = updates["quirks"]
        if "catchphrases" in updates:
            persona.catchphrases = updates["catchphrases"]
        if "expertise_areas" in updates:
            persona.expertise_areas = updates["expertise_areas"]
        
        # Rebuild instruction set
        agent.instruction = agent._build_instruction(persona, agent.emotional_engine)
        
        # Update in repository
        if hasattr(agent, 'minion'):
            agent.minion.persona = persona
            await self.repository.save(agent.minion)
        
        return await self.get_minion(minion_id)
    
    async def get_emotional_state(self, minion_id: str) -> Dict[str, Any]:
        """
        Get current emotional state of a minion
        
        Returns:
            Emotional state details
        """
        agent = self.active_agents.get(minion_id)
        if not agent:
            raise ValueError(f"Minion {minion_id} is not active")
        
        state = await agent.emotional_engine.get_current_state()
        
        return {
            "mood": asdict(state.mood),
            "energy_level": state.energy_level,
            "stress_level": state.stress_level,
            "opinion_scores": {
                entity_id: {
                    "trust": score.trust,
                    "respect": score.respect,
                    "affection": score.affection,
                    "overall_sentiment": score.overall_sentiment
                }
                for entity_id, score in state.opinion_scores.items()
            },
            "last_updated": state.last_updated.isoformat()
        }
    
    async def update_emotional_state(
        self,
        minion_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a minion's emotional state
        
        Args:
            minion_id: ID of minion to update
            updates: Dictionary of emotional updates
            
        Returns:
            Updated emotional state
        """
        agent = self.active_agents.get(minion_id)
        if not agent:
            raise ValueError(f"Minion {minion_id} is not active")
        
        # Apply updates through emotional engine
        current_state = await agent.emotional_engine.get_current_state()
        
        # Update mood if provided
        if "mood" in updates:
            mood_data = updates["mood"]
            current_state.mood = MoodVector(**mood_data)
        
        # Update energy/stress if provided
        if "energy_level" in updates:
            current_state.energy_level = updates["energy_level"]
        if "stress_level" in updates:
            current_state.stress_level = updates["stress_level"]
        
        # Apply the update
        await agent.emotional_engine.apply_direct_update(current_state)
        
        updated_state_dict = await self.get_emotional_state(minion_id)

        asyncio.create_task(connection_manager.broadcast_service_event(
            "minion_emotional_state_updated",
            {"minion_id": minion_id, "emotional_state": updated_state_dict}
        ))

        return updated_state_dict
    
    async def send_command(
        self,
        minion_id: str,
        command: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a command to a minion and get response
        
        Args:
            minion_id: ID of minion to command
            command: Command text
            context: Optional context for the command
            
        Returns:
            Response from the minion
        """
        agent = self.active_agents.get(minion_id)
        if not agent:
            raise ValueError(f"Minion {minion_id} is not active")
        
        # Process through agent's think method
        response = await agent.think(command, context)
        
        return {
            "minion_id": minion_id,
            "command": command,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "emotional_impact": agent.memory_system.get_recent_experiences()[-1].emotional_impact
            if agent.memory_system.get_recent_experiences() else 0
        }
    
    async def get_minion_memories(
        self,
        minion_id: str,
        memory_type: str = "working",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories from a minion's memory system
        
        Args:
            minion_id: ID of minion
            memory_type: Type of memory (working, episodic, semantic)
            limit: Maximum number of memories to return
            
        Returns:
            List of memory records
        """
        agent = self.active_agents.get(minion_id)
        if not agent:
            raise ValueError(f"Minion {minion_id} is not active")
        
        memories = []
        
        if memory_type == "working":
            # Get from working memory
            working_memories = agent.memory_system.get_recent_experiences()[:limit]
            memories = [
                {
                    "type": "working",
                    "content": exp.content,
                    "timestamp": exp.timestamp.isoformat(),
                    "significance": exp.significance,
                    "emotional_impact": exp.emotional_impact
                }
                for exp in working_memories
            ]
        elif memory_type == "episodic" and hasattr(agent, 'episodic_memory'):
            # Get from episodic memory
            episodic_memories = await agent.episodic_memory.retrieve_recent(limit)
            memories = [
                {
                    "type": "episodic",
                    "content": mem.content,
                    "timestamp": mem.timestamp.isoformat(),
                    "context": mem.context,
                    "emotional_state": mem.emotional_state
                }
                for mem in episodic_memories
            ]
        
        return memories
    
    async def deactivate_minion(self, minion_id: str) -> Dict[str, Any]:
        """
        Deactivate a minion (shutdown but keep in repository)
        
        Args:
            minion_id: ID of minion to deactivate
            
        Returns:
            Status message
        """
        agent = self.active_agents.get(minion_id)
        if not agent:
            raise ValueError(f"Minion {minion_id} is not active")
        
        # Shutdown the agent
        await agent.shutdown()
        
        # Remove from active registry
        del self.active_agents[minion_id]
        
        # Update status in repository
        minion = await self.repository.get_by_id(minion_id)
        if minion:
            minion.status = "inactive" # Status is set here
            await self.repository.save(minion)
            minion_name = minion.persona.name if hasattr(minion, 'persona') else minion_id
        else:
            minion_name = minion_id # Fallback if minion object not retrieved

        asyncio.create_task(connection_manager.broadcast_service_event(
            "minion_despawned",
            {"minion_id": minion_id, "minion_name": minion_name}
        ))
        asyncio.create_task(connection_manager.broadcast_service_event(
            "minion_status_changed",
            {"minion_id": minion_id, "status": "inactive"}
        ))
        
        logger.info(f"Deactivated minion {minion_id}")
        
        return {
            "minion_id": minion_id,
            "status": "inactive", # This is correct for the return value
            "timestamp": datetime.now().isoformat()
        }
    
    async def _state_sync_loop(self):
        """Background task to sync minion states to repository"""
        while True:
            try:
                # Sync every 30 seconds
                await asyncio.sleep(30)
                
                for minion_id, agent in self.active_agents.items():
                    try:
                        if hasattr(agent, 'minion'):
                            # Update emotional state
                            agent.minion.emotional_state = await agent.emotional_engine.get_current_state()
                            
                            # Save to repository
                            await self.repository.save(agent.minion)
                            
                    except Exception as e:
                        logger.error(f"Failed to sync state for {minion_id}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in state sync loop: {e}")
    
    async def _health_check_loop(self):
        """Background task to check minion health"""
        while True:
            try:
                # Check every 60 seconds
                await asyncio.sleep(60)
                
                for minion_id, agent in list(self.active_agents.items()):
                    try:
                        # Simple health check - ensure agent is responsive
                        # In a real system, this would be more sophisticated
                        if hasattr(agent, 'emotional_engine'):
                            await agent.emotional_engine.get_current_state()
                        
                    except Exception as e:
                        logger.error(f"Health check failed for {minion_id}: {e}")
                        # Could implement auto-restart logic here
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def _load_existing_minions(self):
        """Load and reactivate existing minions from repository"""
        try:
            # Get all minions marked as active
            minions = await self.repository.list_by_status("active")
            
            for minion in minions:
                try:
                    # Recreate the agent
                    initial_mood_obj = None
                    if minion.emotional_state and hasattr(minion.emotional_state, 'mood'):
                        initial_mood_obj = minion.emotional_state.mood
                    agent = await self.minion_factory.create_minion(
                        minion_id=minion.minion_id,
                        name=minion.persona.name,
                        base_personality=minion.persona.base_personality,
                        quirks=minion.persona.quirks,
                        catchphrases=minion.persona.catchphrases,
                        expertise_areas=minion.persona.expertise_areas,
                        allowed_tools=minion.persona.allowed_tools,
                        initial_mood=initial_mood_obj
                    )
                    
                    # Restore emotional state
                    if minion.emotional_state:
                        await agent.emotional_engine.apply_direct_update(minion.emotional_state)
                    
                    # Register as active
                    self.active_agents[minion.minion_id] = agent
                    
                    logger.info(f"Reactivated minion {minion.minion_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to reactivate minion {minion.minion_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load existing minions: {e}")
    
    def _minion_to_dict(self, minion: Minion) -> Dict[str, Any]:
        """Convert domain Minion to API-friendly dictionary"""
        return {
            "minion_id": minion.minion_id,
            "name": minion.persona.name,
            "status": minion.status,
            "personality": minion.persona.base_personality,
            "quirks": minion.persona.quirks,
            "catchphrases": minion.persona.catchphrases,
            "expertise_areas": minion.persona.expertise_areas,
            "allowed_tools": minion.persona.allowed_tools,
            "spawn_time": minion.spawn_time.isoformat(),
            "emotional_state": {
                "mood": asdict(minion.emotional_state.mood),
                "energy_level": minion.emotional_state.energy_level,
                "stress_level": minion.emotional_state.stress_level
            }
        }
