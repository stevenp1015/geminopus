"""
API Endpoints

Collection of all API endpoint routers.
"""

from .minions import router as minions_router
from .channels import router as channels_router
from .health import router as health_router

__all__ = ['minions_router', 'channels_router', 'health_router']