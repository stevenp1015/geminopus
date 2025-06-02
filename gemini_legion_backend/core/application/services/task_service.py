"""
Task Service - Application Layer

This service handles task orchestration, assignment, and lifecycle management,
coordinating between Minions to accomplish complex multi-step tasks.
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import logging
import asyncio
from enum import Enum
from dataclasses import asdict
import json

from ....api.websocket.connection_manager import connection_manager
from ...domain import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskDecomposition,
    SubTask,
    TaskAssignment
)
from ...infrastructure.persistence.repositories import TaskRepository
from .minion_service import MinionService


logger = logging.getLogger(__name__)


class TaskOrchestrationStrategy(Enum):
    """Strategies for orchestrating task execution"""
    SEQUENTIAL = "sequential"  # Execute subtasks one after another
    PARALLEL = "parallel"      # Execute all subtasks at once
    DEPENDENCY = "dependency"  # Execute based on dependency graph
    ADAPTIVE = "adaptive"      # Dynamically adjust based on progress


class TaskService:
    """
    Application service for Task operations
    
    This service manages the lifecycle of tasks, including decomposition,
    assignment, execution monitoring, and result aggregation.
    """
    
    def __init__(
        self,
        task_repository: TaskRepository,
        minion_service: MinionService
    ):
        """
        Initialize the Task service
        
        Args:
            task_repository: Repository for persisting task state
            minion_service: Service for interacting with Minions
        """
        self.repository = task_repository
        self.minion_service = minion_service
        
        # Active task monitoring
        self.active_tasks: Dict[str, Task] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Task execution queues
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.result_queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self):
        """Start the service and background tasks"""
        logger.info("Starting Task Service...")
        
        # Start task monitoring
        self._monitor_task = asyncio.create_task(self._task_monitor_loop())
        
        # Load active tasks from repository
        await self._load_active_tasks()
        
        logger.info("Task Service started successfully")
    
    async def stop(self):
        """Stop the service and cleanup"""
        logger.info("Stopping Task Service...")
        
        # Cancel monitoring task
        if self._monitor_task:
            self._monitor_task.cancel()
        
        # Save all active tasks
        for task in self.active_tasks.values():
            await self.repository.save(task)
        
        logger.info("Task Service stopped")
    
    async def create_task(
        self,
        task_id: str,
        title: str,
        description: str,
        priority: str = "normal",
        assigned_to: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new task
        
        Args:
            task_id: Unique identifier for the task
            title: Task title
            description: Detailed task description
            priority: Task priority (low, normal, high, critical)
            assigned_to: Initial assignee (minion_id)
            dependencies: List of task IDs this depends on
            metadata: Additional task metadata
            
        Returns:
            Created task details
        """
        try:
            # Create domain task object
            task = Task(
                task_id=task_id,
                title=title,
                description=description,
                status=TaskStatus.PENDING,
                priority=TaskPriority(priority),
                created_at=datetime.now(),
                created_by="commander",  # TODO: Get from auth context
                assigned_to=assigned_to,
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            
            # Persist to repository
            await self.repository.save(task)
            
            # Add to active tasks
            self.active_tasks[task_id] = task
            
            # Auto-decompose if complex
            if self._is_complex_task(description):
                await self.decompose_task(task_id)
            
            # Auto-assign if not assigned
            if not assigned_to:
                await self.auto_assign_task(task_id)
            
            logger.info(f"Created task: {title} ({task_id})")
            
            task_dict = self._task_to_dict(task)
            asyncio.create_task(connection_manager.broadcast_service_event(
                "task_created",
                {"task": task_dict}
            ))

            return task_dict
            
        except Exception as e:
            logger.error(f"Failed to create task {task_id}: {e}")
            raise
    
    async def decompose_task(
        self,
        task_id: str,
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decompose a complex task into subtasks
        
        Args:
            task_id: ID of task to decompose
            strategy: Decomposition strategy to use
            
        Returns:
            Decomposition details with subtasks
        """
        task = self.active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Get TaskMaster minion for decomposition
        taskmaster = await self._get_taskmaster_minion()
        if not taskmaster:
            raise ValueError("No TaskMaster minion available for decomposition")
        
        # Request decomposition from TaskMaster
        decomposition_prompt = f"""
        Decompose this task into subtasks:
        Title: {task.title}
        Description: {task.description}
        Priority: {task.priority.value}
        
        Provide a structured decomposition with:
        1. Subtask list with clear titles and descriptions
        2. Dependency relationships between subtasks
        3. Estimated complexity for each subtask
        4. Suggested minion type for each subtask
        
        Return as JSON with structure:
        {{
            "subtasks": [
                {{
                    "title": "...",
                    "description": "...",
                    "complexity": "low|medium|high",
                    "suggested_minion_type": "scout|analyst|generalist",
                    "dependencies": []
                }}
            ],
            "execution_strategy": "sequential|parallel|dependency"
        }}
        """
        
        response = await self.minion_service.send_command(
            taskmaster["minion_id"],
            decomposition_prompt
        )
        
        # Parse decomposition response
        try:
            decomposition_data = json.loads(response["response"])
        except:
            # Fallback to simple decomposition
            decomposition_data = {
                "subtasks": [
                    {
                        "title": f"Subtask 1: {task.title}",
                        "description": task.description,
                        "complexity": "medium",
                        "suggested_minion_type": "generalist",
                        "dependencies": []
                    }
                ],
                "execution_strategy": "sequential"
            }
        
        # Create subtasks
        subtasks = []
        for i, subtask_data in enumerate(decomposition_data["subtasks"]):
            subtask = SubTask(
                subtask_id=f"{task_id}_sub_{i+1}",
                parent_task_id=task_id,
                title=subtask_data["title"],
                description=subtask_data["description"],
                status=TaskStatus.PENDING,
                complexity=subtask_data["complexity"],
                suggested_minion_type=subtask_data.get("suggested_minion_type"),
                dependencies=subtask_data.get("dependencies", [])
            )
            subtasks.append(subtask)
        
        # Create decomposition
        decomposition = TaskDecomposition(
            task_id=task_id,
            subtasks=subtasks,
            strategy=TaskOrchestrationStrategy(
                decomposition_data.get("execution_strategy", "sequential")
            ),
            created_at=datetime.now(),
            created_by=taskmaster["minion_id"]
        )
        
        # Update task with decomposition
        task.decomposition = decomposition
        task.status = TaskStatus.DECOMPOSED
        
        # Save updated task
        await self.repository.save(task)
        
        logger.info(f"Decomposed task {task_id} into {len(subtasks)} subtasks")
        
        return {
            "task_id": task_id,
            "subtask_count": len(subtasks),
            "strategy": decomposition.strategy.value,
            "subtasks": [
                {
                    "subtask_id": st.subtask_id,
                    "title": st.title,
                    "complexity": st.complexity,
                    "suggested_minion_type": st.suggested_minion_type
                }
                for st in subtasks
            ]
        }
    
    async def auto_assign_task(
        self,
        task_id: str,
        prefer_minion_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Automatically assign task to best available minion
        
        Args:
            task_id: ID of task to assign
            prefer_minion_type: Preferred type of minion
            
        Returns:
            Assignment details
        """
        task = self.active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Get available minions
        minions = await self.minion_service.list_minions(status_filter="active")
        
        if not minions:
            raise ValueError("No active minions available for assignment")
        
        # Score minions for task suitability
        scored_minions = []
        for minion in minions:
            score = await self._score_minion_for_task(minion, task, prefer_minion_type)
            scored_minions.append((score, minion))
        
        # Sort by score (highest first)
        scored_minions.sort(key=lambda x: x[0], reverse=True)
        
        # Assign to best minion
        best_minion = scored_minions[0][1]
        
        # Create assignment
        assignment = TaskAssignment(
            task_id=task_id,
            minion_id=best_minion["minion_id"],
            assigned_at=datetime.now(),
            assigned_by="auto_assign",
            reason=f"Best match with score {scored_minions[0][0]}"
        )
        
        # Update task
        task.assigned_to = best_minion["minion_id"]
        task.assignment_history.append(assignment)
        task.status = TaskStatus.ASSIGNED
        
        # Save task
        await self.repository.save(task)
        
        # Notify minion of assignment
        await self._notify_assignment(best_minion["minion_id"], task)
        
        logger.info(f"Auto-assigned task {task_id} to {best_minion['name']}")

        task_dict_for_event = self._task_to_dict(task) # Get latest task state
        asyncio.create_task(connection_manager.broadcast_service_event(
            "task_assigned",
            {"task_id": task.task_id, "minion_id": best_minion["minion_id"]}
        ))
        asyncio.create_task(connection_manager.broadcast_service_event(
            "task_updated", # Send the whole task as its assignment and status changed
            {"task": task_dict_for_event}
        ))
        
        return {
            "task_id": task_id,
            "assigned_to": best_minion["minion_id"],
            "minion_name": best_minion["name"],
            "assignment_score": scored_minions[0][0],
            "reason": assignment.reason
        }
    
    async def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Start execution of a task
        
        Args:
            task_id: ID of task to start
            
        Returns:
            Execution status
        """
        task = self.active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if not task.assigned_to:
            raise ValueError(f"Task {task_id} not assigned to any minion")
        
        # Check dependencies
        if not await self._check_dependencies_met(task):
            raise ValueError(f"Task {task_id} has unmet dependencies")
        
        # Update status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        # Save task
        await self.repository.save(task)
        
        # Send execution command to minion
        execution_command = f"""
        Execute this task:
        Title: {task.title}
        Description: {task.description}
        Priority: {task.priority.value}
        
        Report progress as you work.
        When complete, summarize your results.
        """
        
        response = await self.minion_service.send_command(
            task.assigned_to,
            execution_command,
            context={"task_id": task_id}
        )
        
        # Add to execution log
        task.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "task_started",
            "minion_id": task.assigned_to,
            "details": response
        })
        
        logger.info(f"Started task {task_id} with minion {task.assigned_to}")

        task_dict_for_event = self._task_to_dict(task)
        asyncio.create_task(connection_manager.broadcast_service_event(
            "task_status_changed",
            {"task_id": task.task_id, "status": task.status.value}
        ))
        asyncio.create_task(connection_manager.broadcast_service_event(
            "task_updated",
            {"task": task_dict_for_event}
        ))

        return { # Return value remains the same as original
            "task_id": task_id,
            "status": task.status.value,
            "assigned_to": task.assigned_to,
            "started_at": task.started_at.isoformat()
        }
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: int,
        status_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update task progress
        
        Args:
            task_id: ID of task to update
            progress: Progress percentage (0-100)
            status_message: Optional status message
            
        Returns:
            Updated task details
        """
        task = self.active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update progress
        task.progress = progress
        task.last_updated = datetime.now()
        
        # Add to execution log
        task.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "progress_update",
            "progress": progress,
            "message": status_message
        })
        
        # Check if complete
        if progress >= 100:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
        
        # Save task
        await self.repository.save(task)
        
        logger.info(f"Updated task {task_id} progress to {progress}%")

        task_dict_for_event = self._task_to_dict(task)
        asyncio.create_task(connection_manager.broadcast_service_event(
            "task_updated",
            {"task": task_dict_for_event}
        ))

        if task.status == TaskStatus.COMPLETED:
            asyncio.create_task(connection_manager.broadcast_service_event(
                "task_completed",
                {"task": task_dict_for_event}
            ))

        return task_dict_for_event # Return the dict we already created
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task details by ID"""
        task = self.active_tasks.get(task_id)
        if not task:
            task = await self.repository.get_by_id(task_id)
            if not task:
                return None
        
        return self._task_to_dict(task)
    
    async def list_tasks(
        self,
        status_filter: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering
        
        Args:
            status_filter: Filter by status
            assigned_to: Filter by assigned minion
            limit: Maximum number to return
            offset: Pagination offset
            
        Returns:
            List of task details
        """
        # Get from repository
        tasks = await self.repository.list_all(limit, offset)
        
        # Apply filters
        if status_filter:
            tasks = [t for t in tasks if t.status.value == status_filter]
        
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        
        return [self._task_to_dict(t) for t in tasks]
    
    async def get_task_tree(self, task_id: str) -> Dict[str, Any]:
        """
        Get task with full subtask tree
        
        Args:
            task_id: ID of parent task
            
        Returns:
            Task tree structure
        """
        task = await self.get_task(task_id)
        if not task:
            return None
        
        # Get decomposition
        if task.get("decomposition"):
            subtasks = []
            for subtask in task["decomposition"]["subtasks"]:
                # Recursively get subtask trees
                subtask_tree = await self.get_task_tree(subtask["subtask_id"])
                if subtask_tree:
                    subtasks.append(subtask_tree)
            
            task["subtasks"] = subtasks
        
        return task
    
    async def _task_monitor_loop(self):
        """Background task to monitor task execution"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                for task_id, task in list(self.active_tasks.items()):
                    try:
                        # Check task health
                        if task.status == TaskStatus.IN_PROGRESS:
                            # Check if minion is still working
                            if task.assigned_to:
                                minion = await self.minion_service.get_minion(task.assigned_to)
                                if not minion or minion["status"] != "active":
                                    # Minion went offline, reassign
                                    logger.warning(f"Minion {task.assigned_to} offline, reassigning task {task_id}")
                                    await self.auto_assign_task(task_id)
                            
                            # Check for timeout
                            if task.started_at:
                                elapsed = (datetime.now() - task.started_at).total_seconds()
                                if elapsed > 3600:  # 1 hour timeout
                                    logger.warning(f"Task {task_id} timed out")
                                    task.status = TaskStatus.FAILED
                                    task.error = "Task execution timed out"
                                    await self.repository.save(task)
                        
                        # Remove completed tasks from active after 5 minutes
                        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                            if task.completed_at:
                                elapsed = (datetime.now() - task.completed_at).total_seconds()
                                if elapsed > 300:  # 5 minutes
                                    del self.active_tasks[task_id]
                    
                    except Exception as e:
                        logger.error(f"Error monitoring task {task_id}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task monitor loop: {e}")
    
    async def _load_active_tasks(self):
        """Load active tasks from repository"""
        try:
            # Get all non-completed tasks
            tasks = await self.repository.list_by_status([
                TaskStatus.PENDING,
                TaskStatus.ASSIGNED,
                TaskStatus.IN_PROGRESS,
                TaskStatus.DECOMPOSED
            ])
            
            for task in tasks:
                self.active_tasks[task.task_id] = task
            
            logger.info(f"Loaded {len(tasks)} active tasks")
            
        except Exception as e:
            logger.error(f"Failed to load active tasks: {e}")
    
    async def _get_taskmaster_minion(self) -> Optional[Dict[str, Any]]:
        """Get an available TaskMaster minion"""
        minions = await self.minion_service.list_minions(status_filter="active")
        
        for minion in minions:
            # Check if it's a TaskMaster type
            if "taskmaster" in minion.get("personality", "").lower():
                return minion
            if "task" in minion.get("expertise_areas", []):
                return minion
        
        return None
    
    async def _score_minion_for_task(
        self,
        minion: Dict[str, Any],
        task: Task,
        prefer_type: Optional[str] = None
    ) -> float:
        """Score a minion's suitability for a task"""
        score = 0.0
        
        # Check minion availability (lower stress = higher score)
        emotional_state = minion.get("emotional_state", {})
        stress = emotional_state.get("stress_level", 0.5)
        score += (1.0 - stress) * 20
        
        # Check expertise match
        task_keywords = set(task.title.lower().split() + task.description.lower().split())
        expertise_areas = set(area.lower() for area in minion.get("expertise_areas", []))
        
        matching_expertise = task_keywords.intersection(expertise_areas)
        score += len(matching_expertise) * 10
        
        # Check preference match
        if prefer_type:
            if prefer_type in minion.get("personality", "").lower():
                score += 30
        
        # Check current workload
        current_tasks = await self.list_tasks(assigned_to=minion["minion_id"], status_filter="in_progress")
        score -= len(current_tasks) * 5
        
        # Personality traits bonus
        if task.priority == TaskPriority.CRITICAL:
            # Prefer focused, reliable minions for critical tasks
            if "reliable" in minion.get("personality", "").lower():
                score += 15
            if "focused" in minion.get("personality", "").lower():
                score += 15
        
        return max(0, score)
    
    async def _notify_assignment(self, minion_id: str, task: Task):
        """Notify a minion of task assignment"""
        notification = f"""
        You have been assigned a new task!
        
        Task: {task.title}
        Priority: {task.priority.value}
        Description: {task.description}
        
        Please acknowledge receipt and begin planning your approach.
        """
        
        await self.minion_service.send_command(
            minion_id,
            notification,
            context={"task_assignment": task.task_id}
        )
    
    async def _check_dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are met"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = await self.repository.get_by_id(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _is_complex_task(self, description: str) -> bool:
        """Heuristic to determine if a task is complex enough to decompose"""
        # Simple heuristic based on description length and keywords
        complexity_keywords = ["multiple", "steps", "complex", "analyze", "research", "implement", "design"]
        
        if len(description) > 200:
            return True
        
        description_lower = description.lower()
        if any(keyword in description_lower for keyword in complexity_keywords):
            return True
        
        return False
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert domain Task to API-friendly dictionary"""
        result = {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "created_by": task.created_by,
            "assigned_to": task.assigned_to,
            "dependencies": task.dependencies,
            "metadata": task.metadata
        }
        
        if task.started_at:
            result["started_at"] = task.started_at.isoformat()
        
        if task.completed_at:
            result["completed_at"] = task.completed_at.isoformat()
        
        if task.decomposition:
            result["decomposition"] = {
                "strategy": task.decomposition.strategy.value,
                "subtask_count": len(task.decomposition.subtasks),
                "subtasks": [
                    {
                        "subtask_id": st.subtask_id,
                        "title": st.title,
                        "status": st.status.value,
                        "complexity": st.complexity
                    }
                    for st in task.decomposition.subtasks
                ]
            }
        
        return result
