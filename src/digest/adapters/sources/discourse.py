"""Discourse forum source adapter."""

import asyncio
import logging
from typing import TYPE_CHECKING

import feedparser

from ...models import FetchResult, NormalizedItem, SourceConfig, SourceError
from ...utils import create_http_client, normalize_feed_entry
from ..base import SourceAdapter

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class DiscourseAdapter(SourceAdapter):
    """Adapter for Discourse forums via RSS feeds."""

    source_type = "discourse"

    def __init__(self, config: SourceConfig) -> None:
        super().__init__(config)
        self.base_url = config.config.get("base_url", "").rstrip("/")
        if not self.base_url:
            raise ValueError(f"Discourse source '{self.name}' missing 'base_url' field")

        self.categories = config.config.get("categories", [])
        self.tags = config.config.get("tags", [])

        if not self.categories and not self.tags:
            raise ValueError(
                f"Discourse source '{self.name}' must have at least one category or tag"
            )

    async def fetch(self, rate_limit_delay: float = 1.0) -> FetchResult:
        """Fetch items from Discourse RSS feeds."""
        all_items: list[NormalizedItem] = []
        errors: list[str] = []

        async with create_http_client() as client:
            # Fetch category feeds
            for category in self.categories:
                try:
                    items = await self._fetch_category(
                        client, category, rate_limit_delay
                    )
                    all_items.extend(items)
                except Exception as e:
                    error_msg = f"Category '{category.get('path', 'unknown')}': {e}"
                    logger.warning(f"Discourse '{self.name}': {error_msg}")
                    errors.append(error_msg)

            # Fetch tag feeds
            for tag in self.tags:
                try:
                    items = await self._fetch_tag(client, tag, rate_limit_delay)
                    all_items.extend(items)
                except Exception as e:
                    error_msg = f"Tag '{tag}': {e}"
                    logger.warning(f"Discourse '{self.name}': {error_msg}")
                    errors.append(error_msg)

        logger.info(f"Discourse '{self.name}': fetched {len(all_items)} items")

        # Return error only if all fetches failed
        error = None
        if errors and not all_items:
            error = SourceError(
                source_name=self.name,
                source_type=self.source_type,
                error="; ".join(errors),
            )

        return FetchResult(source_name=self.name, items=all_items, error=error)

    async def _fetch_category(
        self, client: "httpx.AsyncClient", category: dict, delay: float
    ) -> list[NormalizedItem]:
        """Fetch items from a category RSS feed."""
        path = category.get("path", "")
        cat_id = category.get("id")

        if cat_id:
            url = f"{self.base_url}/c/{path}/{cat_id}.rss"
        else:
            url = f"{self.base_url}/c/{path}.rss"

        return await self._fetch_feed(client, url, delay)

    async def _fetch_tag(
        self, client: "httpx.AsyncClient", tag: str, delay: float
    ) -> list[NormalizedItem]:
        """Fetch items from a tag RSS feed."""
        url = f"{self.base_url}/tag/{tag}.rss"
        return await self._fetch_feed(client, url, delay)

    async def _fetch_feed(self, client, url: str, delay: float) -> list[NormalizedItem]:
        """Fetch and parse an RSS feed."""
        await asyncio.sleep(delay)

        response = await client.get(url)
        response.raise_for_status()

        feed = feedparser.parse(response.text)

        if feed.bozo and not feed.entries:
            raise ValueError(f"Feed parse error: {feed.bozo_exception}")

        items = []
        for entry in feed.entries:
            try:
                item = normalize_feed_entry(entry, self.name, self.source_type)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to normalize Discourse entry: {e}")
                continue

        return items
