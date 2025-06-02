"""
Health check endpoint

Provides system health and status information.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import psutil
import os

from ..schemas import HealthCheckResponse
from ....core.dependencies import get_minion_service, get_channel_service
from ....core.application.services import MinionService, ChannelService

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    minion_service: MinionService = Depends(get_minion_service),
    channel_service: ChannelService = Depends(get_channel_service)
) -> HealthCheckResponse:
    """System health check"""
    minions = await minion_service.list_minions()
    channels = await channel_service.list_channels()
    
    return HealthCheckResponse(
        status="operational",
        timestamp=datetime.now().isoformat(),
        minion_count=len(minions),
        active_channels=len(channels)
    )


@router.get("/health/detailed")
async def detailed_health_check(
    minion_service: MinionService = Depends(get_minion_service),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """Detailed system health information"""
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get minion and channel data
    minions = await minion_service.list_minions()
    channels = await channel_service.list_channels()
    
    # Get minion stats
    minion_stats = []
    for minion in minions:
        # For now, just include basic info since we don't have direct access to memory stats
        minion_stats.append({
            "id": minion["minion_id"],
            "name": minion["name"],
            "status": minion.get("status", "active"),
            "personality": minion.get("personality", "unknown")
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
            "minion_count": len(minions),
            "active_channels": len(channels),
            "minion_stats": minion_stats
        }
    }