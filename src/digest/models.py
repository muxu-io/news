"""Data models for the digest system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NormalizedItem:
    """A content item normalized to a common schema."""

    title: str
    url: str
    date: datetime
    author: str
    body: str
    source_name: str
    source_type: str
    item_id: str | None = None

    def __post_init__(self) -> None:
        if self.item_id is None:
            self.item_id = self.url


@dataclass
class SourceError:
    """An error that occurred while fetching a source."""

    source_name: str
    source_type: str
    error: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FetchResult:
    """Result of fetching from a source."""

    source_name: str
    items: list[NormalizedItem]
    error: SourceError | None = None


@dataclass
class DigestMetadata:
    """Metadata for a generated digest."""

    title: str
    date: str
    generated_at: str
    config: str
    sources_fetched: int
    sources_failed: int
    items_processed: int
    time_window: str
    errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class SourceConfig:
    """Configuration for a single source."""

    name: str
    type: str
    config: dict[str, Any]


@dataclass
class FilterConfig:
    """Configuration for content filtering."""

    time_window: str = "24h"
    use_state: bool = True
    keywords_include: list[str] = field(default_factory=list)
    keywords_exclude: list[str] = field(default_factory=list)
    min_content_length: int = 50


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    delay_between_sources: float = 2.0
    delay_between_requests: float = 1.0


@dataclass
class SummarizerConfig:
    """Configuration for the LLM summarizer."""

    provider: str
    model: str
    max_tokens: int
    prompt: str


@dataclass
class OutputConfig:
    """Configuration for an output adapter."""

    type: str
    config: dict[str, Any]


@dataclass
class DigestConfig:
    """Complete configuration for a digest."""

    name: str
    slug: str
    description: str
    sources: list[SourceConfig]
    filters: FilterConfig
    rate_limit: RateLimitConfig
    summarizer: SummarizerConfig
    outputs: list[OutputConfig]
    schedule: str = ""
