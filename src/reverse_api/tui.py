"""Rich Terminal UI for Claude SDK interactions."""

from typing import Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, MINIMAL, HEAVY
from rich.padding import Padding
from rich.rule import Rule


# Tool icons for visual clarity
TOOL_ICONS = {
    "Read": "📖",
    "Write": "✏️",
    "Edit": "📝",
    "Bash": "💻",
    "Glob": "🔍",
    "Grep": "🔎",
    "WebSearch": "🌐",
    "WebFetch": "🌍",
    "Task": "📋",
    "default": "🔧",
}

# Tool colors
TOOL_COLORS = {
    "Read": "blue",
    "Write": "green",
    "Edit": "yellow",
    "Bash": "magenta",
    "Glob": "cyan",
    "Grep": "cyan",
    "WebSearch": "bright_blue",
    "WebFetch": "bright_blue",
    "default": "white",
}


class ClaudeUI:
    """Interactive terminal UI for Claude SDK operations."""
    
    def __init__(self, verbose: bool = True):
        self.console = Console()
        self.verbose = verbose
        self._tool_count = 0
        self._tools_used: list[str] = []
    
    def header(self, run_id: str, prompt: str, model: Optional[str] = None) -> None:
        """Display the session header."""
        # Create a clean header table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("key", style="dim", width=12)
        table.add_column("value")
        
        table.add_row("Run ID", f"[yellow]{run_id}[/yellow]")
        if model:
            table.add_row("Model", f"[green]{model}[/green]")
        table.add_row("Task", f"[white]{prompt}[/white]")
        
        self.console.print()
        self.console.print(Panel(
            table,
            title="[bold cyan]🔍 Reverse API Analysis[/bold cyan]",
            border_style="cyan",
            box=ROUNDED,
        ))
    
    def start_analysis(self) -> None:
        """Display analysis start message."""
        self.console.print()
        self.console.print(Rule("[bold]Claude is analyzing...[/bold]", style="dim"))
        self.console.print()
    
    def tool_start(self, tool_name: str, tool_input: dict) -> None:
        """Display when a tool starts execution."""
        self._tool_count += 1
        self._tools_used.append(tool_name)
        
        icon = TOOL_ICONS.get(tool_name, TOOL_ICONS["default"])
        color = TOOL_COLORS.get(tool_name, TOOL_COLORS["default"])
        
        # Build input summary
        input_summary = self._summarize_input(tool_name, tool_input)
        
        # Compact single-line format
        self.console.print(
            f"  [{color}]●[/{color}] {icon} [bold {color}]{tool_name:12}[/bold {color}] {input_summary}"
        )
    
    def tool_result(self, tool_name: str, is_error: bool = False) -> None:
        """Display when a tool completes (only show on error)."""
        if is_error:
            self.console.print(f"  [red]✗ {tool_name} failed[/red]")
    
    def thinking(self, text: str, max_length: int = 100) -> None:
        """Display Claude's thinking/response text."""
        if not self.verbose:
            return
        
        # Only show substantial thinking (skip short status updates)
        if len(text) < 20:
            return
        
        # Truncate and clean
        display_text = text[:max_length].replace("\n", " ").strip()
        if len(text) > max_length:
            display_text += "..."
        
        self.console.print(f"  [dim]→ {display_text}[/dim]")
    
    def progress(self, message: str) -> None:
        """Display a progress message."""
        self.console.print(f"  [dim italic]{message}[/dim italic]")
    
    def success(self, script_path: str) -> None:
        """Display success message with generated script path."""
        self.console.print()
        self.console.print(Rule(style="green"))
        
        # Summary
        summary = Text()
        summary.append("✨ ", style="bold")
        summary.append("Analysis Complete\n\n", style="bold green")
        summary.append(f"   Tools: ", style="dim")
        summary.append(f"{self._tool_count}\n", style="white")
        summary.append(f"   Script: ", style="dim")
        summary.append(f"{script_path}", style="cyan underline")
        
        self.console.print(summary)
        self.console.print()
    
    def error(self, message: str) -> None:
        """Display error message."""
        self.console.print()
        self.console.print(f"[bold red]✗ Error:[/bold red] {message}")
    
    def _summarize_input(self, tool_name: str, tool_input: dict) -> str:
        """Create a brief summary of tool input."""
        if tool_name == "Read":
            path = tool_input.get("file_path", "")
            return f"[dim]{self._truncate_path(path)}[/dim]"
        elif tool_name == "Write":
            path = tool_input.get("file_path", "")
            return f"[dim]→ {self._truncate_path(path)}[/dim]"
        elif tool_name == "Edit":
            path = tool_input.get("file_path", "")
            return f"[dim]{self._truncate_path(path)}[/dim]"
        elif tool_name == "Bash":
            cmd = tool_input.get("command", "")
            cmd = cmd.replace("\n", " ").strip()
            return f"[dim]$ {cmd[:60]}{'...' if len(cmd) > 60 else ''}[/dim]"
        elif tool_name in ("Grep", "Glob"):
            pattern = tool_input.get("pattern", "")
            return f"[dim]'{pattern}'[/dim]"
        elif tool_name == "WebSearch":
            query = tool_input.get("query", "")
            return f"[dim]'{query[:50]}{'...' if len(query) > 50 else ''}'[/dim]"
        elif tool_name == "WebFetch":
            url = tool_input.get("url", "")
            return f"[dim]{url[:60]}{'...' if len(url) > 60 else ''}[/dim]"
        return ""
    
    def _truncate_path(self, path: str, max_len: int = 60) -> str:
        """Truncate a path for display."""
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3):]


def get_model_choices() -> list[dict]:
    """Get available model choices for questionary."""
    return [
        {"name": "Claude Sonnet (default, balanced)", "value": "sonnet"},
        {"name": "Claude Opus (most capable)", "value": "opus"},
        {"name": "Claude Haiku (fastest)", "value": "haiku"},
    ]
