"""
Memory-based Task Repository Implementation

In-memory implementation of TaskRepository for testing and development.
"""

from typing import List, Optional, Dict, Set
from datetime import datetime
import asyncio
from copy import deepcopy

from ..task_repository import TaskRepository
from .....domain import Task, TaskStatus, TaskPriority


class TaskRepositoryMemory(TaskRepository):
    """
    In-memory implementation of TaskRepository
    
    Stores tasks with efficient lookups by various criteria.
    """
    
    def __init__(self):
        """Initialize the in-memory storage"""
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
    
    async def save(self, entity: Task) -> Task:
        """
        Save or update a task
        
        Args:
            entity: The task to save
            
        Returns:
            The saved task
        """
        async with self._lock:
            # Deep copy to avoid external modifications
            saved_task = deepcopy(entity)
            saved_task.updated_at = datetime.now()
            
            self._tasks[entity.task_id] = saved_task
            
            return deepcopy(saved_task)
    
    async def get_by_id(self, entity_id: str) -> Optional[Task]:
        """
        Get a task by its ID
        
        Args:
            entity_id: The ID of the task
            
        Returns:
            The task if found, None otherwise
        """
        async with self._lock:
            task = self._tasks.get(entity_id)
            return deepcopy(task) if task else None
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """
        List all tasks with pagination
        
        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of tasks
        """
        async with self._lock:
            # Get all tasks sorted by creation time
            all_tasks = sorted(
                self._tasks.values(),
                key=lambda t: t.created_at,
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(t) for t in all_tasks[start:end]]
    
    async def delete(self, entity_id: str) -> bool:
        """
        Delete a task by ID
        
        Args:
            entity_id: The ID of the task to delete
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if entity_id in self._tasks:
                del self._tasks[entity_id]
                return True
            return False
    
    async def exists(self, entity_id: str) -> bool:
        """
        Check if a task exists
        
        Args:
            entity_id: The ID of the task
            
        Returns:
            True if exists, False otherwise
        """
        async with self._lock:
            return entity_id in self._tasks
    
    async def list_by_status(
        self,
        statuses: List[TaskStatus],
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        List tasks by status
        
        Args:
            statuses: List of statuses to filter by
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of tasks with the specified statuses
        """
        async with self._lock:
            # Filter by statuses
            filtered_tasks = [
                t for t in self._tasks.values()
                if t.status in statuses
            ]
            
            # Sort by priority and then creation time
            filtered_tasks.sort(
                key=lambda t: (t.priority.value, t.created_at),
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(t) for t in filtered_tasks[start:end]]
    
    async def list_by_assignee(
        self,
        assignee_id: str,
        include_subtasks: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        List tasks assigned to a specific minion
        
        Args:
            assignee_id: The ID of the assigned minion
            include_subtasks: Whether to include subtasks
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of tasks assigned to the minion
        """
        async with self._lock:
            # Filter by assignee
            filtered_tasks = []
            
            for task in self._tasks.values():
                if task.assigned_to == assignee_id:
                    filtered_tasks.append(task)
                elif include_subtasks and task.subtasks:
                    # Check if any subtask is assigned to this minion
                    for subtask_id in task.subtasks:
                        subtask = self._tasks.get(subtask_id)
                        if subtask and subtask.assigned_to == assignee_id:
                            filtered_tasks.append(task)
                            break
            
            # Sort by priority and deadline
            filtered_tasks.sort(
                key=lambda t: (
                    t.priority.value,
                    t.deadline or datetime.max
                ),
                reverse=True
            )
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(t) for t in filtered_tasks[start:end]]
    
    async def list_by_parent(
        self,
        parent_task_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        List subtasks of a parent task
        
        Args:
            parent_task_id: The ID of the parent task
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of subtasks
        """
        async with self._lock:
            # Filter by parent task
            filtered_tasks = [
                t for t in self._tasks.values()
                if t.parent_task_id == parent_task_id
            ]
            
            # Sort by creation time
            filtered_tasks.sort(key=lambda t: t.created_at)
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(t) for t in filtered_tasks[start:end]]
    
    async def list_overdue(
        self,
        as_of: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        List overdue tasks
        
        Args:
            as_of: The reference time for overdue check (defaults to now)
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of overdue tasks
        """
        async with self._lock:
            reference_time = as_of or datetime.now()
            
            # Filter overdue tasks
            overdue_tasks = [
                t for t in self._tasks.values()
                if (t.deadline and 
                    t.deadline < reference_time and
                    t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED])
            ]
            
            # Sort by how overdue they are
            overdue_tasks.sort(key=lambda t: t.deadline)
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return [deepcopy(t) for t in overdue_tasks[start:end]]
    
    async def update_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> Optional[Task]:
        """
        Update a task's status
        
        Args:
            task_id: The ID of the task
            status: The new status
            
        Returns:
            The updated task if found, None otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            
            task.status = status
            task.updated_at = datetime.now()
            
            # Update completion time if completed
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
            
            return deepcopy(task)
    
    async def list_subtasks(self, parent_task_id: str) -> List[Task]:
        """
        List subtasks of a parent task
        
        Args:
            parent_task_id: The ID of the parent task
            
        Returns:
            List of subtasks
        """
        async with self._lock:
            # Get the parent task
            parent_task = self._tasks.get(parent_task_id)
            if not parent_task:
                return []
            
            # Get all subtasks
            subtasks = []
            for subtask_id in parent_task.subtasks:
                subtask = self._tasks.get(subtask_id)
                if subtask:
                    subtasks.append(deepcopy(subtask))
            
            # Sort by creation time
            subtasks.sort(key=lambda t: t.created_at)
            
            return subtasks
    
    async def get_dependencies(self, task_id: str) -> List[Task]:
        """
        Get tasks that a specific task depends on
        
        Args:
            task_id: The ID of the task
            
        Returns:
            List of dependency tasks
        """
        async with self._lock:
            # Get the task
            task = self._tasks.get(task_id)
            if not task:
                return []
            
            # Get all dependency tasks
            dependencies = []
            for dep_id in task.dependencies:
                dep_task = self._tasks.get(dep_id)
                if dep_task:
                    dependencies.append(deepcopy(dep_task))
            
            # Sort by priority and creation time
            dependencies.sort(
                key=lambda t: (t.priority.value, t.created_at),
                reverse=True
            )
            
            return dependencies
    
    async def clear(self):
        """Clear all tasks from memory (for testing)"""
        async with self._lock:
            self._tasks.clear()