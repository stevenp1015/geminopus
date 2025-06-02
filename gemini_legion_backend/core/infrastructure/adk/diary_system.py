"""
Personal Diary System

Rich narrative logs that supplement structured emotional state,
providing searchable memory and introspection capabilities.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import asyncio
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from ...domain import EmotionalState, MoodVector


logger = logging.getLogger(__name__)


class DiaryEntryType(Enum):
    """Types of diary entries"""
    INTERACTION = "interaction"
    REFLECTION = "reflection"
    OBSERVATION = "observation"
    ACHIEVEMENT = "achievement"
    FRUSTRATION = "frustration"
    DISCOVERY = "discovery"
    RELATIONSHIP = "relationship"
    TASK_COMPLETION = "task_completion"
    EMOTIONAL_EVENT = "emotional_event"
    SYSTEM_EVENT = "system_event"


@dataclass
class DiaryEntry:
    """A single diary entry with context and metadata"""
    minion_id: str
    timestamp: datetime
    entry_type: DiaryEntryType
    content: str
    emotional_snapshot: Dict[str, Any]  # Serialized emotional state
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[np.ndarray] = None
    importance: float = 0.5  # 0-1 scale
    tags: List[str] = field(default_factory=list)


class DiaryStorage:
    """
    Handles persistent storage of diary entries
    
    Stores entries as JSON files with embeddings in separate numpy files.
    """
    
    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize diary storage
        
        Args:
            base_path: Base directory for diary storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings model (lightweight)
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embeddings_enabled = True
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.embeddings_enabled = False
    
    async def save_entry(self, entry: DiaryEntry):
        """Save a diary entry to disk"""
        # Create minion-specific directory
        minion_dir = self.base_path / entry.minion_id
        minion_dir.mkdir(exist_ok=True)
        
        # Generate filename based on timestamp
        filename = f"{entry.timestamp.strftime('%Y%m%d_%H%M%S')}_{entry.entry_type.value}.json"
        filepath = minion_dir / filename
        
        # Prepare entry data
        entry_data = {
            "minion_id": entry.minion_id,
            "timestamp": entry.timestamp.isoformat(),
            "entry_type": entry.entry_type.value,
            "content": entry.content,
            "emotional_snapshot": entry.emotional_snapshot,
            "metadata": entry.metadata,
            "importance": entry.importance,
            "tags": entry.tags
        }
        
        # Save JSON
        with open(filepath, 'w') as f:
            json.dump(entry_data, f, indent=2)
        
        # Save embeddings if available
        if entry.embeddings is not None:
            embeddings_path = filepath.with_suffix('.npy')
            np.save(embeddings_path, entry.embeddings)
        
        logger.debug(f"Saved diary entry: {filepath}")
    
    async def load_entries(
        self,
        minion_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entry_types: Optional[List[DiaryEntryType]] = None
    ) -> List[DiaryEntry]:
        """Load diary entries with optional filtering"""
        minion_dir = self.base_path / minion_id
        
        if not minion_dir.exists():
            return []
        
        entries = []
        
        for json_file in minion_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Parse timestamp
                timestamp = datetime.fromisoformat(data["timestamp"])
                
                # Apply date filters
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                
                # Apply type filter
                entry_type = DiaryEntryType(data["entry_type"])
                if entry_types and entry_type not in entry_types:
                    continue
                
                # Load embeddings if available  
                embeddings = None
                embeddings_path = json_file.with_suffix('.npy')
                if embeddings_path.exists():
                    embeddings = np.load(embeddings_path)
                
                # Create entry
                entry = DiaryEntry(
                    minion_id=data["minion_id"],
                    timestamp=timestamp,
                    entry_type=entry_type,
                    content=data["content"],
                    emotional_snapshot=data["emotional_snapshot"],
                    metadata=data.get("metadata", {}),
                    embeddings=embeddings,
                    importance=data.get("importance", 0.5),
                    tags=data.get("tags", [])
                )
                
                entries.append(entry)
                
            except Exception as e:
                logger.error(f"Error loading diary entry {json_file}: {e}")
        
        # Sort by timestamp
        entries.sort(key=lambda e: e.timestamp)
        
        return entries


class PersonalDiary:
    """
    Rich narrative log system for Minions
    
    Provides semantic search, emotional filtering, and
    integration with the structured emotional state.
    """
    
    def __init__(
        self,
        minion_id: str,
        storage: DiaryStorage,
        auto_tag: bool = True
    ):
        """
        Initialize personal diary
        
        Args:
            minion_id: ID of the Minion
            storage: Storage backend
            auto_tag: Whether to automatically tag entries
        """
        self.minion_id = minion_id
        self.storage = storage
        self.auto_tag = auto_tag
        
        # Cache recent entries for performance
        self._entry_cache: List[DiaryEntry] = []
        self._cache_size = 50
    
    async def write_entry(
        self,
        content: str,
        entry_type: DiaryEntryType,
        emotional_state: EmotionalState,
        metadata: Optional[Dict[str, Any]] = None,
        importance: Optional[float] = None
    ):
        """
        Write a new diary entry
        
        Args:
            content: The diary entry content
            entry_type: Type of entry
            emotional_state: Current emotional state
            metadata: Additional metadata
            importance: Importance score (auto-calculated if None)
        """
        # Auto-calculate importance if not provided
        if importance is None:
            importance = self._calculate_importance(
                content, entry_type, emotional_state
            )
        
        # Auto-generate tags
        tags = []
        if self.auto_tag:
            tags = self._generate_tags(content, entry_type, metadata)
        
        # Generate embeddings
        embeddings = None
        if self.storage.embeddings_enabled:
            embeddings = await self._generate_embeddings(content)
        
        # Create entry
        entry = DiaryEntry(
            minion_id=self.minion_id,
            timestamp=datetime.now(),
            entry_type=entry_type,
            content=content,
            emotional_snapshot=emotional_state.to_snapshot(),
            metadata=metadata or {},
            embeddings=embeddings,
            importance=importance,
            tags=tags
        )
        
        # Save to storage
        await self.storage.save_entry(entry)
        
        # Update cache
        self._update_cache(entry)
        
        logger.info(f"Minion {self.minion_id} wrote {entry_type.value} diary entry")
    
    async def search_memories(
        self,
        query: str,
        emotional_filter: Optional[MoodVector] = None,
        time_range: Optional[timedelta] = None,
        entry_types: Optional[List[DiaryEntryType]] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[DiaryEntry]:
        """
        Search through diary with semantic and emotional filtering
        
        Args:
            query: Search query
            emotional_filter: Filter by similar emotional state
            time_range: Time range to search within
            entry_types: Types of entries to include
            min_importance: Minimum importance threshold
            limit: Maximum results to return
            
        Returns:
            List of matching diary entries
        """
        # Determine date range
        end_date = datetime.now()
        start_date = end_date - time_range if time_range else None
        
        # Load candidate entries
        entries = await self.storage.load_entries(
            self.minion_id,
            start_date=start_date,
            end_date=end_date,
            entry_types=entry_types
        )
        
        # Filter by importance
        entries = [e for e in entries if e.importance >= min_importance]
        
        # Semantic search if embeddings available
        if self.storage.embeddings_enabled and query:
            query_embedding = await self._generate_embeddings(query)
            
            # Calculate similarities
            similarities = []
            for entry in entries:
                if entry.embeddings is not None:
                    similarity = self._cosine_similarity(
                        query_embedding, entry.embeddings
                    )
                    similarities.append((entry, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            entries = [e for e, _ in similarities[:limit*2]]  # Get more for emotional filtering
        
        # Emotional filtering
        if emotional_filter:
            emotionally_similar = []
            
            for entry in entries:
                mood_data = entry.emotional_snapshot.get("mood", {})
                if mood_data:
                    entry_mood = MoodVector(**mood_data)
                    distance = emotional_filter.distance_to(entry_mood)
                    
                    # Include if emotionally similar (lower distance is better)
                    if distance < 0.5:
                        emotionally_similar.append((entry, distance))
            
            # Sort by emotional similarity
            emotionally_similar.sort(key=lambda x: x[1])
            entries = [e for e, _ in emotionally_similar]
        
        # Return top results
        return entries[:limit]
    
    async def get_recent_entries(
        self,
        hours: int = 24,
        entry_types: Optional[List[DiaryEntryType]] = None
    ) -> List[DiaryEntry]:
        """Get recent diary entries"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Check cache first
        recent = [
            e for e in self._entry_cache
            if e.timestamp >= cutoff and
            (not entry_types or e.entry_type in entry_types)
        ]
        
        # If not enough in cache, load from storage
        if len(recent) < 10:
            recent = await self.storage.load_entries(
                self.minion_id,
                start_date=cutoff,
                entry_types=entry_types
            )
        
        return recent
    
    async def generate_summary(
        self,
        time_range: timedelta,
        focus: Optional[str] = None
    ) -> str:
        """
        Generate a summary of diary entries
        
        Args:
            time_range: Time range to summarize
            focus: Optional focus area (e.g., "emotions", "tasks", "relationships")
            
        Returns:
            Natural language summary
        """
        entries = await self.storage.load_entries(
            self.minion_id,
            start_date=datetime.now() - time_range
        )
        
        if not entries:
            return "No diary entries found for the specified time range."
        
        # Group by type
        by_type = {}
        for entry in entries:
            if entry.entry_type not in by_type:
                by_type[entry.entry_type] = []
            by_type[entry.entry_type].append(entry)
        
        # Build summary
        summary_parts = [
            f"Diary summary for the past {time_range.days} days:"
        ]
        
        # Emotional journey
        if focus in [None, "emotions"]:
            emotional_highlights = self._summarize_emotional_journey(entries)
            if emotional_highlights:
                summary_parts.append(f"\nEmotional Journey:\n{emotional_highlights}")
        
        # Key events by type
        for entry_type, type_entries in by_type.items():
            if len(type_entries) > 0:
                summary_parts.append(
                    f"\n{entry_type.value.replace('_', ' ').title()} ({len(type_entries)} entries):"
                )
                
                # Get most important entries
                important = sorted(
                    type_entries,
                    key=lambda e: e.importance,
                    reverse=True
                )[:3]
                
                for entry in important:
                    summary_parts.append(
                        f"- {entry.content[:100]}..."
                    )
        
        return "\n".join(summary_parts)
    
    def _calculate_importance(
        self,
        content: str,
        entry_type: DiaryEntryType,
        emotional_state: EmotionalState
    ) -> float:
        """Calculate importance score for an entry"""
        importance = 0.5  # Base importance
        
        # Type-based importance
        type_weights = {
            DiaryEntryType.ACHIEVEMENT: 0.8,
            DiaryEntryType.FRUSTRATION: 0.7,
            DiaryEntryType.EMOTIONAL_EVENT: 0.7,
            DiaryEntryType.TASK_COMPLETION: 0.6,
            DiaryEntryType.DISCOVERY: 0.8,
            DiaryEntryType.RELATIONSHIP: 0.6
        }
        importance = type_weights.get(entry_type, importance)
        
        # Emotional intensity bonus
        emotional_intensity = abs(emotional_state.mood.valence) + emotional_state.stress_level
        importance += emotional_intensity * 0.1
        
        # Length bonus (longer entries often more important)
        if len(content) > 200:
            importance += 0.1
        
        # Keywords that increase importance
        important_keywords = [
            "commander", "steven", "breakthrough", "critical",
            "important", "urgent", "discovery", "realized"
        ]
        content_lower = content.lower()
        for keyword in important_keywords:
            if keyword in content_lower:
                importance += 0.05
        
        return min(1.0, importance)
    
    def _generate_tags(
        self,
        content: str,
        entry_type: DiaryEntryType,
        metadata: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Auto-generate tags for an entry"""
        tags = [entry_type.value]
        
        content_lower = content.lower()
        
        # Entity detection
        if "commander" in content_lower or "steven" in content_lower:
            tags.append("commander")
        
        # Emotion detection
        emotions = ["happy", "sad", "frustrated", "excited", "anxious", "proud"]
        for emotion in emotions:
            if emotion in content_lower:
                tags.append(f"emotion:{emotion}")
        
        # Task-related tags
        if any(word in content_lower for word in ["complete", "finish", "done"]):
            tags.append("completion")
        
        # Metadata tags
        if metadata:
            if "task_id" in metadata:
                tags.append(f"task:{metadata['task_id']}")
            if "channel" in metadata:
                tags.append(f"channel:{metadata['channel']}")
        
        return tags
    
    async def _generate_embeddings(self, text: str) -> np.ndarray:
        """Generate embeddings for text"""
        if not self.storage.embeddings_enabled:
            return None
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.storage.embedding_model.encode,
                text
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _update_cache(self, entry: DiaryEntry):
        """Update the entry cache"""
        self._entry_cache.append(entry)
        
        # Maintain cache size
        if len(self._entry_cache) > self._cache_size:
            # Keep most recent and most important
            sorted_cache = sorted(
                self._entry_cache,
                key=lambda e: (e.timestamp, e.importance),
                reverse=True
            )
            self._entry_cache = sorted_cache[:self._cache_size]
    
    def _summarize_emotional_journey(self, entries: List[DiaryEntry]) -> str:
        """Summarize emotional journey from entries"""
        if not entries:
            return ""
        
        # Track mood trajectory
        moods = []
        for entry in entries:
            mood_data = entry.emotional_snapshot.get("mood", {})
            if mood_data:
                moods.append((
                    entry.timestamp,
                    mood_data.get("valence", 0),
                    mood_data.get("arousal", 0)
                ))
        
        if not moods:
            return "Emotional data not available."
        
        # Analyze trajectory
        start_valence = moods[0][1]
        end_valence = moods[-1][1] if moods else start_valence
        
        avg_valence = sum(m[1] for m in moods) / len(moods)
        avg_arousal = sum(m[2] for m in moods) / len(moods)
        
        # Build description
        journey = []
        
        if end_valence > start_valence + 0.2:
            journey.append("Mood has significantly improved")
        elif end_valence < start_valence - 0.2:
            journey.append("Mood has declined")
        else:
            journey.append("Mood has remained relatively stable")
        
        if avg_valence > 0.3:
            journey.append("Generally positive emotional state")
        elif avg_valence < -0.3:
            journey.append("Experiencing some emotional challenges")
        
        if avg_arousal > 0.7:
            journey.append("High energy and excitement")
        elif avg_arousal < 0.3:
            journey.append("Low energy, possibly needing stimulation")
        
        return ". ".join(journey) + "."