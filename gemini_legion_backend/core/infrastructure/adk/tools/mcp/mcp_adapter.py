"""
MCP to ADK Tool Adapter Framework

This module provides the core framework for adapting Model Context Protocol (MCP)
tools to work as ADK tools within the Gemini Legion system.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Type, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

from google.adk.tools import BaseTool


logger = logging.getLogger(__name__)


@dataclass
class MCPCapability:
    """Represents an MCP tool capability"""
    name: str
    description: str
    endpoint: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    
    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters against schema"""
        # Simplified validation - in production would use jsonschema
        required = self.input_schema.get("required", [])
        properties = self.input_schema.get("properties", {})
        
        # Check required fields
        for field in required:
            if field not in params:
                return False
        
        # Check types (simplified)
        for field, value in params.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type:
                    # Basic type checking
                    if expected_type == "string" and not isinstance(value, str):
                        return False
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        return False
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        return False
                    elif expected_type == "array" and not isinstance(value, list):
                        return False
        
        return True


class MCPClient(ABC):
    """Abstract base for MCP client implementations"""
    
    @abstractmethod
    async def execute(self, capability_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP capability"""
        pass
    
    @abstractmethod
    async def discover_capabilities(self) -> List[MCPCapability]:
        """Discover available capabilities from MCP server"""
        pass


class LocalMCPClient(MCPClient):
    """
    Local MCP client that executes tools directly
    
    This is a simplified implementation for local tools.
    In production, this would communicate with actual MCP servers.
    """
    
    def __init__(self, tool_implementations: Dict[str, Callable]):
        """
        Initialize with local tool implementations
        
        Args:
            tool_implementations: Map of capability names to implementation functions
        """
        self.tool_implementations = tool_implementations
    
    async def execute(self, capability_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a capability locally"""
        if capability_name not in self.tool_implementations:
            raise ValueError(f"Unknown capability: {capability_name}")
        
        implementation = self.tool_implementations[capability_name]
        
        # Execute the tool
        try:
            if asyncio.iscoroutinefunction(implementation):
                result = await implementation(**params)
            else:
                result = implementation(**params)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing {capability_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def discover_capabilities(self) -> List[MCPCapability]:
        """Return pre-defined capabilities for local tools"""
        # This would be replaced with actual discovery in production
        return []


class MCPToADKAdapter:
    """Adapts MCP tools to ADK tool interface"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self._adapted_tools: Dict[str, Type[BaseTool]] = {}
    
    async def adapt_tool(self, capability: MCPCapability) -> Type[BaseTool]:
        """
        Convert MCP capability to ADK tool class
        
        Args:
            capability: MCP capability to adapt
            
        Returns:
            ADK Tool class that wraps the MCP capability
        """
        # Check if already adapted
        if capability.name in self._adapted_tools:
            return self._adapted_tools[capability.name]
        
        # Create dynamic tool class
        class AdaptedMCPTool(BaseTool):
            name = capability.name
            description = capability.description
            
            def __init__(self):
                super().__init__()
                self.capability = capability
                self.mcp_client = mcp_client
            
            async def execute(self, **kwargs) -> Dict[str, Any]:
                """Execute the MCP tool through ADK interface"""
                # Validate inputs
                if not self.capability.validate_input(kwargs):
                    return {
                        "success": False,
                        "error": "Invalid input parameters"
                    }
                
                # Execute via MCP client
                result = await self.mcp_client.execute(
                    self.capability.name, kwargs
                )
                
                # Transform result to ADK format if needed
                return self._transform_result(result)
            
            def _transform_result(self, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
                """Transform MCP result to ADK expected format"""
                # For now, pass through
                # In production, might need schema transformation
                return mcp_result
            
            def get_schema(self) -> Dict[str, Any]:
                """Get tool schema in ADK format"""
                return {
                    "name": self.capability.name,
                    "description": self.capability.description,
                    "parameters": self.capability.input_schema
                }
        
        # Store the adapted class
        self._adapted_tools[capability.name] = AdaptedMCPTool
        
        return AdaptedMCPTool
    
    async def discover_and_adapt_all(self) -> List[Type[BaseTool]]:
        """
        Discover all MCP capabilities and adapt them to ADK tools
        
        Returns:
            List of ADK Tool classes
        """
        capabilities = await self.mcp_client.discover_capabilities()
        
        tools = []
        for cap in capabilities:
            try:
                tool_class = await self.adapt_tool(cap)
                tools.append(tool_class)
                logger.info(f"Adapted MCP tool: {cap.name}")
            except Exception as e:
                logger.error(f"Failed to adapt {cap.name}: {e}")
        
        return tools


class ToolPermissionManager:
    """Manages permissions for tool access by Minions"""
    
    def __init__(self):
        self.permissions: Dict[str, List[str]] = {}  # minion_id -> allowed tools
        self.tool_restrictions: Dict[str, Dict[str, Any]] = {}  # tool -> restrictions
    
    def grant_permission(self, minion_id: str, tool_name: str):
        """Grant a Minion permission to use a tool"""
        if minion_id not in self.permissions:
            self.permissions[minion_id] = []
        
        if tool_name not in self.permissions[minion_id]:
            self.permissions[minion_id].append(tool_name)
            logger.info(f"Granted {minion_id} permission to use {tool_name}")
    
    def revoke_permission(self, minion_id: str, tool_name: str):
        """Revoke a Minion's permission to use a tool"""
        if minion_id in self.permissions and tool_name in self.permissions[minion_id]:
            self.permissions[minion_id].remove(tool_name)
            logger.info(f"Revoked {minion_id} permission to use {tool_name}")
    
    def check_permission(self, minion_id: str, tool_name: str) -> bool:
        """Check if a Minion has permission to use a tool"""
        return minion_id in self.permissions and tool_name in self.permissions[minion_id]
    
    def set_tool_restriction(self, tool_name: str, restrictions: Dict[str, Any]):
        """Set usage restrictions for a tool"""
        self.tool_restrictions[tool_name] = restrictions
    
    def wrap_tool(self, tool: BaseTool, minion_id: str) -> BaseTool:
        """
        Wrap a tool with permission checking
        
        Args:
            tool: Original tool
            minion_id: ID of the Minion using the tool
            
        Returns:
            Wrapped tool with permission checking
        """
        original_execute = tool.execute
        
        async def wrapped_execute(**kwargs):
            # Check permission
            if not self.check_permission(minion_id, tool.name):
                return {
                    "success": False,
                    "error": f"Permission denied: {minion_id} cannot use {tool.name}"
                }
            
            # Check restrictions
            restrictions = self.tool_restrictions.get(tool.name, {})
            
            # Example: rate limiting
            if "rate_limit" in restrictions:
                # Would implement rate limiting here
                pass
            
            # Execute original tool
            return await original_execute(**kwargs)
        
        # Replace execute method
        tool.execute = wrapped_execute
        
        return tool


class MCPToolRegistry:
    """Registry for all available MCP tools"""
    
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        self.capabilities: Dict[str, MCPCapability] = {}
        self.adapters: List[MCPToADKAdapter] = []
    
    async def register_mcp_server(self, server_name: str, mcp_client: MCPClient):
        """
        Register an MCP server and discover its tools
        
        Args:
            server_name: Name to identify this server
            mcp_client: Client to communicate with the server
        """
        logger.info(f"Registering MCP server: {server_name}")
        
        # Create adapter
        adapter = MCPToADKAdapter(mcp_client)
        self.adapters.append(adapter)
        
        # Discover and adapt tools
        tools = await adapter.discover_and_adapt_all()
        
        # Register each tool
        for tool_class in tools:
            self.register_tool(tool_class)
    
    def register_tool(self, tool_class: Type[BaseTool]):
        """Register a single tool"""
        tool_name = tool_class.name
        
        if tool_name in self.tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")
        
        self.tools[tool_name] = tool_class
        logger.debug(f"Registered tool: {tool_name}")
    
    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        """Get a tool class by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names"""
        return list(self.tools.keys())
    
    def create_tool_instance(self, name: str) -> Optional[BaseTool]:
        """Create an instance of a tool"""
        tool_class = self.get_tool(name)
        if tool_class:
            return tool_class()
        return None
