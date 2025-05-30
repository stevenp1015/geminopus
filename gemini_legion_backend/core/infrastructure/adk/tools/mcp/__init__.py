"""
MCP Tool Adapters for Gemini Legion
"""

from .mcp_adapter import (
    MCPCapability,
    MCPClient,
    LocalMCPClient,
    MCPToADKAdapter,
    ToolPermissionManager,
    MCPToolRegistry
)

from .filesystem_tools import (
    FileSystemReadTool,
    FileSystemWriteTool,
    FileSystemListTool,
    DiaryTool,
    create_filesystem_tools
)

from .computer_use_tools import (
    ComputerScreenshotTool,
    ComputerClickTool,
    ComputerTypeTool,
    ComputerKeyTool,
    ComputerScrollTool,
    ComputerWaitTool,
    create_computer_use_tools,
    COMPUTER_USE_CAPABILITIES
)

from .web_automation_tools import (
    WebNavigateTool,
    WebScreenshotTool,
    WebClickTool,
    WebFillTool,
    WebExtractTextTool,
    WebExecuteScriptTool,
    WebWaitForElementTool,
    WebSearchTool,
    create_web_automation_tools,
    WEB_AUTOMATION_CAPABILITIES
)

__all__ = [
    # Core adapter framework
    'MCPCapability',
    'MCPClient',
    'LocalMCPClient',
    'MCPToADKAdapter',
    'ToolPermissionManager',
    'MCPToolRegistry',
    # Filesystem tools
    'FileSystemReadTool',
    'FileSystemWriteTool',
    'FileSystemListTool',
    'DiaryTool',
    'create_filesystem_tools',
    # Computer use tools
    'ComputerScreenshotTool',
    'ComputerClickTool',
    'ComputerTypeTool',
    'ComputerKeyTool',
    'ComputerScrollTool',
    'ComputerWaitTool',
    'create_computer_use_tools',
    'COMPUTER_USE_CAPABILITIES',
    # Web automation tools
    'WebNavigateTool',
    'WebScreenshotTool',
    'WebClickTool',
    'WebFillTool',
    'WebExtractTextTool',
    'WebExecuteScriptTool',
    'WebWaitForElementTool',
    'WebSearchTool',
    'create_web_automation_tools',
    'WEB_AUTOMATION_CAPABILITIES'
]