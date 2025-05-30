"""
Health check endpoint

Provides system health and status information.
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

from ..schemas import HealthCheckResponse
from .minions import get_minion_factory
from .channels import channels_store

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """System health check"""
    factory = get_minion_factory()
    
    return HealthCheckResponse(
        status="operational",
        timestamp=datetime.now().isoformat(),
        minion_count=len(factory.list_minions()),
        active_channels=len(channels_store)
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed system health information"""
    factory = get_minion_factory()
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get minion stats
    minion_ids = factory.list_minions()
    minion_stats = []
    
    for minion_id in minion_ids:
        minion = factory.get_minion(minion_id)
        if minion:
            memory_stats = minion.memory_system.get_memory_stats()
            minion_stats.append({
                "id": minion_id,
                "name": minion.persona.name,
                "memory": memory_stats
            })
    
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent
            },
            "process": {
                "pid": os.getpid(),
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
            }
        },
        "legion": {
            "minion_count": len(minion_ids),
            "active_channels": len(channels_store),
            "minion_stats": minion_stats
        }
    }