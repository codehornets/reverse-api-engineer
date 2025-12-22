"""Utility functions for run ID generation and path management."""

import uuid
from datetime import datetime
from pathlib import Path


def generate_run_id() -> str:
    """Generate a unique run ID using a short UUID format."""
    return uuid.uuid4().hex[:12]


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_har_dir(run_id: str) -> Path:
    """Get the HAR directory for a specific run."""
    har_dir = get_project_root() / "har" / run_id
    har_dir.mkdir(parents=True, exist_ok=True)
    return har_dir


def get_scripts_dir(run_id: str) -> Path:
    """Get the scripts directory for a specific run."""
    scripts_dir = get_project_root() / "scripts" / run_id
    scripts_dir.mkdir(parents=True, exist_ok=True)
    return scripts_dir


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()
