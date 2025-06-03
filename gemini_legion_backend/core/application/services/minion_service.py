"""
Minion Service - Application Layer

This service mediates between the API endpoints and the domain logic,
handling use cases related to minion lifecycle, state management, and operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
from dataclasses import asdict, is_dataclass # Added is_dataclass
import uuid # Import uuid

from ...domain import (
    Minion,
    MinionPersona,
    EmotionalState,
    MoodVector,
    WorkingMemory,
    Experience,
    MinionStatus # Import MinionStatus domain object
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
    # Define status enum strings directly for mapping, avoiding API layer import
    # These should align with api.rest.schemas.MinionStatusEnum
    _STATUS_ENUM_ACTIVE = "active"
    _STATUS_ENUM_IDLE = "idle"
    _STATUS_ENUM_BUSY = "busy"
    _STATUS_ENUM_ERROR = "error"
    _STATUS_ENUM_REBOOTING = "rebooting" # Though current mapping logic doesn't produce this

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
        name: str,
        personality: str, # Changed from base_personality
        quirks: List[str],
        catchphrases: Optional[List[str]] = None,
        expertise: Optional[List[str]] = None,
        tools: Optional[List[str]] = None, # Changed from allowed_tools
        initial_mood: Optional[Dict[str, float]] = None,
        minion_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Spawn a new Minion
        
        This is the primary use case for creating new Minions.
        
        Returns:
            Dictionary containing minion details and status
        """
        try:
            # Generate minion_id if not provided
            if not minion_id:
                minion_id = str(uuid.uuid4())
            
            # Check if minion already exists
            if minion_id in self.active_agents:
                # This could happen if a UUID collision occurs, though highly unlikely.
                # Or if an ID was passed in that already exists.
                raise ValueError(f"Minion {minion_id} already exists or collision.")
            
            # Create mood vector from dict if provided
            mood = None
            if initial_mood:
                mood = MoodVector(**initial_mood)
            
            # Create the agent through factory
            agent = await self.minion_factory.create_minion(
                minion_id=minion_id,
                name=name,
                base_personality=personality, # Use new parameter name
                quirks=quirks,
                catchphrases=catchphrases,
                expertise_areas=expertise,
                allowed_tools=tools, # This line should now be correct as 'tools' is the param
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
                # Use a serializable status for the event, e.g., health_status or a simple "active" string
                # status_for_event = minion.status.health_status if minion and minion.status else "unknown"
                mapped_status_string = self._map_domain_status_to_api_enum_string(minion.status) if minion and minion.status else self._STATUS_ENUM_ERROR
                asyncio.create_task(connection_manager.broadcast_service_event(
                    "minion_status_changed",
                    {"minion_id": minion_id, "status": mapped_status_string}
                ))
            
            # Return minion details
            # Ensure the returned status is consistent with what was broadcast
            # current_status = minion.status if minion else "active" # This was the object
            mapped_status_string_for_return = self._map_domain_status_to_api_enum_string(minion.status) if minion and minion.status else self._STATUS_ENUM_ERROR
            creation_date_iso = minion.creation_date.isoformat() if minion and hasattr(minion, 'creation_date') else datetime.now().isoformat()
            emotional_state_dict = asdict(minion.emotional_state) if minion and minion.emotional_state else None

            return {
                "minion_id": minion_id,
                "name": name,
                "status": mapped_status_string_for_return,
                "personality": personality,
                "quirks": quirks,
                "expertise": expertise,
                "catchphrases": catchphrases,
                "tools": tools,# Ensure this matches the new parameter name
                "creation_date": creation_date_iso, # Changed from spawn_time
                "emotional_state": emotional_state_dict
            }
            
        except Exception as e:
            # Ensure minion_id is part of the log message even if generated
            log_minion_id = minion_id if 'minion_id' in locals() and minion_id else "UNKNOWN_ID"
            logger.error(f"Failed to spawn minion {log_minion_id}: {e}")
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
        # "inactive" is not part of MinionStatusEnum, frontend might not handle it.
        # Mapping to ERROR for now, or consider adding INACTIVE to the enum and frontend.
        asyncio.create_task(connection_manager.broadcast_service_event(
            "minion_status_changed",
            {"minion_id": minion_id, "status": self._STATUS_ENUM_ERROR } # Was "inactive"
        ))
        
        logger.info(f"Deactivated minion {minion_id}")
        
        return {
            "minion_id": minion_id,
            "status": self._STATUS_ENUM_ERROR, # Was "inactive"
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
                            agent.minion.emotional_state = agent.emotional_engine.get_current_state() # Removed await
                            
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
                            agent.emotional_engine.get_current_state() # Removed await
                        
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
    
    def _map_domain_status_to_api_enum_string(self, domain_status: Optional[MinionStatus]) -> str:
        """Maps domain MinionStatus object to an API enum string."""
        if not domain_status:
            return self._STATUS_ENUM_ERROR

        # Logic adapted from api.rest.endpoints.minions.convert_minion_to_response
        if not domain_status.is_active:
            return self._STATUS_ENUM_ERROR # Consider an INACTIVE if defined in enum
        elif domain_status.health_status == "error":
            return self._STATUS_ENUM_ERROR
        elif domain_status.health_status == "operational":
            if domain_status.current_task:
                return self._STATUS_ENUM_BUSY
            else:
                return self._STATUS_ENUM_IDLE
        elif domain_status.health_status == "degraded":
            # Consider a DEGRADED enum if defined, maps to ACTIVE for now
            return self._STATUS_ENUM_ACTIVE
        else: # Unknown health_status but is_active
            return self._STATUS_ENUM_ACTIVE
        # REBOOTING status is not derivable from current domain_status fields with this logic

    def _minion_to_dict(self, minion: Minion) -> Dict[str, Any]:
        """Convert domain Minion to API-friendly dictionary"""
        
        mapped_status = self._map_domain_status_to_api_enum_string(minion.status)

        # Prepare a nested persona dictionary
        persona_dict = {
            "name": minion.persona.name,
            "base_personality": minion.persona.base_personality,
            "quirks": minion.persona.quirks if hasattr(minion.persona, 'quirks') else [],
            "catchphrases": minion.persona.catchphrases if hasattr(minion.persona, 'catchphrases') else [],
            "expertise_areas": minion.persona.expertise_areas if hasattr(minion.persona, 'expertise_areas') else [],
            "allowed_tools": minion.persona.allowed_tools if hasattr(minion.persona, 'allowed_tools') else [],
            "model_name": minion.persona.model_name if hasattr(minion.persona, 'model_name') else "unknown"
            # Not including minion_id here as it's at the top level of the Minion object
        }

        return {
            "minion_id": minion.minion_id,
            "persona": persona_dict, # Nested persona object
            "status": mapped_status, # Use the mapped string enum
            "creation_date": minion.creation_date.isoformat(),
            "emotional_state": {
                "mood": asdict(m.mood) if (m := minion.emotional_state) and hasattr(m, 'mood') and is_dataclass(m.mood) else (getattr(m, 'mood', None) if (m := minion.emotional_state) else None),
                "energy_level": m.energy_level if (m := minion.emotional_state) and hasattr(m, 'energy_level') else 0.8,
                "stress_level": m.stress_level if (m := minion.emotional_state) and hasattr(m, 'stress_level') else 0.2,
                "opinion_scores": {
                    entity_id: asdict(score) if is_dataclass(score) else score
                    for entity_id, score in m.opinion_scores.items()
                } if (m := minion.emotional_state) and hasattr(m, 'opinion_scores') and m.opinion_scores else {},
                "last_updated": m.last_updated.isoformat() if (m := minion.emotional_state) and hasattr(m, 'last_updated') and m.last_updated else datetime.now().isoformat(),
                "state_version": m.state_version if (m := minion.emotional_state) and hasattr(m, 'state_version') else 1
            } if minion.emotional_state else None
        }

    async def send_message(
        self,
        minion_id: str,
        channel_id: str, # Changed from 'channel' to 'channel_id' for clarity and consistency
        content: str     # Changed from 'message' to 'content' for clarity
    ) -> bool:
        """
        Allows a specific minion to send a message to a channel.
        This is called by the /api/minions/{minion_id}/send-message endpoint.
        """
        logger.info(f"MinionService: Minion '{minion_id}' attempting to send message to channel '{channel_id}': \"{content[:50]}...\"")
        
        agent = self.active_agents.get(minion_id)
        if not agent:
            logger.error(f"MinionService: Minion '{minion_id}' not found or not active. Cannot send message.")
            # Consider raising a specific exception an endpoint can catch for a 404 vs 500
            return False # Or raise ValueError(f"Minion {minion_id} not active")

        if not self.comm_system:
            logger.error("MinionService: Communication system is not initialized. Cannot send message.")
            return False # Or raise Exception("Communication system not available")

        try:
            # Assuming comm_system has a method like send_message_as_minion or similar
            # that can take the minion_id, channel_id, and the message content.
            # The IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md shows:
            # ConversationalLayer.send_message(from_minion: str, to_channel: str, message: str, ...)
            # We'll map our parameters to that.
            
            # We also need to consider if the minion should "think" or just relay.
            # For now, let's assume it's a relay via the comm_system.
            # A more advanced version might involve agent.think(f"I need to say '{content}' in channel '{channel_id}'")
            
            # IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md section 5.1 shows InterMinionCommunicationSystem
            # has a conversational_layer which has the send_message method.
            # Parameter names must match the definition in ConversationalLayer.send_message
            # which are likely from_minion, to_channel, message as per IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md
            await self.comm_system.conversational_layer.send_message(
                from_minion=minion_id,     # Corrected keyword to match expected 'from_minion'
                to_channel=channel_id,      # Corrected keyword to match expected 'to_channel'
                message=content            # Corrected keyword to match expected 'message'
                # We could potentially pass personality_modifiers if available and supported
            )
            
            logger.info(f"MinionService: Message successfully sent by minion '{minion_id}' to channel '{channel_id}'.")
            
            # The message itself should be broadcast to clients (including the sender's UI)
            # by the InterMinionCommunicationSystem when it processes the message for the channel.
            # So, no explicit broadcast here, relying on comm_system's duties.
            return True
            
        except Exception as e:
            logger.error(f"MinionService: Error during send_message for minion '{minion_id}' to channel '{channel_id}': {e}", exc_info=True)
            # This will likely result in a 500 if not caught specifically by the endpoint
            raise # Re-raise to let the endpoint handle it as a 500 or a more specific error
