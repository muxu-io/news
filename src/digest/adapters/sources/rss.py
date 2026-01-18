"""RSS feed source adapter."""

import logging

import feedparser

from ...models import FetchResult, SourceConfig, SourceError
from ...utils import create_http_client, normalize_feed_entry
from ..base import SourceAdapter

logger = logging.getLogger(__name__)


class RSSAdapter(SourceAdapter):
    """Adapter for RSS/Atom feeds."""

    source_type = "rss"

    def __init__(self, config: SourceConfig) -> None:
        super().__init__(config)
        self.url = config.config.get("url")
        if not self.url:
            raise ValueError(f"RSS source '{self.name}' missing 'url' field")

    async def fetch(self, rate_limit_delay: float = 1.0) -> FetchResult:
        """Fetch items from the RSS feed."""
        try:
            async with create_http_client() as client:
                response = await client.get(self.url)
                response.raise_for_status()
                content = response.text

            feed = feedparser.parse(content)

            if feed.bozo and not feed.entries:
                error_msg = (
                    str(feed.bozo_exception)
                    if feed.bozo_exception
                    else "Unknown parse error"
                )
                return FetchResult(
                    source_name=self.name,
                    items=[],
                    error=SourceError(
                        source_name=self.name,
                        source_type=self.source_type,
                        error=f"Feed parse error: {error_msg}",
                    ),
                )

            items = []
            for entry in feed.entries:
                try:
                    item = normalize_feed_entry(entry, self.name, self.source_type)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to normalize RSS entry: {e}")
                    continue

            logger.info(f"RSS '{self.name}': fetched {len(items)} items")
            return FetchResult(source_name=self.name, items=items)

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "response"):
                error_msg = (
                    f"HTTP {e.response.status_code} - {e.response.reason_phrase}"
                )
            return FetchResult(
                source_name=self.name,
                items=[],
                error=SourceError(
                    source_name=self.name,
                    source_type=self.source_type,
                    error=error_msg,
                ),
            )
