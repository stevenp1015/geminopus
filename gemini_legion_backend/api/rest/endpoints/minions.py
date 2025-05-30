"""
Minion-related API endpoints

Handles creation, management, and interaction with Minions.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..schemas import (
    CreateMinionRequest,
    MinionResponse,
    MinionsListResponse,
    OperationResponse,
    RebootMinionRequest,
    MoodVectorResponse,
    OpinionScoreResponse,
    EmotionalStateResponse,
    MinionStatusEnum
)
from ....core.infrastructure.adk.agents import MinionFactory, MinionAgent
from ....core.infrastructure.messaging.communication_system import InterMinionCommunicationSystem
from ....core.infrastructure.messaging.safeguards import CommunicationSafeguards
from ....core.domain import MoodVector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/minions", tags=["minions"])


# Dependency injection for shared resources
def get_minion_factory() -> MinionFactory:
    """Get the singleton MinionFactory instance"""
    # This would typically be initialized at app startup
    # For now, we'll create it here
    if not hasattr(get_minion_factory, "_instance"):
        comm_system = InterMinionCommunicationSystem()
        safeguards = CommunicationSafeguards()
        get_minion_factory._instance = MinionFactory(
            comm_system=comm_system,
            safeguards=safeguards,
            memory_storage_path="/tmp/gemini_legion/memories"
        )
    return get_minion_factory._instance


def convert_minion_to_response(minion: MinionAgent) -> MinionResponse:
    """Convert a MinionAgent to API response format"""
    # Get current emotional state
    emotional_state = minion.emotional_engine.get_current_state()
    
    # Convert mood vector
    mood_response = MoodVectorResponse(
        valence=emotional_state.mood.valence,
        arousal=emotional_state.mood.arousal,
        dominance=emotional_state.mood.dominance,
        curiosity=emotional_state.mood.curiosity,
        creativity=emotional_state.mood.creativity,
        sociability=emotional_state.mood.sociability
    )
    
    # Convert opinion scores
    opinion_scores = {}
    for entity_id, opinion in emotional_state.opinion_scores.items():
        opinion_scores[entity_id] = OpinionScoreResponse(
            trust=opinion.trust,
            respect=opinion.respect,
            affection=opinion.affection,
            overall_sentiment=opinion.overall_sentiment
        )
    
    # Create emotional state response
    emotional_response = EmotionalStateResponse(
        minion_id=minion.minion_id,
        mood=mood_response,
        energy_level=emotional_state.energy_level,
        stress_level=emotional_state.stress_level,
        opinion_scores=opinion_scores,
        last_updated=emotional_state.last_updated.isoformat(),
        state_version=emotional_state.state_version
    )
    
    # Determine status
    if emotional_state.stress_level > 0.8:
        status = MinionStatusEnum.ERROR
    elif emotional_state.energy_level < 0.2:
        status = MinionStatusEnum.IDLE
    else:
        status = MinionStatusEnum.ACTIVE
    
    return MinionResponse(
        id=minion.minion_id,
        name=minion.persona.name,
        personality=minion.persona.base_personality,
        status=status,
        emotional_state=emotional_response,
        quirks=minion.persona.quirks,
        catchphrases=minion.persona.catchphrases,
        expertise=minion.persona.expertise_areas
    )


@router.get("/", response_model=MinionsListResponse)
async def list_minions(
    factory: MinionFactory = Depends(get_minion_factory)
) -> MinionsListResponse:
    """List all active minions"""
    minion_ids = factory.list_minions()
    
    minions = []
    for minion_id in minion_ids:
        minion = factory.get_minion(minion_id)
        if minion:
            minions.append(convert_minion_to_response(minion))
    
    return MinionsListResponse(
        minions=minions,
        total=len(minions)
    )


@router.get("/{minion_id}", response_model=MinionResponse)
async def get_minion(
    minion_id: str,
    factory: MinionFactory = Depends(get_minion_factory)
) -> MinionResponse:
    """Get a specific minion"""
    minion = factory.get_minion(minion_id)
    
    if not minion:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    return convert_minion_to_response(minion)


@router.post("/", response_model=OperationResponse)
async def create_minion(
    request: CreateMinionRequest,
    factory: MinionFactory = Depends(get_minion_factory)
) -> OperationResponse:
    """Create a new minion"""
    try:
        # Generate unique ID
        import uuid
        minion_id = f"minion_{uuid.uuid4().hex[:8]}"
        
        # Create minion using factory
        minion = await factory.create_minion(
            minion_id=minion_id,
            name=request.name,
            base_personality=request.personality,
            quirks=request.quirks,
            catchphrases=request.catchphrases,
            expertise_areas=request.expertise,
            allowed_tools=request.tools,
            enable_communication=True
        )
        
        logger.info(f"Created minion: {minion.minion_id} - {minion.persona.name}")
        
        return OperationResponse(
            status="created",
            id=minion_id,
            message=f"Minion '{request.name}' created successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating minion: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/specialized", response_model=OperationResponse)
async def create_specialized_minion(
    minion_type: str,
    name: str,
    factory: MinionFactory = Depends(get_minion_factory)
) -> OperationResponse:
    """Create a specialized minion (taskmaster, scout, analyst)"""
    try:
        # Generate unique ID
        import uuid
        minion_id = f"{minion_type}_{uuid.uuid4().hex[:8]}"
        
        # Create specialized minion
        minion = await factory.create_specialized_minion(
            minion_type=minion_type,
            minion_id=minion_id,
            name=name
        )
        
        logger.info(f"Created specialized {minion_type}: {minion.minion_id} - {name}")
        
        return OperationResponse(
            status="created",
            id=minion_id,
            message=f"Specialized {minion_type} '{name}' created successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating specialized minion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{minion_id}", response_model=OperationResponse)
async def delete_minion(
    minion_id: str,
    factory: MinionFactory = Depends(get_minion_factory)
) -> OperationResponse:
    """Delete a minion"""
    minion = factory.get_minion(minion_id)
    
    if not minion:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    try:
        # Shutdown the minion
        await minion.shutdown()
        
        # Remove from factory registry
        # Note: We'd need to add this method to MinionFactory
        # For now, we'll just mark it as deleted
        
        return OperationResponse(
            status="deleted",
            id=minion_id,
            message=f"Minion '{minion.persona.name}' deleted",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error deleting minion {minion_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting minion")


@router.post("/{minion_id}/reboot", response_model=OperationResponse)
async def reboot_minion(
    minion_id: str,
    request: RebootMinionRequest,
    factory: MinionFactory = Depends(get_minion_factory)
) -> OperationResponse:
    """Reboot a misbehaving minion"""
    minion = factory.get_minion(minion_id)
    
    if not minion:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    try:
        if request.hard_reset:
            # Hard reset - reset emotional state and clear all memories
            initial_mood = MoodVector(
                valence=0.0,
                arousal=0.5,
                dominance=0.3,
                curiosity=0.7,
                creativity=0.6,
                sociability=0.6
            )
            
            # Reset emotional state
            minion.emotional_engine.reset_state(initial_mood)
            
            # Clear all memories (would need to implement this)
            await minion.memory_system.forget(aggressive=True)
            
            status = "hard_reset_complete"
            message = f"Minion '{minion.persona.name}' hard reset - emotional state and memories cleared"
        else:
            # Soft reset - just clear working memory
            await minion.memory_system.working_memory.forget(threshold=0.0)
            
            status = "soft_reset_complete"
            message = f"Minion '{minion.persona.name}' soft reset - working memory cleared"
        
        logger.info(f"Rebooted minion {minion_id}: {status}")
        
        return OperationResponse(
            status=status,
            id=minion_id,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error rebooting minion {minion_id}: {e}")
        raise HTTPException(status_code=500, detail="Error rebooting minion")


@router.post("/{minion_id}/think", response_model=Dict[str, Any])
async def minion_think(
    minion_id: str,
    message: str,
    factory: MinionFactory = Depends(get_minion_factory)
) -> Dict[str, Any]:
    """Have a minion process a message and generate a response"""
    minion = factory.get_minion(minion_id)
    
    if not minion:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    try:
        # Generate response
        response = await minion.think(message)
        
        # Get memory stats
        memory_stats = minion.memory_system.get_memory_stats()
        
        return {
            "response": response,
            "minion_id": minion_id,
            "memory_stats": memory_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in minion think: {e}")
        raise HTTPException(status_code=500, detail="Error processing message")


@router.post("/{minion_id}/consolidate_memory", response_model=OperationResponse)
async def consolidate_memory(
    minion_id: str,
    factory: MinionFactory = Depends(get_minion_factory)
) -> OperationResponse:
    """Trigger memory consolidation for a minion"""
    minion = factory.get_minion(minion_id)
    
    if not minion:
        raise HTTPException(status_code=404, detail="Minion not found")
    
    try:
        # Run memory consolidation
        await minion.memory_system.consolidate()
        
        return OperationResponse(
            status="consolidation_complete",
            id=minion_id,
            message=f"Memory consolidation completed for '{minion.persona.name}'",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error consolidating memory for {minion_id}: {e}")
        raise HTTPException(status_code=500, detail="Error consolidating memory")