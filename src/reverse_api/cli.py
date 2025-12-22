"""CLI for reverse-api package."""

import click
import questionary
from rich.console import Console

from .browser import ManualBrowser
from .utils import generate_run_id
from .tui import get_model_choices


console = Console()


def prompt_interactive_options(
    prompt: str | None = None,
    url: str | None = None,
    reverse_engineer: bool | None = None,
    model: str | None = None,
) -> dict:
    """Prompt user for essential options interactively (minimal prompts)."""
    console.print("\n[bold cyan]🔍 Reverse API[/bold cyan]\n")
    
    # Only ask for the essential: prompt description
    if prompt is None:
        prompt = questionary.text(
            "What APIs do you want to capture?",
            instruction="(e.g., 'login flow for example.com')",
        ).ask()
    
    if not prompt:
        raise click.Abort()
    
    # Starting URL (optional)
    if url is None:
        url = questionary.text(
            "Starting URL:",
            instruction="(press Enter to skip)",
            default="",
        ).ask()
    
    # Ask if they want to reverse engineer immediately
    if reverse_engineer is False: # If True, they already specified it via -r
        reverse_engineer = questionary.confirm(
            "Run reverse engineering (Claude) immediately after capture?",
            default=True,
        ).ask()
    
    if model is None and reverse_engineer:
        model = questionary.select(
            "Select Claude model:",
            choices=["sonnet", "opus", "haiku"],
            default="sonnet",
        ).ask()
    
    return {
        "prompt": prompt,
        "url": url if url else None,
        "reverse_engineer": reverse_engineer,
        "model": model,
    }


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option()
def main(ctx: click.Context):
    """Reverse API - Capture browser traffic for API reverse engineering."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(manual)


@main.command()
@click.option(
    "--prompt", "-p",
    default=None,
    help="Description of what APIs you want to capture. If omitted, enters interactive mode.",
)
@click.option(
    "--url", "-u",
    default=None,
    help="Optional starting URL to navigate to.",
)
@click.option(
    "--reverse-engineer", "-r",
    is_flag=True,
    default=False,
    help="Automatically reverse engineer APIs using Claude after capture.",
)
@click.option(
    "--model", "-m",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default=None,
    help="Claude model to use for reverse engineering.",
)
@click.option(
    "--instructions", "-i",
    default=None,
    help="Additional instructions for Claude when reverse engineering.",
)
def manual(
    prompt: str | None,
    url: str | None,
    reverse_engineer: bool,
    model: str | None,
    instructions: str | None,
):
    """Start a manual browser session with HAR recording.
    
    Opens a Chromium browser where you can interact with websites.
    All network traffic is recorded to a HAR file for later analysis.
    Close the browser or press Ctrl+C when done.
    
    If --prompt is omitted, enters interactive mode.
    
    Use -r to auto-generate a Python API client after capture.
    """
    # Interactive mode if no prompt provided
    if prompt is None:
        options = prompt_interactive_options(
            prompt=prompt,
            url=url,
            reverse_engineer=reverse_engineer,
            model=model,
        )
        prompt = options["prompt"]
        url = options["url"]
        reverse_engineer = options["reverse_engineer"]
        model = options["model"]
    
    run_id = generate_run_id()
    browser = ManualBrowser(run_id=run_id, prompt=prompt)
    har_path = browser.start(start_url=url)
    
    if reverse_engineer:
        from .engineer import run_reverse_engineering
        script_path = run_reverse_engineering(
            run_id=run_id,
            har_path=har_path,
            prompt=prompt,
            model=model,
            additional_instructions=instructions,
        )
        if script_path:
            console.print(f"\n[green]✓[/green] Generated API script: [cyan]{script_path}[/cyan]")


@main.command()
@click.argument("run_id")
@click.option(
    "--model", "-m",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default=None,
    help="Claude model to use for reverse engineering.",
)
@click.option(
    "--instructions", "-i",
    default=None,
    help="Additional instructions for Claude.",
)
def engineer(run_id: str, model: str | None, instructions: str | None):
    """Reverse engineer APIs from a previous capture.
    
    Analyzes the HAR file from a previous run and generates
    a Python API client script using Claude.
    """
    import json
    from pathlib import Path
    from .utils import get_har_dir
    from .engineer import run_reverse_engineering
    
    har_dir = get_har_dir(run_id)
    har_path = har_dir / "recording.har"
    metadata_path = har_dir / "metadata.json"
    
    if not har_path.exists():
        console.print(f"[red]Error:[/red] HAR file not found for run ID: {run_id}")
        console.print(f"[dim]Expected path: {har_path}[/dim]")
        return
    
    # Load prompt from metadata if available
    prompt = "Reverse engineer the captured APIs"
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
            prompt = metadata.get("prompt", prompt)
    
    script_path = run_reverse_engineering(
        run_id=run_id,
        har_path=har_path,
        prompt=prompt,
        model=model,
        additional_instructions=instructions,
    )
    if script_path:
        console.print(f"\n[green]✓[/green] Generated API script: [cyan]{script_path}[/cyan]")


if __name__ == "__main__":
    main()
