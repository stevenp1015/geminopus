"""
Task Repository Interface

This module defines the repository interface for Task entities.
"""

from typing import List, Optional
from abc import abstractmethod

from .base import Repository
from ....domain import Task, TaskStatus


class TaskRepository(Repository[Task]):
    """
    Repository interface for Task entities
    
    Extends the base repository with Task-specific operations.
    """
    
    @abstractmethod
    async def list_by_status(self, statuses: List[TaskStatus], limit: int = 100, offset: int = 0) -> List[Task]:
        """
        List tasks by status
        
        Args:
            statuses: List of statuses to filter by
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of tasks with the specified statuses
        """
        pass
    
    @abstractmethod
    async def list_by_assignee(self, assignee_id: str, limit: int = 100, offset: int = 0) -> List[Task]:
        """
        List tasks assigned to a specific minion
        
        Args:
            assignee_id: The ID of the assigned minion
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of tasks assigned to the minion
        """
        pass
    
    @abstractmethod
    async def list_subtasks(self, parent_task_id: str) -> List[Task]:
        """
        List subtasks of a parent task
        
        Args:
            parent_task_id: The ID of the parent task
            
        Returns:
            List of subtasks
        """
        pass
    
    @abstractmethod
    async def get_dependencies(self, task_id: str) -> List[Task]:
        """
        Get tasks that a specific task depends on
        
        Args:
            task_id: The ID of the task
            
        Returns:
            List of dependency tasks
        """
        pass