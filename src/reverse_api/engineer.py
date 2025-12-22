"""Reverse engineering module using Claude Agent SDK."""

import asyncio
import json
from pathlib import Path
from typing import Optional

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)

from .utils import get_scripts_dir, get_timestamp
from .tui import ClaudeUI


class APIReverseEngineer:
    """Uses Claude to analyze HAR files and generate Python API scripts."""

    def __init__(
        self,
        run_id: str,
        har_path: Path,
        prompt: str,
        model: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        verbose: bool = True,
    ):
        self.run_id = run_id
        self.har_path = har_path
        self.prompt = prompt
        self.model = model
        self.additional_instructions = additional_instructions
        self.scripts_dir = get_scripts_dir(run_id)
        self.ui = ClaudeUI(verbose=verbose)

    def _build_analysis_prompt(self) -> str:
        """Build the prompt for Claude to analyze the HAR file."""
        base_prompt = f"""Analyze the HAR file at {self.har_path} and reverse engineer the APIs captured.

Original user prompt: {self.prompt}

Your task:
1. Read and analyze the HAR file to understand the API calls made
2. Identify authentication patterns (cookies, tokens, headers)
3. Extract request/response patterns for each endpoint
4. Generate a clean, well-documented Python script that replicates these API calls

The Python script should:
- Use the `requests` library
- Include proper authentication handling
- Have functions for each distinct API endpoint
- Include type hints and docstrings
- Handle errors gracefully
- Be production-ready

Save the generated Python script to: {self.scripts_dir / 'api_client.py'}
Also create a brief README.md in the same folder explaining the APIs discovered.
"""
        if self.additional_instructions:
            base_prompt += f"\n\nAdditional instructions:\n{self.additional_instructions}"
        
        return base_prompt

    async def analyze_and_generate(self) -> Optional[str]:
        """Run the reverse engineering analysis with Claude."""
        self.ui.header(self.run_id, self.prompt, self.model)
        self.ui.start_analysis()

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Bash", "Glob", "Grep", "WebSearch", "WebFetch"],
            permission_mode="acceptEdits",
            cwd=str(self.scripts_dir.parent.parent),  # Project root
            model=self.model,
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(self._build_analysis_prompt())

                # Process response and show progress with TUI
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, ToolUseBlock):
                                self.ui.tool_start(block.name, block.input)
                            elif isinstance(block, ToolResultBlock):
                                # Determine tool name from context
                                is_error = block.is_error if block.is_error else False
                                self.ui.tool_result("Tool", is_error)
                            elif isinstance(block, TextBlock):
                                self.ui.thinking(block.text)
                    
                    elif isinstance(message, ResultMessage):
                        if message.is_error:
                            self.ui.error(message.result or "Unknown error")
                            return None
                        else:
                            script_path = str(self.scripts_dir / 'api_client.py')
                            self.ui.success(script_path)
                            return script_path

        except Exception as e:
            self.ui.error(str(e))
            self.ui.console.print(
                "\n[dim]Make sure Claude Code CLI is installed: "
                "npm install -g @anthropic-ai/claude-code[/dim]"
            )
            return None

        return None


def run_reverse_engineering(
    run_id: str,
    har_path: Path,
    prompt: str,
    model: Optional[str] = None,
    additional_instructions: Optional[str] = None,
    verbose: bool = True,
) -> Optional[str]:
    """Synchronous wrapper for reverse engineering."""
    engineer = APIReverseEngineer(
        run_id=run_id,
        har_path=har_path,
        prompt=prompt,
        model=model,
        additional_instructions=additional_instructions,
        verbose=verbose,
    )
    return asyncio.run(engineer.analyze_and_generate())
