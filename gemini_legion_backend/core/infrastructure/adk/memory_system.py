"""
Multi-Layered Memory System for Minions

Implements a comprehensive memory architecture with working memory,
short-term memory, episodic memory, semantic memory, and procedural memory.
"""

from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from abc import ABC, abstractmethod
import asyncio
import logging
import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ...domain import Experience, EmotionalState, MoodVector


logger = logging.getLogger(__name__)


# Constants
EPISODIC_SIGNIFICANCE_THRESHOLD = 0.6
SEMANTIC_EXTRACTION_THRESHOLD = 0.7
PATTERN_RECOGNITION_THRESHOLD = 0.8


@dataclass
class MemoryItem:
    """Base class for memory items"""
    id: str
    timestamp: datetime
    content: Any
    context: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    decay_rate: float = 0.1
    
    def access(self):
        """Record access to this memory"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def get_strength(self) -> float:
        """Calculate memory strength based on decay and access"""
        if not self.last_accessed:
            return 1.0
        
        time_since_access = (datetime.now() - self.last_accessed).total_seconds() / 3600
        decay_factor = np.exp(-self.decay_rate * time_since_access)
        access_factor = min(1.0, self.access_count / 10)
        
        return decay_factor * (0.7 + 0.3 * access_factor)


@dataclass 
class EpisodicMemory(MemoryItem):
    """Specific experience memory"""
    experience: Optional[Experience] = None
    emotional_context: Optional[Dict[str, Any]] = None
    significance: Optional[float] = None
    related_memories: List[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None


@dataclass
class SemanticMemory(MemoryItem):
    """Learned knowledge/concept"""
    concept: Optional[str] = None
    properties: Optional[Dict[str, Any]] = field(default_factory=dict)
    relationships: Optional[Dict[str, List[str]]] = field(default_factory=dict)
    confidence: Optional[float] = 0.0
    source_episodes: List[str] = field(default_factory=list)


@dataclass
class ProceduralMemory(MemoryItem):
    """Learned skill or pattern"""
    skill_name: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = field(default_factory=dict)
    action_sequence: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    success_rate: Optional[float] = 0.0
    usage_count: int = 0
    refinements: List[Dict[str, Any]] = field(default_factory=list)


class MemoryLayer(ABC):
    """Abstract base class for memory layers"""
    
    @abstractmethod
    async def store(self, item: Any) -> bool:
        """Store an item in this memory layer"""
        pass
    
    @abstractmethod
    async def retrieve(self, query: Any) -> List[Any]:
        """Retrieve items from this memory layer"""
        pass
    
    @abstractmethod
    async def forget(self, threshold: float) -> int:
        """Forget items below strength threshold"""
        pass


class WorkingMemory(MemoryLayer):
    """
    Immediate context memory - Miller's Law (7±2 items)
    
    Stores the most recent and relevant items for current processing.
    """
    
    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.items: deque = deque(maxlen=capacity)
        self._attention_weights: Dict[str, float] = {}
    
    async def store(self, item: Experience) -> bool:
        """Store experience in working memory"""
        # Create memory item
        memory_item = MemoryItem(
            id=f"wm_{datetime.now().timestamp()}",
            timestamp=item.timestamp,
            content=item,
            context=item.context
        )
        
        # Add to deque (automatically removes oldest if at capacity)
        self.items.append(memory_item)
        
        # Update attention weights
        self._update_attention_weights()
        
        return True
    
    async def retrieve(self, query: Optional[str] = None) -> List[MemoryItem]:
        """Retrieve all items from working memory"""
        # Apply attention weights
        weighted_items = []
        for item in self.items:
            weight = self._attention_weights.get(item.id, 1.0)
            weighted_items.append((item, weight))
        
        # Sort by attention weight
        weighted_items.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, _ in weighted_items]
    
    async def forget(self, threshold: float) -> int:
        """Working memory doesn't forget based on threshold"""
        return 0
    
    def _update_attention_weights(self):
        """Update attention weights based on recency and relevance"""
        if not self.items:
            return
        
        # Simple recency-based attention
        total_items = len(self.items)
        for i, item in enumerate(self.items):
            # More recent items get higher weight
            recency_weight = (i + 1) / total_items
            self._attention_weights[item.id] = recency_weight
    
    def get_context_summary(self) -> str:
        """Get a summary of current working memory context"""
        if not self.items:
            return "No active context"
        
        summaries = []
        for item in list(self.items)[-3:]:  # Last 3 items
            if isinstance(item.content, Experience):
                summaries.append(item.content.content[:50] + "...")
        
        return " | ".join(summaries)

class ShortTermMemory(MemoryLayer):
    """
    Recent interactions memory with TTL
    
    Stores recent experiences that might become long-term memories.
    """
    
    def __init__(self, ttl_minutes: int = 30, max_items: int = 100):
        self.ttl_minutes = ttl_minutes
        self.max_items = max_items
        self.items: Dict[str, MemoryItem] = {}
        self._cleanup_task = None
    
    async def store(self, item: Experience) -> bool:
        """Store experience in short-term memory"""
        memory_id = f"stm_{datetime.now().timestamp()}"
        
        memory_item = MemoryItem(
            id=memory_id,
            timestamp=item.timestamp,
            content=item,
            context=item.context,
            decay_rate=0.5  # Faster decay for short-term
        )
        
        self.items[memory_id] = memory_item
        
        # Enforce max items
        if len(self.items) > self.max_items:
            await self._evict_oldest()
        
        return True
    
    async def retrieve(
        self,
        query: Optional[str] = None,
        time_window: Optional[timedelta] = None
    ) -> List[MemoryItem]:
        """Retrieve items from short-term memory"""
        current_time = datetime.now()
        
        # Filter by time window if specified
        if time_window:
            cutoff = current_time - time_window
            items = [
                item for item in self.items.values()
                if item.timestamp >= cutoff
            ]
        else:
            items = list(self.items.values())
        
        # Filter expired items
        ttl_cutoff = current_time - timedelta(minutes=self.ttl_minutes)
        active_items = [
            item for item in items
            if item.timestamp >= ttl_cutoff
        ]
        
        # Sort by recency
        active_items.sort(key=lambda x: x.timestamp, reverse=True)
        
        return active_items
    
    async def forget(self, threshold: float) -> int:
        """Forget items below strength threshold or expired"""
        current_time = datetime.now()
        ttl_cutoff = current_time - timedelta(minutes=self.ttl_minutes)
        
        to_remove = []
        for memory_id, item in self.items.items():
            # Check TTL
            if item.timestamp < ttl_cutoff:
                to_remove.append(memory_id)
            # Check strength
            elif item.get_strength() < threshold:
                to_remove.append(memory_id)
        
        for memory_id in to_remove:
            del self.items[memory_id]
        
        return len(to_remove)
    
    async def _evict_oldest(self):
        """Evict oldest items when at capacity"""
        if len(self.items) <= self.max_items:
            return
        
        # Sort by timestamp
        sorted_items = sorted(
            self.items.items(),
            key=lambda x: x[1].timestamp
        )
        
        # Remove oldest
        num_to_remove = len(self.items) - self.max_items
        for memory_id, _ in sorted_items[:num_to_remove]:
            del self.items[memory_id]
    
    def get_important_memories(self, threshold: float = 0.7) -> List[MemoryItem]:
        """Get memories above importance threshold"""
        important = []
        
        for item in self.items.values():
            if isinstance(item.content, Experience):
                if item.content.significance >= threshold:
                    important.append(item)
        
        return important


class EpisodicMemoryLayer(MemoryLayer):
    """
    Long-term episodic memory with vector search
    
    Stores significant experiences with semantic search capabilities.
    """
    
    def __init__(
        self,
        storage_path: Path,
        embedding_model: Optional[Any] = None,
        index_dimensions: int = 768
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = embedding_model
        self.index_dimensions = index_dimensions
        
        # In-memory index for fast retrieval
        self.memory_index: Dict[str, EpisodicMemory] = {}
        self.embeddings_matrix: Optional[np.ndarray] = None
        self.memory_ids: List[str] = []
        
        # Load existing memories
        self._load_memories()
    
    async def store(self, experience: Experience) -> bool:
        """Store significant experience as episodic memory"""
        # Check significance threshold
        if experience.significance < EPISODIC_SIGNIFICANCE_THRESHOLD:
            return False
        
        memory_id = f"ep_{datetime.now().timestamp()}"
        
        # Generate embeddings if model available
        embeddings = None
        if self.embedding_model and hasattr(experience, 'content'):
            embeddings = await self._generate_embeddings(experience.content)
        
        # Create episodic memory
        memory = EpisodicMemory(
            id=memory_id,
            timestamp=experience.timestamp,
            content=experience,
            context=experience.context,
            experience=experience,
            emotional_context=experience.context.get('emotional_state', {}),
            significance=experience.significance,
            embeddings=embeddings
        )
        
        # Find related memories
        if embeddings is not None:
            related = await self._find_related_memories(embeddings, limit=3)
            memory.related_memories = [m.id for m in related]
        
        # Store in index
        self.memory_index[memory_id] = memory
        
        # Update embeddings matrix
        if embeddings is not None:
            self._update_embeddings_matrix(memory_id, embeddings)
        
        # Persist to disk
        self._save_memory(memory)
        
        return True
    
    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        min_significance: float = 0.0
    ) -> List[EpisodicMemory]:
        """Retrieve memories by semantic search"""
        if not self.embedding_model:
            # Fallback to recency-based retrieval
            memories = list(self.memory_index.values())
            memories.sort(key=lambda x: x.timestamp, reverse=True)
            return memories[:limit]
        
        # Generate query embeddings
        query_embeddings = await self._generate_embeddings(query)
        
        # Find similar memories
        similar = await self._find_related_memories(
            query_embeddings,
            limit=limit * 2  # Get more for filtering
        )
        
        # Filter by significance
        filtered = [
            m for m in similar
            if m.significance >= min_significance
        ]
        
        return filtered[:limit]
    
    async def forget(self, threshold: float) -> int:
        """Forget memories below strength threshold"""
        to_remove = []
        
        for memory_id, memory in self.memory_index.items():
            if memory.get_strength() < threshold:
                to_remove.append(memory_id)
        
        for memory_id in to_remove:
            # Remove from index
            del self.memory_index[memory_id]
            
            # Remove from disk
            memory_file = self.storage_path / f"{memory_id}.pkl"
            if memory_file.exists():
                memory_file.unlink()
        
        # Rebuild embeddings matrix
        self._rebuild_embeddings_matrix()
        
        return len(to_remove)
    
    async def _generate_embeddings(self, text: str) -> np.ndarray:
        """Generate embeddings for text"""
        # This would use the actual embedding model
        # For now, return random embeddings
        return np.random.randn(self.index_dimensions)
    
    async def _find_related_memories(
        self,
        embeddings: np.ndarray,
        limit: int = 5
    ) -> List[EpisodicMemory]:
        """Find memories similar to given embeddings"""
        if self.embeddings_matrix is None or len(self.memory_ids) == 0:
            return []
        
        # Calculate similarities
        similarities = cosine_similarity(
            embeddings.reshape(1, -1),
            self.embeddings_matrix
        )[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[-limit:][::-1]
        
        related = []
        for idx in top_indices:
            memory_id = self.memory_ids[idx]
            if memory_id in self.memory_index:
                memory = self.memory_index[memory_id]
                memory.access()  # Record access
                related.append(memory)
        
        return related
    
    def _update_embeddings_matrix(self, memory_id: str, embeddings: np.ndarray):
        """Update the embeddings matrix with new memory"""
        self.memory_ids.append(memory_id)
        
        if self.embeddings_matrix is None:
            self.embeddings_matrix = embeddings.reshape(1, -1)
        else:
            self.embeddings_matrix = np.vstack([
                self.embeddings_matrix,
                embeddings.reshape(1, -1)
            ])
    
    def _rebuild_embeddings_matrix(self):
        """Rebuild embeddings matrix from current memories"""
        self.memory_ids = []
        embeddings_list = []
        
        for memory_id, memory in self.memory_index.items():
            if memory.embeddings is not None:
                self.memory_ids.append(memory_id)
                embeddings_list.append(memory.embeddings)
        
        if embeddings_list:
            self.embeddings_matrix = np.vstack(embeddings_list)
        else:
            self.embeddings_matrix = None
    
    def _save_memory(self, memory: EpisodicMemory):
        """Save memory to disk"""
        memory_file = self.storage_path / f"{memory.id}.pkl"
        with open(memory_file, 'wb') as f:
            pickle.dump(memory, f)
    
    def _load_memories(self):
        """Load memories from disk"""
        for memory_file in self.storage_path.glob("ep_*.pkl"):
            try:
                with open(memory_file, 'rb') as f:
                    memory = pickle.load(f)
                    self.memory_index[memory.id] = memory
            except Exception as e:
                logger.error(f"Error loading memory {memory_file}: {e}")
        
        # Rebuild embeddings matrix
        self._rebuild_embeddings_matrix()
        
        logger.info(f"Loaded {len(self.memory_index)} episodic memories")


class SemanticMemoryLayer(MemoryLayer):
    """
    Semantic memory - general knowledge and concepts
    
    Stores learned facts, relationships, and concepts extracted from experiences.
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Knowledge graph representation
        self.concepts: Dict[str, SemanticMemory] = {}
        self.concept_relationships: Dict[str, Dict[str, Set[str]]] = {}
        
        # Concept embeddings for similarity
        self.concept_embeddings: Dict[str, np.ndarray] = {}
        
        # Load existing knowledge
        self._load_knowledge_graph()
    
    async def store(self, knowledge: Dict[str, Any]) -> bool:
        """Store extracted knowledge as semantic memory"""
        concept_id = knowledge.get('concept_id', f"sem_{datetime.now().timestamp()}")
        concept_name = knowledge.get('concept', 'unknown')
        
        # Create or update semantic memory
        if concept_id in self.concepts:
            # Update existing concept
            memory = self.concepts[concept_id]
            memory.properties.update(knowledge.get('properties', {}))
            memory.confidence = min(1.0, memory.confidence + 0.1)
            memory.source_episodes.extend(knowledge.get('source_episodes', []))
        else:
            # Create new concept
            memory = SemanticMemory(
                id=concept_id,
                timestamp=datetime.now(),
                content=knowledge,
                concept=concept_name,
                properties=knowledge.get('properties', {}),
                relationships=knowledge.get('relationships', {}),
                confidence=knowledge.get('confidence', 0.5),
                source_episodes=knowledge.get('source_episodes', [])
            )
            self.concepts[concept_id] = memory
        
        # Update relationships
        for rel_type, related_concepts in memory.relationships.items():
            if concept_id not in self.concept_relationships:
                self.concept_relationships[concept_id] = {}
            
            if rel_type not in self.concept_relationships[concept_id]:
                self.concept_relationships[concept_id][rel_type] = set()
            
            self.concept_relationships[concept_id][rel_type].update(related_concepts)
        
        # Generate embeddings if needed
        if 'embeddings' in knowledge:
            self.concept_embeddings[concept_id] = knowledge['embeddings']
        
        # Persist
        self._save_concept(memory)
        
        return True
    
    async def retrieve(
        self,
        query: str,
        relationship_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SemanticMemory]:
        """Retrieve concepts by query or relationship"""
        results = []
        
        # Direct concept lookup
        for concept_id, memory in self.concepts.items():
            if query.lower() in memory.concept.lower():
                results.append(memory)
        
        # Relationship-based retrieval
        if relationship_type:
            for concept_id, relationships in self.concept_relationships.items():
                if relationship_type in relationships:
                    related_ids = relationships[relationship_type]
                    for related_id in related_ids:
                        if related_id in self.concepts:
                            results.append(self.concepts[related_id])
        
        # Sort by confidence and limit
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Record access
        for memory in results[:limit]:
            memory.access()
        
        return results[:limit]
    
    async def forget(self, threshold: float) -> int:
        """Forget concepts below confidence threshold"""
        to_remove = []
        
        for concept_id, memory in self.concepts.items():
            # Low confidence or low strength
            if memory.confidence < threshold or memory.get_strength() < threshold:
                to_remove.append(concept_id)
        
        for concept_id in to_remove:
            # Remove from concepts
            del self.concepts[concept_id]
            
            # Remove from relationships
            if concept_id in self.concept_relationships:
                del self.concept_relationships[concept_id]
            
            # Remove from embeddings
            if concept_id in self.concept_embeddings:
                del self.concept_embeddings[concept_id]
            
            # Remove from disk
            concept_file = self.storage_path / f"{concept_id}.json"
            if concept_file.exists():
                concept_file.unlink()
        
        return len(to_remove)
    
    def get_concept_graph(self, root_concept: str, depth: int = 2) -> Dict[str, Any]:
        """Get subgraph centered on a concept"""
        if root_concept not in self.concepts:
            return {}
        
        visited = set()
        graph = {'nodes': [], 'edges': []}
        
        def explore(concept_id: str, current_depth: int):
            if current_depth > depth or concept_id in visited:
                return
            
            visited.add(concept_id)
            
            if concept_id in self.concepts:
                memory = self.concepts[concept_id]
                graph['nodes'].append({
                    'id': concept_id,
                    'label': memory.concept,
                    'properties': memory.properties,
                    'confidence': memory.confidence
                })
                
                # Explore relationships
                if concept_id in self.concept_relationships:
                    for rel_type, related_ids in self.concept_relationships[concept_id].items():
                        for related_id in related_ids:
                            graph['edges'].append({
                                'source': concept_id,
                                'target': related_id,
                                'type': rel_type
                            })
                            explore(related_id, current_depth + 1)
        
        explore(root_concept, 0)
        return graph
    
    def _save_concept(self, memory: SemanticMemory):
        """Save concept to disk"""
        concept_file = self.storage_path / f"{memory.id}.json"
        
        # Convert to JSON-serializable format
        data = {
            'id': memory.id,
            'timestamp': memory.timestamp.isoformat(),
            'concept': memory.concept,
            'properties': memory.properties,
            'relationships': memory.relationships,
            'confidence': memory.confidence,
            'source_episodes': memory.source_episodes,
            'access_count': memory.access_count,
            'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None
        }
        
        with open(concept_file, 'w') as f:
            json.dump(data, f)
    
    def _load_knowledge_graph(self):
        """Load knowledge graph from disk"""
        for concept_file in self.storage_path.glob("sem_*.json"):
            try:
                with open(concept_file, 'r') as f:
                    data = json.load(f)
                
                memory = SemanticMemory(
                    id=data['id'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    content=data,
                    concept=data['concept'],
                    properties=data['properties'],
                    relationships=data['relationships'],
                    confidence=data['confidence'],
                    source_episodes=data['source_episodes']
                )
                
                if data['last_accessed']:
                    memory.last_accessed = datetime.fromisoformat(data['last_accessed'])
                memory.access_count = data.get('access_count', 0)
                
                self.concepts[memory.id] = memory
                
                # Rebuild relationships
                for rel_type, related_ids in memory.relationships.items():
                    if memory.id not in self.concept_relationships:
                        self.concept_relationships[memory.id] = {}
                    
                    if rel_type not in self.concept_relationships[memory.id]:
                        self.concept_relationships[memory.id][rel_type] = set()
                    
                    self.concept_relationships[memory.id][rel_type].update(related_ids)
                    
            except Exception as e:
                  logger.error(f"Error loading concept {concept_file}: {e}")
        
        logger.info(f"Loaded {len(self.concepts)} semantic concepts")


class ProceduralMemoryLayer(MemoryLayer):
    """
    Procedural memory - learned skills and patterns
    
    Stores successful action sequences and behavioral patterns.
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Skills library
        self.skills: Dict[str, ProceduralMemory] = {}
        self.skill_patterns: Dict[str, List[str]] = {}  # pattern -> skill_ids
        
        # Load existing skills
        self._load_skills()
    
    async def store(self, skill_data: Dict[str, Any]) -> bool:
        """Store learned skill or pattern"""
        skill_id = skill_data.get('skill_id', f"proc_{datetime.now().timestamp()}")
        skill_name = skill_data.get('skill_name', 'unknown_skill')
        
        # Create or update procedural memory
        if skill_id in self.skills:
            # Update existing skill
            memory = self.skills[skill_id]
            memory.usage_count += 1
            
            # Update success rate
            if 'success' in skill_data:
                old_rate = memory.success_rate
                memory.success_rate = (
                    (old_rate * memory.usage_count + skill_data['success']) /
                    (memory.usage_count + 1)
                )
            
            # Add refinement
            if 'refinement' in skill_data:
                memory.refinements.append({
                    'timestamp': datetime.now().isoformat(),
                    'refinement': skill_data['refinement']
                })
        else:
            # Create new skill
            memory = ProceduralMemory(
                id=skill_id,
                timestamp=datetime.now(),
                content=skill_data,
                skill_name=skill_name,
                trigger_conditions=skill_data.get('trigger_conditions', {}),
                action_sequence=skill_data.get('action_sequence', []),
                success_rate=skill_data.get('success_rate', 0.5),
                usage_count=1
            )
            self.skills[skill_id] = memory
        
        # Index by pattern
        pattern = self._extract_pattern(memory.trigger_conditions)
        if pattern not in self.skill_patterns:
            self.skill_patterns[pattern] = []
        
        if skill_id not in self.skill_patterns[pattern]:
            self.skill_patterns[pattern].append(skill_id)
        
        # Persist
        self._save_skill(memory)
        
        return True
    
    async def retrieve(
        self,
        context: Dict[str, Any],
        min_success_rate: float = 0.6
    ) -> List[ProceduralMemory]:
        """Retrieve applicable skills for given context"""
        applicable_skills = []
        
        # Find skills matching context
        for skill_id, memory in self.skills.items():
            if self._matches_context(memory.trigger_conditions, context):
                if memory.success_rate >= min_success_rate:
                    applicable_skills.append(memory)
        
        # Sort by success rate and usage
        applicable_skills.sort(
            key=lambda x: (x.success_rate, x.usage_count),
            reverse=True
        )
        
        # Record access
        for memory in applicable_skills:
            memory.access()
        
        return applicable_skills
    
    async def forget(self, threshold: float) -> int:
        """Forget skills below success threshold"""
        to_remove = []
        
        for skill_id, memory in self.skills.items():
            # Low success rate or rarely used
            if memory.success_rate < threshold and memory.usage_count < 3:
                to_remove.append(skill_id)
        
        for skill_id in to_remove:
            # Remove from skills
            del self.skills[skill_id]
            
            # Remove from patterns
            for pattern, skill_ids in self.skill_patterns.items():
                if skill_id in skill_ids:
                    skill_ids.remove(skill_id)
            
            # Remove from disk
            skill_file = self.storage_path / f"{skill_id}.json"
            if skill_file.exists():
                skill_file.unlink()
        
        return len(to_remove)
    
    def _extract_pattern(self, trigger_conditions: Dict[str, Any]) -> str:
        """Extract pattern key from trigger conditions"""
        # Simple pattern extraction - could be more sophisticated
        keys = sorted(trigger_conditions.keys())
        return "_".join(keys)
    
    def _matches_context(
        self,
        trigger_conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if trigger conditions match context"""
        for key, value in trigger_conditions.items():
            if key not in context:
                return False
            
            # Simple matching - could be enhanced with fuzzy matching
            if isinstance(value, dict) and 'operator' in value:
                # Handle operators like >, <, contains, etc.
                op = value['operator']
                target = value['value']
                
                if op == 'contains' and target not in context[key]:
                    return False
                elif op == '>' and context[key] <= target:
                    return False
                elif op == '<' and context[key] >= target:
                    return False
            elif context[key] != value:
                return False
        
        return True
    
    def _save_skill(self, memory: ProceduralMemory):
        """Save skill to disk"""
        skill_file = self.storage_path / f"{memory.id}.json"
        
        # Convert to JSON-serializable format
        data = {
            'id': memory.id,
            'timestamp': memory.timestamp.isoformat(),
            'skill_name': memory.skill_name,
            'trigger_conditions': memory.trigger_conditions,
            'action_sequence': memory.action_sequence,
            'success_rate': memory.success_rate,
            'usage_count': memory.usage_count,
            'refinements': memory.refinements,
            'access_count': memory.access_count,
            'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None
        }
        
        with open(skill_file, 'w') as f:
            json.dump(data, f)
    
    def _load_skills(self):
        """Load skills from disk"""
        for skill_file in self.storage_path.glob("proc_*.json"):
            try:
                with open(skill_file, 'r') as f:
                    data = json.load(f)
                
                memory = ProceduralMemory(
                    id=data['id'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    content=data,
                    skill_name=data['skill_name'],
                    trigger_conditions=data['trigger_conditions'],
                    action_sequence=data['action_sequence'],
                    success_rate=data['success_rate'],
                    usage_count=data['usage_count'],
                    refinements=data.get('refinements', [])
                )
                
                if data['last_accessed']:
                    memory.last_accessed = datetime.fromisoformat(data['last_accessed'])
                memory.access_count = data.get('access_count', 0)
                
                self.skills[memory.id] = memory
                
                # Index by pattern
                pattern = self._extract_pattern(memory.trigger_conditions)
                if pattern not in self.skill_patterns:
                    self.skill_patterns[pattern] = []
                self.skill_patterns[pattern].append(memory.id)
                
            except Exception as e:
                logger.error(f"Error loading skill {skill_file}: {e}")
        
        logger.info(f"Loaded {len(self.skills)} procedural skills")


class MinionMemorySystem:
    """
    Comprehensive memory system orchestrating all memory layers
    
    Manages the flow of information through working, short-term,
    episodic, semantic, and procedural memory layers.
    """
    
    def __init__(
        self,
        minion_id: str,
        storage_base_path: Path,
        embedding_model: Optional[Any] = None
    ):
        self.minion_id = minion_id
        self.storage_base_path = Path(storage_base_path) / minion_id
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory layers
        self.working_memory = WorkingMemory(capacity=7)
        
        self.short_term_memory = ShortTermMemory(
            ttl_minutes=30,
            max_items=100
        )
        
        self.episodic_memory = EpisodicMemoryLayer(
            storage_path=self.storage_base_path / "episodic",
            embedding_model=embedding_model,
            index_dimensions=768
        )
        
        self.semantic_memory = SemanticMemoryLayer(
            storage_path=self.storage_base_path / "semantic"
        )
        
        self.procedural_memory = ProceduralMemoryLayer(
            storage_path=self.storage_base_path / "procedural"
        )
        
        # Memory consolidator
        self.consolidator = MemoryConsolidator(self)
        
        logger.info(f"Initialized memory system for {minion_id}")
    
    async def store_experience(self, experience: Experience):
        """
        Store experience across appropriate memory layers
        
        Flows through working -> short-term -> episodic/semantic/procedural
        """
        # Always goes to working memory
        await self.working_memory.store(experience)
        
        # Always goes to short-term
        await self.short_term_memory.store(experience)
        
        # Episodic if significant
        if experience.is_significant:
            stored = await self.episodic_memory.store(experience)
            if stored:
                logger.debug(f"Stored significant experience in episodic memory")
        
        # Extract semantic knowledge
        knowledge = await self._extract_knowledge(experience)
        if knowledge:
            await self.semantic_memory.store(knowledge)
            logger.debug(f"Extracted and stored knowledge: {knowledge.get('concept')}")
        
        # Learn procedural patterns
        if 'task_completion' in experience.context:
            skill_data = await self._extract_skill_pattern(experience)
            if skill_data:
                await self.procedural_memory.store(skill_data)
                logger.debug(f"Learned skill: {skill_data.get('skill_name')}")
    
    async def retrieve_relevant(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Any]]:
        """
        Retrieve relevant memories from all layers
        
        Returns memories organized by layer type.
        """
        results = {
            'working': [],
            'short_term': [],
            'episodic': [],
            'semantic': [],
            'procedural': []
        }
        
        # Working memory - all recent items
        results['working'] = await self.working_memory.retrieve(query)
        
        # Short-term - recent relevant items
        st_memories = await self.short_term_memory.retrieve(query)
        results['short_term'] = st_memories[:5]
        
        # Episodic - semantically similar experiences
        if query:
            ep_memories = await self.episodic_memory.retrieve(query, limit=5)
            results['episodic'] = ep_memories
        
        # Semantic - related concepts
        if query:
            concepts = await self.semantic_memory.retrieve(query, limit=5)
            results['semantic'] = concepts
        
        # Procedural - applicable skills
        if context:
            skills = await self.procedural_memory.retrieve(context)
            results['procedural'] = skills[:3]
        
        return results
    
    async def consolidate(self):
        """Run memory consolidation process"""
        await self.consolidator.consolidate_memories()
    
    async def forget(self, aggressive: bool = False):
        """
        Forget low-importance memories
        
        Args:
            aggressive: If True, use lower thresholds
        """
        threshold = 0.3 if aggressive else 0.5
        
        forgotten = {
            'short_term': 0,
            'episodic': 0,
            'semantic': 0,
            'procedural': 0
        }
        
        # Short-term cleanup
        forgotten['short_term'] = await self.short_term_memory.forget(threshold)
        
        # Episodic cleanup
        forgotten['episodic'] = await self.episodic_memory.forget(threshold)
        
        # Semantic cleanup (higher threshold - knowledge is valuable)
        forgotten['semantic'] = await self.semantic_memory.forget(threshold + 0.2)
        
        # Procedural cleanup (only forget failed skills)
        forgotten['procedural'] = await self.procedural_memory.forget(0.4)
        
        logger.info(f"Forgot memories: {forgotten}")
        
        return forgotten
    
    async def _extract_knowledge(self, experience: Experience) -> Optional[Dict[str, Any]]:
        """Extract semantic knowledge from experience"""
        # Simple extraction based on tags and context
        if 'learned' in experience.tags or 'discovery' in experience.tags:
            return {
                'concept_id': f"sem_{hash(experience.content)}",
                'concept': experience.context.get('concept', 'unknown'),
                'properties': experience.context.get('properties', {}),
                'relationships': experience.context.get('relationships', {}),
                'confidence': experience.significance,
                'source_episodes': [f"ep_{experience.timestamp.timestamp()}"]
            }
        
        return None
    
    async def _extract_skill_pattern(self, experience: Experience) -> Optional[Dict[str, Any]]:
        """Extract procedural pattern from task completion"""
        task_data = experience.context.get('task_completion', {})
        
        if task_data.get('success', False):
            return {
                'skill_id': f"proc_{hash(task_data.get('task_type', ''))}",
                'skill_name': task_data.get('task_type', 'unknown_task'),
                'trigger_conditions': task_data.get('initial_conditions', {}),
                'action_sequence': task_data.get('actions', []),
                'success_rate': 1.0,
                'success': True
            }
        
        return None
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        return {
            'working_memory': {
                'items': len(self.working_memory.items),
                'capacity': self.working_memory.capacity
            },
            'short_term_memory': {
                'items': len(self.short_term_memory.items),
                'max_items': self.short_term_memory.max_items
            },
            'episodic_memory': {
                'items': len(self.episodic_memory.memory_index)
            },
            'semantic_memory': {
                'concepts': len(self.semantic_memory.concepts),
                'relationships': sum(
                    len(rels) for rels in self.semantic_memory.concept_relationships.values()
                )
            },
            'procedural_memory': {
                'skills': len(self.procedural_memory.skills),
                'patterns': len(self.procedural_memory.skill_patterns)
            }
        }


class MemoryConsolidator:
    """
    Manages memory consolidation and transfer between layers
    
    Implements sleep-like consolidation processes that:
    - Move important short-term memories to episodic
    - Extract patterns from episodic memories to semantic
    - Generalize successful procedures
    """
    
    def __init__(self, memory_system: MinionMemorySystem):
        self.memory_system = memory_system
        self._last_consolidation = datetime.now()
    
    async def consolidate_memories(self):
        """Run full consolidation process"""
        logger.info(f"Starting memory consolidation for {self.memory_system.minion_id}")
        
        # Step 1: Short-term to episodic
        await self._promote_short_term_memories()
        
        # Step 2: Pattern extraction for semantic memory
        await self._extract_semantic_patterns()
        
        # Step 3: Skill generalization for procedural memory  
        await self._generalize_skills()
        
        # Step 4: Forgetting curve application
        await self._apply_forgetting_curve()
        
        self._last_consolidation = datetime.now()
        
        logger.info("Memory consolidation complete")
    
    async def _promote_short_term_memories(self):
        """Move important short-term memories to episodic"""
        important = self.memory_system.short_term_memory.get_important_memories()
        
        promoted = 0
        for memory_item in important:
            if isinstance(memory_item.content, Experience):
                stored = await self.memory_system.episodic_memory.store(
                    memory_item.content
                )
                if stored:
                    promoted += 1
        
        logger.debug(f"Promoted {promoted} memories to episodic storage")
    
    async def _extract_semantic_patterns(self):
        """Extract semantic knowledge from episodic patterns"""
        # Get recent episodic memories
        recent_memories = []
        for memory in self.memory_system.episodic_memory.memory_index.values():
            if (datetime.now() - memory.timestamp).days < 7:
                recent_memories.append(memory)
        
        # Group by similarity (simplified - would use embeddings)
        memory_groups = self._group_similar_memories(recent_memories)
        
        # Extract patterns from groups
        for group in memory_groups:
            if len(group) >= 3:  # Need multiple instances
                pattern = self._extract_pattern_from_group(group)
                if pattern:
                    await self.memory_system.semantic_memory.store(pattern)
    
    async def _generalize_skills(self):
        """Generalize successful procedural patterns"""
        skills = list(self.memory_system.procedural_memory.skills.values())
        
        # Group similar skills
        skill_groups = self._group_similar_skills(skills)
        
        for group in skill_groups:
            if len(group) >= 2:
                # All skills in group successful?
                avg_success = sum(s.success_rate for s in group) / len(group)
                
                if avg_success > 0.8:
                    # Create generalized skill
                    generalized = self._generalize_skill_group(group)
                    if generalized:
                        await self.memory_system.procedural_memory.store(generalized)
    
    async def _apply_forgetting_curve(self):
        """Apply forgetting curve to all memory layers"""
        now = datetime.now()
        time_since_last = (now - self._last_consolidation).total_seconds() / 3600
        
        # More aggressive forgetting for older consolidations
        if time_since_last > 24:
            await self.memory_system.forget(aggressive=True)
        else:
            await self.memory_system.forget(aggressive=False)
    
    def _group_similar_memories(
        self,
        memories: List[EpisodicMemory]
    ) -> List[List[EpisodicMemory]]:
        """Group memories by similarity (simplified)"""
        # In production, would use embeddings and clustering
        groups = []
        
        for memory in memories:
            placed = False
            
            for group in groups:
                # Simple tag-based similarity
                if self._memories_similar(memory, group[0]):
                    group.append(memory)
                    placed = True
                    break
            
            if not placed:
                groups.append([memory])
        
        return groups
    
    def _memories_similar(
        self,
        mem1: EpisodicMemory,
        mem2: EpisodicMemory
    ) -> bool:
        """Check if two memories are similar"""
        # Simple implementation - check tag overlap
        if hasattr(mem1.experience, 'tags') and hasattr(mem2.experience, 'tags'):
            tags1 = set(mem1.experience.tags)
            tags2 = set(mem2.experience.tags)
            
            overlap = len(tags1.intersection(tags2))
            return overlap >= 2
        
        return False
    
    def _extract_pattern_from_group(
        self,
        group: List[EpisodicMemory]
    ) -> Optional[Dict[str, Any]]:
        """Extract semantic pattern from memory group"""
        if not group:
            return None
        
        # Find common elements
        common_tags = None
        common_context_keys = None
        
        for memory in group:
            exp = memory.experience
            
            if hasattr(exp, 'tags'):
                tags = set(exp.tags)
                if common_tags is None:
                    common_tags = tags
                else:
                    common_tags = common_tags.intersection(tags)
            
            if exp.context:
                keys = set(exp.context.keys())
                if common_context_keys is None:
                    common_context_keys = keys
                else:
                    common_context_keys = common_context_keys.intersection(keys)
        
        if common_tags:
            return {
                'concept': f"pattern_{list(common_tags)[0]}",
                'properties': {
                    'common_tags': list(common_tags),
                    'common_context': list(common_context_keys) if common_context_keys else [],
                    'instance_count': len(group)
                },
                'relationships': {},
                'confidence': min(1.0, len(group) / 10),
                'source_episodes': [m.id for m in group]
            }
        
        return None
    
    def _group_similar_skills(
        self,
        skills: List[ProceduralMemory]
    ) -> List[List[ProceduralMemory]]:
        """Group similar skills"""
        groups = []
        
        for skill in skills:
            placed = False
            
            for group in groups:
                if self._skills_similar(skill, group[0]):
                    group.append(skill)
                    placed = True
                    break
            
            if not placed:
                groups.append([skill])
        
        return groups
    
    def _skills_similar(
        self,
        skill1: ProceduralMemory,
        skill2: ProceduralMemory
    ) -> bool:
        """Check if two skills are similar"""
        # Compare trigger conditions
        keys1 = set(skill1.trigger_conditions.keys())
        keys2 = set(skill2.trigger_conditions.keys())
        
        overlap = len(keys1.intersection(keys2))
        return overlap >= len(keys1) * 0.7  # 70% overlap
    
    def _generalize_skill_group(
        self,
        group: List[ProceduralMemory]
    ) -> Optional[Dict[str, Any]]:
        """Create generalized skill from group"""
        if not group:
            return None
        
        # Find common trigger conditions
        common_triggers = {}
        
        for skill in group:
            for key, value in skill.trigger_conditions.items():
                if key not in common_triggers:
                    common_triggers[key] = []
                common_triggers[key].append(value)
        
        # Generalize triggers
        generalized_triggers = {}
        for key, values in common_triggers.items():
            if len(set(values)) == 1:
                # All same value
                generalized_triggers[key] = values[0]
            else:
                # Range or pattern
                if all(isinstance(v, (int, float)) for v in values):
                    generalized_triggers[key] = {
                        'operator': 'range',
                        'min': min(values),
                        'max': max(values)
                    }
        
        # Common action patterns
        # (Simplified - would do sequence alignment in production)
        common_actions = group[0].action_sequence[:3]  # First 3 actions
        
        return {
            'skill_name': f"generalized_{group[0].skill_name}",
            'trigger_conditions': generalized_triggers,
            'action_sequence': common_actions,
            'success_rate': sum(s.success_rate for s in group) / len(group),
            'refinement': f"Generalized from {len(group)} similar skills"
        }