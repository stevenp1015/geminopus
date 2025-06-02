"""
Task Domain Models - Handles task lifecycle, decomposition, and orchestration
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Status of a task in the system"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    DECOMPOSED = "decomposed"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Priority levels for tasks"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Represents a task in the system"""
    task_id: str
    title: str
    description: str
    requester_id: str  # "commander" or minion_id
    
    # Task management
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None  # minion_id
    created_by: str = "commander"  # Who created the task
    
    # Hierarchical structure
    parent_task_id: Optional[str] = None
    subtask_ids: List[str] = field(default_factory=list)
    decomposition: Optional['TaskDecomposition'] = None  # Task decomposition if complex
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Task details
    dependencies: List[str] = field(default_factory=list)  # task_ids
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Assignment history
    assignment_history: List['TaskAssignment'] = field(default_factory=list)
    
    # Results
    output: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)  # artifact_ids
    

@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    success: bool
    output: str
    artifacts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    
    @classmethod
    def from_workflow_result(cls, workflow_result: Any) -> 'TaskResult':
        """Convert ADK workflow result to TaskResult"""
        # Implementation depends on ADK result structure
        return cls(
            task_id=workflow_result.get('task_id', ''),
            success=workflow_result.get('success', False),
            output=workflow_result.get('output', ''),
            artifacts=workflow_result.get('artifacts', []),
            error_message=workflow_result.get('error', None)
        )


class TaskOrchestrationStrategy(Enum):
    """Strategy for orchestrating task execution"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class SubTask:
    """Represents a subtask within a decomposed task"""
    subtask_id: str
    parent_task_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    complexity: str = "medium"  # low, medium, high
    suggested_minion_type: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TaskDecomposition:
    """Represents the decomposition of a complex task into subtasks"""
    task_id: str
    subtasks: List[SubTask]
    strategy: TaskOrchestrationStrategy = TaskOrchestrationStrategy.SEQUENTIAL
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"


@dataclass
class TaskAssignment:
    """Represents the assignment of a task to a minion"""
    task_id: str
    minion_id: str
    assigned_at: datetime = field(default_factory=datetime.now)
    assigned_by: str = "system"
    reason: Optional[str] = None
