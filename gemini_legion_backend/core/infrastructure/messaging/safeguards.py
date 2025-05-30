"""
Communication Safeguards

Prevents runaway communication loops and ensures healthy
conversation patterns between Minions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque, Counter
import re


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    messages_per_minute: int = 10
    messages_per_hour: int = 60
    cooldown_seconds: float = 2.0


@dataclass
class ConversationHealth:
    """Health metrics for a conversation"""
    repetition_score: float  # 0.0 to 1.0
    participation_balance: float  # 0.0 to 1.0
    topic_diversity: float  # 0.0 to 1.0
    average_message_length: float
    
    @property
    def is_healthy(self) -> bool:
        """Check if conversation is healthy"""
        return (
            self.repetition_score < 0.7 and
            self.participation_balance > 0.3 and
            self.topic_diversity > 0.2
        )


@dataclass
class LoopRisk:
    """Risk assessment for communication loops"""
    pattern_type: str
    severity: float  # 0.0 to 1.0
    description: str
    mitigation: str


class RateLimiter:
    """Rate limiting for message sending"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.message_history: Dict[str, Dict[str, deque]] = {}  # minion_id -> channel_id -> timestamps
    
    def check_allowed(self, minion_id: str, channel_id: str) -> bool:
        """Check if a minion can send a message"""
        now = datetime.now()
        
        # Initialize history if needed
        if minion_id not in self.message_history:
            self.message_history[minion_id] = {}
        if channel_id not in self.message_history[minion_id]:
            self.message_history[minion_id][channel_id] = deque()
        
        history = self.message_history[minion_id][channel_id]
        
        # Clean old entries
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_hour = now - timedelta(hours=1)
        
        # Remove old timestamps
        while history and history[0] < cutoff_hour:
            history.popleft()
        
        # Count recent messages
        minute_count = sum(1 for ts in history if ts >= cutoff_minute)
        hour_count = len(history)
        
        # Check limits
        if minute_count >= self.config.messages_per_minute:
            return False
        if hour_count >= self.config.messages_per_hour:
            return False
        
        # Check cooldown
        if history and (now - history[-1]).total_seconds() < self.config.cooldown_seconds:
            return False
        
        # Add timestamp
        history.append(now)
        return True


class ConversationMonitor:
    """Monitors conversation health metrics"""
    
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict]] = {}  # channel_id -> messages
        self.max_history = 100
    
    def add_message(self, channel_id: str, sender: str, content: str):
        """Add a message to conversation history"""
        if channel_id not in self.conversation_history:
            self.conversation_history[channel_id] = []
        
        self.conversation_history[channel_id].append({
            'sender': sender,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Trim history
        if len(self.conversation_history[channel_id]) > self.max_history:
            self.conversation_history[channel_id] = self.conversation_history[channel_id][-self.max_history:]
    
    async def check_health(self, channel_id: str) -> ConversationHealth:
        """Check the health of a conversation"""
        history = self.conversation_history.get(channel_id, [])
        if len(history) < 5:
            # Not enough data
            return ConversationHealth(0.0, 1.0, 1.0, 50.0)
        
        # Calculate repetition score
        repetition_score = self._calculate_repetition(history)
        
        # Calculate participation balance
        participation_balance = self._calculate_participation_balance(history)
        
        # Calculate topic diversity
        topic_diversity = self._calculate_topic_diversity(history)
        
        # Calculate average message length
        avg_length = sum(len(msg['content']) for msg in history) / len(history)
        
        return ConversationHealth(
            repetition_score=repetition_score,
            participation_balance=participation_balance,
            topic_diversity=topic_diversity,
            average_message_length=avg_length
        )
    
    def _calculate_repetition(self, history: List[Dict]) -> float:
        """Calculate how repetitive the conversation is"""
        if len(history) < 2:
            return 0.0
        
        # Check for repeated phrases
        recent_messages = [msg['content'].lower() for msg in history[-20:]]
        
        # Simple repetition detection
        repetitions = 0
        for i in range(1, len(recent_messages)):
            # Check similarity (simplified)
            if recent_messages[i] == recent_messages[i-1]:
                repetitions += 1
            elif len(set(recent_messages[i].split()) & set(recent_messages[i-1].split())) > 5:
                repetitions += 0.5
        
        return min(1.0, repetitions / len(recent_messages))
    
    def _calculate_participation_balance(self, history: List[Dict]) -> float:
        """Calculate how balanced participation is"""
        sender_counts = Counter(msg['sender'] for msg in history[-20:])
        
        if len(sender_counts) < 2:
            return 0.0
        
        # Calculate entropy-like measure
        total = sum(sender_counts.values())
        proportions = [count/total for count in sender_counts.values()]
        
        # Perfect balance would have equal proportions
        ideal_proportion = 1.0 / len(sender_counts)
        deviation = sum(abs(p - ideal_proportion) for p in proportions)
        
        return max(0.0, 1.0 - deviation)
    
    def _calculate_topic_diversity(self, history: List[Dict]) -> float:
        """Calculate diversity of topics discussed"""
        # Simple keyword-based topic detection
        keywords = []
        for msg in history[-20:]:
            words = re.findall(r'\b\w{4,}\b', msg['content'].lower())
            keywords.extend(words)
        
        if not keywords:
            return 0.0
        
        # Unique keywords ratio
        unique_ratio = len(set(keywords)) / len(keywords)
        return min(1.0, unique_ratio * 2)  # Scale up


class LoopPattern:
    """Base class for loop pattern detection"""
    
    def evaluate(self, minion_id: str, message: str, history: List[Dict]) -> LoopRisk:
        """Evaluate if this pattern is present"""
        raise NotImplementedError


class PingPongPattern(LoopPattern):
    """Detects A says X, B says Y, A says X... patterns"""
    
    def evaluate(self, minion_id: str, message: str, history: List[Dict]) -> LoopRisk:
        if len(history) < 4:
            return LoopRisk("ping_pong", 0.0, "No pattern detected", "")
        
        # Check for alternating similar messages
        minion_messages = [
            msg['content'] for msg in history[-10:]
            if msg['sender'] == minion_id
        ]
        
        if len(minion_messages) < 2:
            return LoopRisk("ping_pong", 0.0, "No pattern detected", "")
        
        # Check similarity
        if minion_messages[-1].lower() == minion_messages[-2].lower():
            return LoopRisk(
                "ping_pong",
                0.8,
                "Repeating same message in alternating pattern",
                "Vary your responses or wait before responding"
            )
        
        return LoopRisk("ping_pong", 0.0, "No pattern detected", "")


class EscalatingPattern(LoopPattern):
    """Detects increasingly intense exchanges"""
    
    def evaluate(self, minion_id: str, message: str, history: List[Dict]) -> LoopRisk:
        if len(history) < 5:
            return LoopRisk("escalating", 0.0, "No pattern detected", "")
        
        # Check for increasing exclamation marks or caps
        recent = history[-5:]
        intensity_scores = []
        
        for msg in recent:
            score = 0
            score += msg['content'].count('!')
            score += msg['content'].count('?')
            score += sum(1 for c in msg['content'] if c.isupper()) / max(1, len(msg['content']))
            intensity_scores.append(score)
        
        # Check if intensity is increasing
        if all(intensity_scores[i] <= intensity_scores[i+1] for i in range(len(intensity_scores)-1)):
            if intensity_scores[-1] > intensity_scores[0] * 1.5:
                return LoopRisk(
                    "escalating",
                    0.7,
                    "Conversation intensity escalating rapidly",
                    "Take a step back and calm the tone"
                )
        
        return LoopRisk("escalating", 0.0, "No pattern detected", "")


class LoopPatternDetector:
    """Detects communication patterns that indicate loops"""
    
    def __init__(self):
        self.pattern_library = [
            PingPongPattern(),
            EscalatingPattern(),
            # More patterns can be added
        ]
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    def add_to_history(self, channel_id: str, sender: str, content: str):
        """Add message to history for analysis"""
        if channel_id not in self.conversation_history:
            self.conversation_history[channel_id] = []
        
        self.conversation_history[channel_id].append({
            'sender': sender,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.conversation_history[channel_id]) > 50:
            self.conversation_history[channel_id] = self.conversation_history[channel_id][-50:]
    
    async def assess_loop_risk(
        self,
        minion_id: str,
        channel_id: str,
        message: str
    ) -> LoopRisk:
        """Assess risk of communication loop"""
        history = self.conversation_history.get(channel_id, [])
        
        # Evaluate each pattern
        risks = []
        for pattern in self.pattern_library:
            risk = pattern.evaluate(minion_id, message, history)
            risks.append(risk)
        
        # Return highest risk
        return max(risks, key=lambda r: r.severity)


class CommunicationSafeguards:
    """
    Prevents runaway communication loops
    
    Integrates rate limiting, pattern detection, and health monitoring
    to ensure healthy communication patterns.
    """
    
    MAX_REPETITION = 0.7
    LOOP_RISK_THRESHOLD = 0.6
    
    def __init__(self):
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.pattern_detector = LoopPatternDetector()
        self.conversation_monitor = ConversationMonitor()
    
    async def check_message_allowed(
        self,
        minion_id: str,
        channel_id: str,
        message: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if message should be allowed
        
        Returns:
            Tuple of (allowed, reason_if_denied)
        """
        # Rate limiting
        if not self.rate_limiter.check_allowed(minion_id, channel_id):
            return False, "Rate limit exceeded"
        
        # Pattern detection
        self.pattern_detector.add_to_history(channel_id, minion_id, message)
        loop_risk = await self.pattern_detector.assess_loop_risk(
            minion_id, channel_id, message
        )
        
        if loop_risk.severity > self.LOOP_RISK_THRESHOLD:
            return False, f"Potential loop detected: {loop_risk.description}"
        
        # Conversation health monitoring
        self.conversation_monitor.add_message(channel_id, minion_id, message)
        health = await self.conversation_monitor.check_health(channel_id)
        
        if health.repetition_score > self.MAX_REPETITION:
            return False, "Conversation becoming too repetitive"
        
        return True, None
