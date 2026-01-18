"""HyperKitty (Mailman 3) mailing list source adapter."""

import logging
from typing import TYPE_CHECKING

import feedparser

from ...models import FetchResult, NormalizedItem, SourceConfig, SourceError
from ...utils import create_http_client, normalize_feed_entry
from ..base import SourceAdapter

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class HyperKittyAdapter(SourceAdapter):
    """Adapter for HyperKitty/Mailman 3 mailing list archives."""

    source_type = "hyperkitty"

    def __init__(self, config: SourceConfig) -> None:
        super().__init__(config)
        self.base_url = config.config.get("base_url", "").rstrip("/")
        if not self.base_url:
            raise ValueError(
                f"HyperKitty source '{self.name}' missing 'base_url' field"
            )

        self.list_address = config.config.get("list_address", "")
        if not self.list_address:
            raise ValueError(
                f"HyperKitty source '{self.name}' missing 'list_address' field"
            )

    async def fetch(self, rate_limit_delay: float = 1.0) -> FetchResult:
        """Fetch items from HyperKitty archives."""
        # Try different feed URL patterns
        # Fedora uses: /archives/list/{list_address}/feed/
        feed_urls = [
            f"{self.base_url}/{self.list_address}/feed/",
            f"{self.base_url}/{self.list_address}/latest.rss",
            f"{self.base_url}/{self.list_address}/atom.xml",
        ]

        async with create_http_client() as client:
            for url in feed_urls:
                try:
                    items = await self._try_fetch_feed(client, url)
                    if items is not None:
                        logger.info(
                            f"HyperKitty '{self.name}': fetched {len(items)} items from {url}"
                        )
                        return FetchResult(source_name=self.name, items=items)
                except Exception as e:
                    logger.debug(f"HyperKitty '{self.name}': {url} failed: {e}")
                    continue

        # All methods failed
        return FetchResult(
            source_name=self.name,
            items=[],
            error=SourceError(
                source_name=self.name,
                source_type=self.source_type,
                error="Could not fetch feed (tried RSS and Atom URLs)",
            ),
        )

    async def _try_fetch_feed(
        self, client: "httpx.AsyncClient", url: str
    ) -> list[NormalizedItem] | None:
        """Try to fetch and parse a feed URL."""
        response = await client.get(url)

        if response.status_code == 404:
            return None

        response.raise_for_status()

        feed = feedparser.parse(response.text)

        if feed.bozo and not feed.entries:
            return None

        items = []
        for entry in feed.entries:
            try:
                item = normalize_feed_entry(entry, self.name, self.source_type)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to normalize HyperKitty entry: {e}")
                continue

        return items
