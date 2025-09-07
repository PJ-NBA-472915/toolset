#!/usr/bin/env python3
"""
Service for running tools
"""

import logging
import subprocess
import sys
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ToolService:
    """Manages tool execution"""

    def run_tool(self, tool_name: str, tool_args: list[str] = None):
        """Run a specific tool from the toolset."""
        logger.info(f"Running tool: {tool_name} with args: {tool_args}")

        toolset_path = Path(__file__).parent.parent.parent
        tool_path = toolset_path / "tools" / tool_name

        if not tool_path.exists():
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        main_file = tool_path / "main.py"
        if not main_file.exists():
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' does not have a main.py file")

        try:
            cmd = [sys.executable, str(main_file)]
            if tool_args:
                cmd.extend(tool_args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=tool_path,
                check=False  # We handle the non-zero exit code ourselves
            )

            return {
                "tool": tool_name,
                "args": tool_args,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to execute tool '{tool_name}': {e}")
