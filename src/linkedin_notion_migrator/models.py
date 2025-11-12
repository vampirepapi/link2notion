"""Data models used by the migrator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SavedPost:
    """Representation of a saved LinkedIn post."""

    urn: str
    content: str
    author: Optional[str]
    url: Optional[str]
    posted_at: Optional[datetime]
    saved_at: Optional[datetime]
    raw_date_text: Optional[str] = None
    raw_saved_text: Optional[str] = None

    def to_summary(self) -> str:
        """Return a summary string for logging purposes."""
        return f"{self.urn} - {self.author or 'Unknown Author'}"
