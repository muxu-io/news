"""State management for tracking processed items."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class StateManager:
    """Manages state persistence for tracking processed items."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.state_file = state_dir / "state.json"
        self._state: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load state from file or create default."""
        if not self.state_file.exists():
            return {
                "schema_version": SCHEMA_VERSION,
                "last_run": None,
                "sources": {},
            }

        with open(self.state_file) as f:
            state = json.load(f)

        # Handle schema migrations if needed
        if state.get("schema_version", 0) < SCHEMA_VERSION:
            state = self._migrate(state)

        return state

    def _migrate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Migrate state from older schema versions."""
        # Currently no migrations needed
        state["schema_version"] = SCHEMA_VERSION
        return state

    def save(self) -> None:
        """Save state to file."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self._state, f, indent=2, default=str)

    def get_last_seen_date(self, source_name: str) -> datetime | None:
        """Get the last seen date for a source."""
        source_state = self._state["sources"].get(source_name)
        if not source_state:
            return None

        last_seen = source_state.get("last_seen_date")
        if not last_seen:
            return None

        return datetime.fromisoformat(last_seen.replace("Z", "+00:00"))

    def update_source(
        self,
        source_name: str,
        last_seen_date: datetime,
        last_seen_id: str,
    ) -> None:
        """Update state for a source after processing."""
        self._state["sources"][source_name] = {
            "last_seen_date": last_seen_date.isoformat(),
            "last_seen_id": last_seen_id,
        }

    def record_run(
        self,
        success: bool,
        items_processed: int,
        digest_file: str | None = None,
    ) -> None:
        """Record information about the current run."""
        self._state["last_run"] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success": success,
            "items_processed": items_processed,
            "digest_file": digest_file,
        }

    @property
    def last_run_timestamp(self) -> datetime | None:
        """Get the timestamp of the last run."""
        last_run = self._state.get("last_run")
        if not last_run:
            return None

        timestamp = last_run.get("timestamp")
        if not timestamp:
            return None

        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
