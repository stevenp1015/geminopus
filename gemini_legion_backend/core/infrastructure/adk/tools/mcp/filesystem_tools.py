"""
Filesystem MCP BaseTool Adapters

This module provides ADK-compatible filesystem tools that wrap
MCP filesystem capabilities, allowing Minions to interact with files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from google.adk.tools import BaseTool

from .mcp_adapter import MCPCapability, LocalMCPClient


logger = logging.getLogger(__name__)


class FileSystemReadTool(BaseTool):
    """
    BaseTool for reading files from the filesystem
    
    This tool allows Minions to read their diary files and other
    authorized files within the allowed directories.
    """
    
    name = "read_file"
    description = "Read the contents of a file"
    
    def __init__(self, allowed_paths: List[str]):
        """
        Initialize with allowed directory paths
        
        Args:
            allowed_paths: List of directory paths the tool can access
        """
        super().__init__(name=self.name, description=self.description)
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories"""
        resolved_path = path.resolve()
        
        for allowed in self.allowed_paths:
            try:
                resolved_path.relative_to(allowed)
                return True
            except ValueError:
                continue
        
        return False
    
    async def execute(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read a file's contents
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with success status and file contents or error
        """
        try:
            path = Path(file_path).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return {
                    "success": False,
                    "error": f"Access denied: {file_path} is outside allowed directories"
                }
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Not a file: {file_path}"
                }
            
            # Read the file
            content = path.read_text(encoding=encoding)
            
            return {
                "success": True,
                "content": content,
                "file_path": str(path),
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class FileSystemWriteTool(BaseTool):
    """
    BaseTool for writing files to the filesystem
    
    This tool allows Minions to write their diary entries and other
    authorized files within the allowed directories.
    """
    
    name = "write_file"
    description = "Write content to a file"
    
    def __init__(self, allowed_paths: List[str]):
        """
        Initialize with allowed directory paths
        
        Args:
            allowed_paths: List of directory paths the tool can access
        """
        super().__init__(name=self.name, description=self.description)
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories"""
        resolved_path = path.resolve()
        
        for allowed in self.allowed_paths:
            try:
                resolved_path.relative_to(allowed)
                return True
            except ValueError:
                continue
        
        return False
    
    async def execute(
        self,
        file_path: str,
        content: str,
        mode: str = "write",
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            mode: Write mode - "write" (overwrite) or "append"
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with success status and file info or error
        """
        try:
            path = Path(file_path).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return {
                    "success": False,
                    "error": f"Access denied: {file_path} is outside allowed directories"
                }
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            if mode == "append":
                with open(path, "a", encoding=encoding) as f:
                    f.write(content)
            else:
                path.write_text(content, encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(path),
                "size": path.stat().st_size,
                "mode": mode
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class FileSystemListTool(BaseTool):
    """
    BaseTool for listing directory contents
    
    This tool allows Minions to explore directory structures
    within allowed paths.
    """
    
    name = "list_directory"
    description = "List files and directories in a path"
    
    def __init__(self, allowed_paths: List[str]):
        """
        Initialize with allowed directory paths
        
        Args:
            allowed_paths: List of directory paths the tool can access
        """
        super().__init__(name=self.name, description=self.description)
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories"""
        resolved_path = path.resolve()
        
        for allowed in self.allowed_paths:
            try:
                resolved_path.relative_to(allowed)
                return True
            except ValueError:
                continue
        
        return False
    
    async def execute(
        self,
        directory_path: str,
        pattern: Optional[str] = None,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List directory contents
        
        Args:
            directory_path: Path to the directory
            pattern: Optional glob pattern to filter files
            recursive: Whether to list recursively
            
        Returns:
            Dictionary with directory contents or error
        """
        try:
            path = Path(directory_path).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return {
                    "success": False,
                    "error": f"Access denied: {directory_path} is outside allowed directories"
                }
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}"
                }
            
            if not path.is_dir():
                return {
                    "success": False,
                    "error": f"Not a directory: {directory_path}"
                }
            
            # List contents
            items = []
            
            if recursive and pattern:
                # Recursive with pattern
                paths = path.rglob(pattern)
            elif recursive:
                # Recursive without pattern
                paths = path.rglob("*")
            elif pattern:
                # Non-recursive with pattern
                paths = path.glob(pattern)
            else:
                # Non-recursive without pattern
                paths = path.iterdir()
            
            for item in paths:
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                items.append(item_info)
            
            return {
                "success": True,
                "directory": str(path),
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {directory_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class DiaryTool(BaseTool):
    """
    Specialized tool for Minion diary operations
    
    This tool provides diary-specific operations like creating
    timestamped entries, searching entries, and maintaining
    diary structure.
    """
    
    name = "diary_tool"
    description = "Manage personal diary entries"
    
    def __init__(self, diary_base_path: str):
        """
        Initialize with diary base path
        
        Args:
            diary_base_path: Base directory for all Minion diaries
        """
        super().__init__(name=self.name, description=self.description)
        self.diary_base_path = Path(diary_base_path).resolve()
        self.diary_base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_minion_diary_path(self, minion_id: str) -> Path:
        """Get the diary directory for a specific Minion"""
        return self.diary_base_path / minion_id
    
    def _get_diary_file_path(self, minion_id: str, date: Optional[datetime] = None) -> Path:
        """Get the diary file path for a specific date"""
        if date is None:
            date = datetime.now()
        
        diary_dir = self._get_minion_diary_path(minion_id)
        diary_dir.mkdir(parents=True, exist_ok=True)
        
        # Organize by year/month
        year_month = date.strftime("%Y-%m")
        file_name = date.strftime("%Y-%m-%d.md")
        
        return diary_dir / year_month / file_name
    
    async def execute(
        self,
        action: str,
        minion_id: str,
        content: Optional[str] = None,
        date: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute diary operations
        
        Args:
            action: Action to perform (write, read, search, list)
            minion_id: ID of the Minion
            content: Content to write (for write action)
            date: Optional date string (ISO format)
            search_query: Query for search action
            
        Returns:
            Result of the diary operation
        """
        try:
            if action == "write":
                return await self._write_entry(minion_id, content or "", date)
            elif action == "read":
                return await self._read_entries(minion_id, date)
            elif action == "search":
                return await self._search_entries(minion_id, search_query or "")
            elif action == "list":
                return await self._list_entries(minion_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Diary operation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _write_entry(self, minion_id: str, content: str, date: Optional[str]) -> Dict[str, Any]:
        """Write a diary entry"""
        entry_date = datetime.fromisoformat(date) if date else datetime.now()
        file_path = self._get_diary_file_path(minion_id, entry_date)
        
        # Create directory structure
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format entry with timestamp
        timestamp = entry_date.strftime("%H:%M:%S")
        formatted_entry = f"\n\n## {timestamp}\n\n{content}"
        
        # Append to file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(formatted_entry)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "timestamp": entry_date.isoformat()
        }
    
    async def _read_entries(self, minion_id: str, date: Optional[str]) -> Dict[str, Any]:
        """Read diary entries for a date"""
        entry_date = datetime.fromisoformat(date) if date else datetime.now()
        file_path = self._get_diary_file_path(minion_id, entry_date)
        
        if not file_path.exists():
            return {
                "success": True,
                "entries": [],
                "message": "No entries for this date"
            }
        
        content = file_path.read_text(encoding="utf-8")
        
        return {
            "success": True,
            "content": content,
            "file_path": str(file_path),
            "date": entry_date.date().isoformat()
        }
    
    async def _search_entries(self, minion_id: str, query: str) -> Dict[str, Any]:
        """Search diary entries"""
        diary_dir = self._get_minion_diary_path(minion_id)
        
        if not diary_dir.exists():
            return {
                "success": True,
                "results": [],
                "message": "No diary found"
            }
        
        results = []
        
        # Search all diary files
        for diary_file in diary_dir.rglob("*.md"):
            try:
                content = diary_file.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    # Extract matching lines
                    lines = content.split("\n")
                    matches = [
                        {
                            "line": line.strip(),
                            "line_number": i + 1
                        }
                        for i, line in enumerate(lines)
                        if query.lower() in line.lower()
                    ]
                    
                    results.append({
                        "file": str(diary_file.relative_to(diary_dir)),
                        "matches": matches
                    })
            except Exception as e:
                logger.error(f"Error searching {diary_file}: {e}")
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_files": len(results)
        }
    
    async def _list_entries(self, minion_id: str) -> Dict[str, Any]:
        """List all diary entries"""
        diary_dir = self._get_minion_diary_path(minion_id)
        
        if not diary_dir.exists():
            return {
                "success": True,
                "entries": [],
                "message": "No diary found"
            }
        
        entries = []
        
        for diary_file in sorted(diary_dir.rglob("*.md")):
            stat = diary_file.stat()
            entries.append({
                "file": str(diary_file.relative_to(diary_dir)),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return {
            "success": True,
            "entries": entries,
            "total": len(entries)
        }


def create_filesystem_tools(config: Dict[str, Any]) -> List[BaseTool]:
    """
    Create filesystem tools with configuration
    
    Args:
        config: Configuration with allowed_paths and diary_path
        
    Returns:
        List of configured filesystem tools
    """
    allowed_paths = config.get("allowed_paths", [])
    diary_path = config.get("diary_path", "./diaries")
    
    tools = [
        FileSystemReadTool(allowed_paths),
        FileSystemWriteTool(allowed_paths),
        FileSystemListTool(allowed_paths),
        DiaryTool(diary_path)
    ]
    
    return tools
