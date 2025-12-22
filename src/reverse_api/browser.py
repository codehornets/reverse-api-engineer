"""Browser management with Playwright for HAR recording."""

import json
import signal
import sys
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext

from .utils import get_har_dir, get_timestamp


class ManualBrowser:
    """Manages a Playwright browser session with HAR recording."""

    def __init__(self, run_id: str, prompt: str):
        self.run_id = run_id
        self.prompt = prompt
        self.har_dir = get_har_dir(run_id)
        self.har_path = self.har_dir / "recording.har"
        self.metadata_path = self.har_dir / "metadata.json"
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._start_time: Optional[str] = None

    def _save_metadata(self, end_time: str) -> None:
        """Save run metadata to JSON file."""
        metadata = {
            "run_id": self.run_id,
            "prompt": self.prompt,
            "start_time": self._start_time,
            "end_time": end_time,
            "har_file": str(self.har_path),
        }
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def _handle_signal(self, signum, frame) -> None:
        """Handle interrupt signals gracefully."""
        print("\n\nClosing browser and saving HAR file...")
        self.close()
        sys.exit(0)

    def start(self, start_url: Optional[str] = None) -> Path:
        """Start the browser with HAR recording enabled. Returns HAR path when done."""
        self._start_time = get_timestamp()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        print(f"Starting browser session...")
        print(f"Run ID: {self.run_id}")
        print(f"HAR will be saved to: {self.har_path}")
        print(f"\nPrompt: {self.prompt}")
        print("\n" + "=" * 50)
        print("Browse the web and interact with APIs you want to capture.")
        print("Close the browser window or press Ctrl+C when done.")
        print("=" * 50 + "\n")

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        
        # Create context with HAR recording
        self._context = self._browser.new_context(
            record_har_path=str(self.har_path),
            record_har_content="attach",  # Include response bodies
            no_viewport=True,  # Use full window size
        )

        # Open initial page
        page = self._context.new_page()
        if start_url:
            page.goto(start_url)

        # Wait for browser to close
        try:
            while self._context.pages:
                # Check every 500ms if browser is still open
                self._context.pages[0].wait_for_timeout(500)
        except Exception:
            pass  # Browser was closed

        return self.close()

    def close(self) -> Path:
        """Close the browser and save HAR file. Returns HAR path."""
        end_time = get_timestamp()
        
        if self._context:
            try:
                self._context.close()  # This saves the HAR file
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        # Save metadata
        self._save_metadata(end_time)
        
        print(f"\n✓ HAR file saved to: {self.har_path}")
        print(f"✓ Metadata saved to: {self.metadata_path}")
        print(f"\nRun ID: {self.run_id}")
        
        return self.har_path
