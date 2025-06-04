"""
Task-related API endpoints

Handles task creation, assignment, and tracking.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..schemas import (
    CreateTaskRequest,
    TaskResponse,
    TasksListResponse,
    OperationResponse,
    TaskStatusEnum,
    TaskPriorityEnum
)
from ....core.dependencies import get_task_service
from ....core.application.services import TaskService
from ....core.domain import TaskStatus, TaskPriority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def convert_task_to_response(task_data: dict) -> TaskResponse:
    """Convert task data to API response format"""
    # Map internal status to API enum
    status_map = {
        TaskStatus.PENDING: TaskStatusEnum.PENDING,
        TaskStatus.ASSIGNED: TaskStatusEnum.ASSIGNED,
        TaskStatus.DECOMPOSED: TaskStatusEnum.DECOMPOSED,
        TaskStatus.IN_PROGRESS: TaskStatusEnum.IN_PROGRESS,
        TaskStatus.COMPLETED: TaskStatusEnum.COMPLETED,
        TaskStatus.FAILED: TaskStatusEnum.FAILED,
        TaskStatus.CANCELLED: TaskStatusEnum.CANCELLED
    }
    
    # Map internal priority to API enum
    priority_map = {
        TaskPriority.LOW: TaskPriorityEnum.LOW,
        TaskPriority.MEDIUM: TaskPriorityEnum.NORMAL,
        TaskPriority.HIGH: TaskPriorityEnum.HIGH,
        TaskPriority.CRITICAL: TaskPriorityEnum.CRITICAL
    }
    
    status = task_data.get("status", TaskStatus.PENDING)
    priority = task_data.get("priority", TaskPriority.MEDIUM)
    
    return TaskResponse(
        task_id=task_data["task_id"], # Changed from id to task_id
        title=task_data["title"],
        description=task_data["description"],
        status=status_map.get(status, TaskStatusEnum.PENDING),
        priority=priority_map.get(priority, TaskPriorityEnum.NORMAL),
        assigned_to=task_data.get("assigned_to"),
        created_by=task_data.get("created_by", "commander"),
        parent_task_id=task_data.get("parent_task_id"),
        subtask_ids=task_data.get("subtask_ids", []),
        dependencies=task_data.get("dependencies", []),
        tags=task_data.get("tags", []),
        created_at=task_data.get("created_at", datetime.now()).isoformat(),
        updated_at=task_data.get("updated_at", datetime.now()).isoformat(),
        completed_at=task_data.get("completed_at", None),
        result=task_data.get("result"),
        metadata=task_data.get("metadata", {})
    )


@router.get("/", response_model=TasksListResponse)
async def list_tasks(
    status: Optional[TaskStatusEnum] = None,
    assigned_to: Optional[str] = None,
    created_by: Optional[str] = None,
    task_service: TaskService = Depends(get_task_service)
) -> TasksListResponse:
    """List all tasks with optional filtering"""
    try:
        # Convert API enum to domain enum if provided
        domain_status = None
        if status:
            status_map = {
                TaskStatusEnum.PENDING: TaskStatus.PENDING,
                TaskStatusEnum.ASSIGNED: TaskStatus.ASSIGNED,
                TaskStatusEnum.IN_PROGRESS: TaskStatus.IN_PROGRESS,
                TaskStatusEnum.COMPLETED: TaskStatus.COMPLETED,
                TaskStatusEnum.FAILED: TaskStatus.FAILED,
                TaskStatusEnum.CANCELLED: TaskStatus.CANCELLED
            }
            domain_status = status_map.get(status)
        
        tasks_data = await task_service.list_tasks(
            status=domain_status,
            assigned_to=assigned_to,
            created_by=created_by
        )
        
        tasks = [convert_task_to_response(task) for task in tasks_data]
        
        return TasksListResponse(
            tasks=tasks,
            total=len(tasks),
            pending_count=sum(1 for t in tasks if t.status == TaskStatusEnum.PENDING),
            in_progress_count=sum(1 for t in tasks if t.status == TaskStatusEnum.IN_PROGRESS),
            completed_count=sum(1 for t in tasks if t.status == TaskStatusEnum.COMPLETED)
        )
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Error listing tasks")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Get a specific task"""
    try:
        task_data = await task_service.get_task(task_id)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return convert_task_to_response(task_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving task")


@router.post("/create", response_model=OperationResponse)
async def create_task(
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Create a new task"""
    try:
        # Convert API priority to domain priority
        priority_map = {
            TaskPriorityEnum.LOW: TaskPriority.LOW,
            TaskPriorityEnum.NORMAL: TaskPriority.MEDIUM,
            TaskPriorityEnum.HIGH: TaskPriority.HIGH,
            TaskPriorityEnum.CRITICAL: TaskPriority.CRITICAL
        }
        
        task_id = await task_service.create_task(
            title=request.title,
            description=request.description,
            priority=priority_map.get(request.priority, TaskPriority.MEDIUM),
            created_by=request.created_by or "commander",
            tags=request.tags,
            metadata=request.metadata
        )
        
        logger.info(f"Created task: {task_id} - {request.title}")
        
        return OperationResponse(
            status="created",
            id=task_id,
            message=f"Task '{request.title}' created successfully!",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/assign", response_model=OperationResponse)
async def assign_task(
    task_id: str,
    minion_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Assign a task to a minion"""
    try:
        success = await task_service.assign_task(task_id, minion_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Task not found or assignment failed"
            )
        
        return OperationResponse(
            status="assigned",
            id=task_id,
            message=f"Task assigned to {minion_id}. Get to work, minion!",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error assigning task")


@router.post("/{task_id}/update-status", response_model=OperationResponse)
async def update_task_status(
    task_id: str,
    status: TaskStatusEnum,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Update task status"""
    try:
        # Convert API enum to domain enum
        status_map = {
            TaskStatusEnum.PENDING: TaskStatus.PENDING,
            TaskStatusEnum.ASSIGNED: TaskStatus.ASSIGNED,
            TaskStatusEnum.IN_PROGRESS: TaskStatus.IN_PROGRESS,
            TaskStatusEnum.COMPLETED: TaskStatus.COMPLETED,
            TaskStatusEnum.FAILED: TaskStatus.FAILED,
            TaskStatusEnum.CANCELLED: TaskStatus.CANCELLED
        }
        
        success = await task_service.update_task_status(
            task_id,
            status_map.get(status, TaskStatus.PENDING)
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return OperationResponse(
            status="updated",
            id=task_id,
            message=f"Task status updated to {status.value}",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        raise HTTPException(status_code=500, detail="Error updating task status")


@router.post("/{task_id}/complete", response_model=OperationResponse)
async def complete_task(
    task_id: str,
    result: Optional[Dict[str, Any]] = None,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Mark a task as completed"""
    try:
        success = await task_service.complete_task(task_id, result)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return OperationResponse(
            status="completed",
            id=task_id,
            message="Task completed successfully! Great work!   . .   .",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error completing task")


@router.post("/{task_id}/cancel", response_model=OperationResponse)
async def cancel_task(
    task_id: str,
    reason: Optional[str] = None,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Cancel a task"""
    try:
        success = await task_service.cancel_task(task_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return OperationResponse(
            status="cancelled",
            id=task_id,
            message=f"Task cancelled. Reason: {reason or 'No reason provided'}",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error cancelling task")


@router.post("/{task_id}/decompose", response_model=OperationResponse)
async def decompose_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Decompose a task into subtasks"""
    try:
        subtask_ids = await task_service.decompose_task(task_id)
        
        if not subtask_ids:
            raise HTTPException(
                status_code=404,
                detail="Task not found or decomposition failed"
            )
        
        return OperationResponse(
            status="decomposed",
            id=task_id,
            message=f"Task decomposed into {len(subtask_ids)} subtasks",
            timestamp=datetime.now().isoformat(),
            data={"subtask_ids": subtask_ids}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error decomposing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error decomposing task")


@router.delete("/{task_id}", response_model=OperationResponse)
async def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> OperationResponse:
    """Delete a task"""
    try:
        success = await task_service.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return OperationResponse(
            status="deleted",
            id=task_id,
            message="Task deleted successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting task")