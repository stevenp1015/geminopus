"""
Computer Use MCP BaseTool Adapters

This module provides ADK-compatible computer use tools that wrap
Desktop Commander MCP capabilities, allowing Minions to interact
with the desktop environment.
"""

import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from google.adk.tools import BaseTool

from .mcp_adapter import MCPCapability


logger = logging.getLogger(__name__)


class ComputerScreenshotTool(BaseTool):
    """
    BaseTool for taking screenshots of the desktop
    
    This tool allows Minions to capture the current state of the screen
    for analysis and decision making.
    """
    
    name = "computer_screenshot"
    description = "Take a screenshot of the desktop"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
        
    async def execute(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot
        
        Args:
            save_path: Optional path to save the screenshot
            
        Returns:
            Dictionary with screenshot data or error
        """
        try:
            # In production, this would call the Desktop Commander MCP
            # For now, we'll simulate the response
            logger.info("Taking screenshot via Desktop Commander")
            
            # Simulated MCP call
            result = {
                "success": True,
                "screenshot": {
                    "width": 1920,
                    "height": 1080,
                    "format": "png",
                    "data": "base64_encoded_image_data",  # Would be actual image
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            if save_path:
                result["saved_to"] = save_path
            
            return result
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ComputerClickTool(BaseTool):
    """
    BaseTool for clicking on screen elements
    
    This tool allows Minions to interact with desktop applications
    by clicking on specific coordinates or elements.
    """
    
    name = "computer_click"
    description = "Click on a screen element"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def execute(
        self,
        x: int,
        y: int,
        button: str = "left",
        double_click: bool = False
    ) -> Dict[str, Any]:
        """
        Click at specified coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button (left, right, middle)
            double_click: Whether to double-click
            
        Returns:
            Result of the click operation
        """
        try:
            # Validate coordinates
            if x < 0 or y < 0:
                return {
                    "success": False,
                    "error": "Invalid coordinates: must be positive"
                }
            
            # In production, this would call Desktop Commander
            logger.info(f"Clicking at ({x}, {y}) with {button} button")
            
            return {
                "success": True,
                "action": "double_click" if double_click else "click",
                "coordinates": {"x": x, "y": y},
                "button": button,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error clicking: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ComputerTypeTool(BaseTool):
    """
    BaseTool for typing text
    
    This tool allows Minions to type text into applications,
    simulating keyboard input.
    """
    
    name = "computer_type"
    description = "Type text using the keyboard"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def execute(self, text: str, delay_ms: int = 0) -> Dict[str, Any]:
        """
        Type text
        
        Args:
            text: Text to type
            delay_ms: Delay between keystrokes in milliseconds
            
        Returns:
            Result of the typing operation
        """
        try:
            if not text:
                return {
                    "success": False,
                    "error": "No text provided"
                }
            
            # In production, this would call Desktop Commander
            logger.info(f"Typing text: {text[:20]}...")
            
            return {
                "success": True,
                "text_length": len(text),
                "delay_ms": delay_ms,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error typing: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ComputerKeyTool(BaseTool):
    """
    BaseTool for pressing keyboard keys
    
    This tool allows Minions to send keyboard shortcuts and
    special key combinations.
    """
    
    name = "computer_key"
    description = "Press keyboard keys or shortcuts"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
        
        # Common key mappings
        self.special_keys = {
            "enter": "Return",
            "tab": "Tab",
            "esc": "Escape",
            "space": "space",
            "backspace": "BackSpace",
            "delete": "Delete",
            "up": "Up",
            "down": "Down",
            "left": "Left",
            "right": "Right",
            "home": "Home",
            "end": "End",
            "pageup": "Page_Up",
            "pagedown": "Page_Down"
        }
    
    async def execute(
        self,
        key: str,
        modifiers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Press a key or key combination
        
        Args:
            key: Key to press
            modifiers: List of modifier keys (ctrl, alt, shift, cmd/super)
            
        Returns:
            Result of the key press
        """
        try:
            # Normalize key name
            key_lower = key.lower()
            if key_lower in self.special_keys:
                key = self.special_keys[key_lower]
            
            # Build key combination
            if modifiers:
                combo = "+".join(modifiers + [key])
            else:
                combo = key
            
            # In production, this would call Desktop Commander
            logger.info(f"Pressing key: {combo}")
            
            return {
                "success": True,
                "key": key,
                "modifiers": modifiers or [],
                "combination": combo,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ComputerScrollTool(BaseTool):
    """
    BaseTool for scrolling
    
    This tool allows Minions to scroll in applications,
    useful for navigating long documents or web pages.
    """
    
    name = "computer_scroll"
    description = "Scroll in the active window"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def execute(
        self,
        direction: str,
        amount: int = 3,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scroll in a direction
        
        Args:
            direction: Scroll direction (up, down, left, right)
            amount: Number of scroll units
            x: Optional X coordinate to scroll at
            y: Optional Y coordinate to scroll at
            
        Returns:
            Result of the scroll operation
        """
        try:
            valid_directions = ["up", "down", "left", "right"]
            if direction not in valid_directions:
                return {
                    "success": False,
                    "error": f"Invalid direction. Must be one of: {valid_directions}"
                }
            
            # In production, this would call Desktop Commander
            logger.info(f"Scrolling {direction} by {amount} units")
            
            result = {
                "success": True,
                "direction": direction,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
            
            if x is not None and y is not None:
                result["position"] = {"x": x, "y": y}
            
            return result
            
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ComputerWaitTool(BaseTool):
    """
    BaseTool for waiting
    
    This tool allows Minions to wait for applications to load
    or for specific conditions to be met.
    """
    
    name = "computer_wait"
    description = "Wait for a specified duration"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def execute(self, seconds: float) -> Dict[str, Any]:
        """
        Wait for a duration
        
        Args:
            seconds: Number of seconds to wait
            
        Returns:
            Result after waiting
        """
        try:
            if seconds < 0:
                return {
                    "success": False,
                    "error": "Wait duration must be positive"
                }
            
            if seconds > 30:
                return {
                    "success": False,
                    "error": "Wait duration too long (max 30 seconds)"
                }
            
            # In production, this would actually wait
            logger.info(f"Waiting for {seconds} seconds")
            
            return {
                "success": True,
                "duration": seconds,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error waiting: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def create_computer_use_tools() -> List[BaseTool]:
    """
    Create all computer use tools
    
    Returns:
        List of computer use tools
    """
    return [
        ComputerScreenshotTool(),
        ComputerClickTool(),
        ComputerTypeTool(),
        ComputerKeyTool(),
        ComputerScrollTool(),
        ComputerWaitTool()
    ]


# BaseTool capability definitions for MCP registration
COMPUTER_USE_CAPABILITIES = [
    MCPCapability(
        name="computer_screenshot",
        description="Take a screenshot of the desktop",
        endpoint="desktop-commander/screenshot",
        input_schema={
            "type": "object",
            "properties": {
                "save_path": {"type": "string", "description": "Optional path to save screenshot"}
            }
        }
    ),
    MCPCapability(
        name="computer_click",
        description="Click on screen coordinates",
        endpoint="desktop-commander/click",
        input_schema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate"},
                "y": {"type": "integer", "description": "Y coordinate"},
                "button": {"type": "string", "enum": ["left", "right", "middle"]},
                "double_click": {"type": "boolean", "default": False}
            },
            "required": ["x", "y"]
        }
    ),
    MCPCapability(
        name="computer_type",
        description="Type text using keyboard",
        endpoint="desktop-commander/type",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type"},
                "delay_ms": {"type": "integer", "description": "Delay between keystrokes", "default": 0}
            },
            "required": ["text"]
        }
    ),
    MCPCapability(
        name="computer_key",
        description="Press keyboard keys or shortcuts",
        endpoint="desktop-commander/key",
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to press"},
                "modifiers": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["ctrl", "alt", "shift", "cmd", "super"]},
                    "description": "Modifier keys"
                }
            },
            "required": ["key"]
        }
    ),
    MCPCapability(
        name="computer_scroll",
        description="Scroll in active window",
        endpoint="desktop-commander/scroll",
        input_schema={
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                "amount": {"type": "integer", "default": 3},
                "x": {"type": "integer", "description": "Optional X coordinate"},
                "y": {"type": "integer", "description": "Optional Y coordinate"}
            },
            "required": ["direction"]
        }
    ),
    MCPCapability(
        name="computer_wait",
        description="Wait for specified duration",
        endpoint="desktop-commander/wait",
        input_schema={
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Seconds to wait", "minimum": 0, "maximum": 30}
            },
            "required": ["seconds"]
        }
    )
]