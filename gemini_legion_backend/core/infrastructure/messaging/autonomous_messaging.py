"""
Autonomous Messaging Engine

Enables Minions to initiate communication autonomously based on
their emotional state, tasks, and social reasoning.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import dataclasses


from ...domain import EmotionalState, Minion


class CommunicationNeed(Enum):
    """Types of communication needs"""
    TASK_COORDINATION = "task_coordination"
    EMOTIONAL_EXPRESSION = "emotional_expression"
    INFORMATION_SHARING = "information_sharing"
    SOCIAL_BONDING = "social_bonding"
    HELP_REQUEST = "help_request"
    STATUS_UPDATE = "status_update"


@dataclass
class AutonomousContext:
    """Context for autonomous decision making"""
    current_time: datetime
    active_tasks: List[str]
    recent_interactions: List[Dict[str, Any]]
    channel_activity: Dict[str, float]  # channel_id -> activity_level
    other_minions_status: Dict[str, str]  # minion_id -> status


@dataclass
class CommunicationNeedAnalysis:
    """Analysis of need to communicate"""
    need_type: CommunicationNeed
    urgency: float  # 0.0 to 1.0
    purpose: str
    target_recipients: List[str]
    suggested_channel: str


@dataclass
class ConversationPlan:
    """Plan for an autonomous conversation"""
    recipients: List[str]
    channel: str
    opening_message: str
    expected_turns: int
    goals: List[str]


@dataclass
class AutonomousMessage:
    """Message initiated autonomously by a Minion"""
    initiator: str
    recipients: List[str]
    purpose: CommunicationNeed
    initial_message: str
    expected_turns: int
    timestamp: datetime = dataclasses.field(default_factory=datetime.now)


class SocialReasoner:
    """Determines social appropriateness of autonomous communication"""
    
    def __init__(self):
        self.quiet_hours = (22, 7)  # 10 PM to 7 AM
        self.max_messages_per_hour = 10
        self.message_history: Dict[str, List[datetime]] = {}
    
    async def is_appropriate_time(self, minion: Minion, context: AutonomousContext) -> bool:
        """
        Check if it's socially appropriate to initiate communication
        
        Args:
            minion: The Minion considering communication
            context: Current context
            
        Returns:
            True if appropriate to communicate
        """
        current_hour = context.current_time.hour
        
        # Check quiet hours (unless urgent)
        if self.quiet_hours[0] <= current_hour or current_hour < self.quiet_hours[1]:
            # Only allow urgent communications during quiet hours
            return False
        
        # Check message rate limit
        minion_id = minion.minion_id
        if minion_id in self.message_history:
            recent_messages = [
                ts for ts in self.message_history[minion_id]
                if (context.current_time - ts).total_seconds() < 3600
            ]
            if len(recent_messages) >= self.max_messages_per_hour:
                return False
        
        # Check if others are overwhelmed
        for channel, activity in context.channel_activity.items():
            if activity > 0.8:  # Channel is very active
                return False
        
        return True


class ConversationPlanner:
    """Plans autonomous conversations"""
    
    def __init__(self):
        self.conversation_templates = {
            CommunicationNeed.TASK_COORDINATION: [
                "Hey {recipient}, I'm working on {task} and could use your input on {aspect}.",
                "Quick question about {task} - do you have a moment?",
            ],
            CommunicationNeed.EMOTIONAL_EXPRESSION: [
                "Feeling {emotion} about recent events. Anyone else experiencing this?",
                "Just wanted to share that {event} really {impact} me.",
            ],
            CommunicationNeed.SOCIAL_BONDING: [
                "How's everyone doing today?",
                "Anyone up for a quick chat? Been focused on {task} all day.",
            ],
        }
    
    async def plan(
        self,
        minion: Minion,
        need: CommunicationNeedAnalysis,
        context: AutonomousContext
    ) -> ConversationPlan:
        """
        Create a conversation plan
        
        Args:
            minion: The initiating Minion
            need: The communication need analysis
            context: Current context
            
        Returns:
            A plan for the conversation
        """
        # Select appropriate template
        templates = self.conversation_templates.get(need.need_type, [])
        template = templates[0] if templates else "Hello, I have something to discuss."
        
        # Fill template based on context
        opening_message = self._fill_template(template, minion, need, context)
        
        # Determine expected conversation length
        expected_turns = self._estimate_turns(need.need_type)
        
        # Set goals
        goals = self._determine_goals(need)
        
        return ConversationPlan(
            recipients=need.target_recipients,
            channel=need.suggested_channel,
            opening_message=opening_message,
            expected_turns=expected_turns,
            goals=goals
        )
    
    def _fill_template(
        self,
        template: str,
        minion: Minion,
        need: CommunicationNeedAnalysis,
        context: AutonomousContext
    ) -> str:
        """Fill in template with context-specific information"""
        # Simplified implementation
        replacements = {
            '{recipient}': need.target_recipients[0] if need.target_recipients else 'everyone',
            '{task}': context.active_tasks[0] if context.active_tasks else 'my current work',
            '{emotion}': self._describe_emotion(minion.emotional_state),
            '{aspect}': 'the implementation approach',
            '{event}': 'the recent feedback',
            '{impact}': 'motivated'
        }
        
        message = template
        for key, value in replacements.items():
            message = message.replace(key, value)
        
        return message
    
    def _describe_emotion(self, emotional_state: EmotionalState) -> str:
        """Describe current emotional state in words"""
        mood = emotional_state.mood
        if mood.valence > 0.5:
            return "energized and positive"
        elif mood.valence < -0.5:
            return "a bit frustrated"
        else:
            return "contemplative"
    
    def _estimate_turns(self, need_type: CommunicationNeed) -> int:
        """Estimate expected conversation length"""
        estimates = {
            CommunicationNeed.TASK_COORDINATION: 5,
            CommunicationNeed.EMOTIONAL_EXPRESSION: 3,
            CommunicationNeed.INFORMATION_SHARING: 4,
            CommunicationNeed.SOCIAL_BONDING: 6,
            CommunicationNeed.HELP_REQUEST: 8,
            CommunicationNeed.STATUS_UPDATE: 2
        }
        return estimates.get(need_type, 4)
    
    def _determine_goals(self, need: CommunicationNeedAnalysis) -> List[str]:
        """Determine conversation goals"""
        base_goals = [need.purpose]
        
        if need.need_type == CommunicationNeed.TASK_COORDINATION:
            base_goals.extend([
                "Align on approach",
                "Identify dependencies",
                "Set next steps"
            ])
        elif need.need_type == CommunicationNeed.EMOTIONAL_EXPRESSION:
            base_goals.extend([
                "Share feelings",
                "Seek understanding",
                "Build connection"
            ])
        
        return base_goals


class AutonomousMessagingEngine:
    """
    Enables Minions to initiate communication autonomously
    
    This engine analyzes context and emotional state to determine
    when and how Minions should initiate conversations.
    """
    
    def __init__(self, communication_system):
        self.comm_system = communication_system
        self.conversation_planner = ConversationPlanner()
        self.social_reasoner = SocialReasoner()
        self.active_conversations: Dict[str, AutonomousMessage] = {}
    
    async def consider_autonomous_message(
        self,
        minion: Minion,
        context: AutonomousContext
    ) -> Optional[AutonomousMessage]:
        """
        Determine if Minion should initiate communication
        
        Args:
            minion: The Minion considering communication
            context: Current context
            
        Returns:
            AutonomousMessage if communication should be initiated, None otherwise
        """
        # Check social appropriateness
        if not await self.social_reasoner.is_appropriate_time(minion, context):
            return None
        
        # Analyze need for communication
        communication_need = await self._analyze_communication_need(minion, context)
        
        if communication_need.urgency < 0.3:  # Threshold for autonomous initiation
            return None
        
        # Plan conversation
        conversation_plan = await self.conversation_planner.plan(
            minion, communication_need, context
        )
        
        # Create autonomous message
        message = AutonomousMessage(
            initiator=minion.minion_id,
            recipients=conversation_plan.recipients,
            purpose=communication_need.need_type,
            initial_message=conversation_plan.opening_message,
            expected_turns=conversation_plan.expected_turns
        )
        
        # Record for tracking
        self.active_conversations[minion.minion_id] = message
        
        return message


    
    async def _analyze_communication_need(
        self,
        minion: Minion,
        context: AutonomousContext
    ) -> CommunicationNeedAnalysis:
        """
        Analyze whether and why communication is needed
        
        Args:
            minion: The Minion to analyze
            context: Current context
            
        Returns:
            Analysis of communication need
        """
        # Base urgency on emotional state
        emotional_urgency = 0.0
        emotional_state = minion.emotional_state
        
        # High stress or low energy might trigger need for support
        if emotional_state.stress_level > 0.7:
            emotional_urgency = 0.6
            need_type = CommunicationNeed.HELP_REQUEST
            purpose = "Seeking support due to high stress"
        elif emotional_state.energy_level < 0.3:
            emotional_urgency = 0.4
            need_type = CommunicationNeed.SOCIAL_BONDING
            purpose = "Need social interaction to boost energy"
        else:
            need_type = CommunicationNeed.STATUS_UPDATE
            purpose = "Regular status check-in"
        
        # Task-based urgency
        task_urgency = 0.0
        if context.active_tasks:
            # If working on tasks, might need coordination
            task_urgency = 0.3
            if len(context.active_tasks) > 2:
                task_urgency = 0.5
                need_type = CommunicationNeed.TASK_COORDINATION
                purpose = "Coordinate on multiple active tasks"
        
        # Social factors
        social_urgency = 0.0
        if not context.recent_interactions:
            # Haven't talked to anyone recently
            social_urgency = 0.4
            if need_type == CommunicationNeed.STATUS_UPDATE:
                need_type = CommunicationNeed.SOCIAL_BONDING
                purpose = "Haven't connected with team recently"
        
        # Calculate overall urgency
        urgency = max(emotional_urgency, task_urgency, social_urgency)
        
        # Determine recipients
        if need_type == CommunicationNeed.TASK_COORDINATION:
            # Find other minions working on related tasks
            recipients = self._find_task_collaborators(minion, context)
        elif need_type in [CommunicationNeed.EMOTIONAL_EXPRESSION, CommunicationNeed.SOCIAL_BONDING]:
            # Talk to minions with good relationships
            recipients = self._find_friendly_minions(minion, context)
        else:
            # General broadcast
            recipients = ["all"]
        
        # Suggest channel
        if urgency > 0.7:
            channel = "#urgent"
        elif need_type == CommunicationNeed.SOCIAL_BONDING:
            channel = "#random"
        else:
            channel = "#general"
        
        return CommunicationNeedAnalysis(
            need_type=need_type,
            urgency=urgency,
            purpose=purpose,
            target_recipients=recipients,
            suggested_channel=channel
        )
    
    def _find_task_collaborators(self, minion: Minion, context: AutonomousContext) -> List[str]:
        """Find other minions who might be working on related tasks"""
        # Simplified - in real implementation would check task assignments
        collaborators = []
        for other_id, status in context.other_minions_status.items():
            if status == "active" and other_id != minion.minion_id:
                collaborators.append(other_id)
        return collaborators[:2]  # Limit to 2 collaborators
    
    def _find_friendly_minions(self, minion: Minion, context: AutonomousContext) -> List[str]:
        """Find minions with positive relationships"""
        friendly = []
        for entity_id, opinion in minion.emotional_state.opinion_scores.items():
            if opinion.overall_sentiment > 60 and entity_id != "commander":
                friendly.append(entity_id)
        return friendly[:3]  # Limit to 3 friends
