"""Generic REST API source adapter."""

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from dateutil import parser as date_parser

from ...models import FetchResult, NormalizedItem, SourceConfig, SourceError
from ...utils import clean_html, ensure_utc
from ..base import SourceAdapter

logger = logging.getLogger(__name__)


class RestAPIAdapter(SourceAdapter):
    """Adapter for generic REST APIs with configurable field mapping."""

    source_type = "rest_api"

    def __init__(self, config: SourceConfig) -> None:
        super().__init__(config)
        self.url = config.config.get("url")
        if not self.url:
            raise ValueError(f"REST API source '{self.name}' missing 'url' field")

        self.method = config.config.get("method", "GET").upper()
        self.headers = config.config.get("headers", {})
        self.mapping = config.config.get("mapping", {})

        # Pagination config
        self.pagination = config.config.get("pagination", {})
        self.max_pages = self.pagination.get("max_pages", 5)

    async def fetch(self, rate_limit_delay: float = 1.0) -> FetchResult:
        """Fetch items from the REST API."""
        import asyncio

        all_items: list[NormalizedItem] = []

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            ) as client:
                url = self.url
                page = 0

                while url and page < self.max_pages:
                    if page > 0:
                        await asyncio.sleep(rate_limit_delay)

                    if self.method == "GET":
                        response = await client.get(url, headers=self.headers)
                    elif self.method == "POST":
                        response = await client.post(url, headers=self.headers)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {self.method}")

                    response.raise_for_status()
                    data = response.json()

                    # Extract items from response
                    items_data = self._extract_items(data)
                    if not items_data:
                        break

                    for item_data in items_data:
                        try:
                            item = self._normalize_item(item_data)
                            all_items.append(item)
                        except Exception as e:
                            logger.warning(f"Failed to normalize API item: {e}")
                            continue

                    # Get next page URL if pagination is configured
                    url = self._get_next_page_url(data, response)
                    page += 1

            logger.info(f"REST API '{self.name}': fetched {len(all_items)} items")
            return FetchResult(source_name=self.name, items=all_items)

        except httpx.HTTPStatusError as e:
            return FetchResult(
                source_name=self.name,
                items=[],
                error=SourceError(
                    source_name=self.name,
                    source_type=self.source_type,
                    error=f"HTTP {e.response.status_code} - {e.response.reason_phrase}",
                ),
            )
        except Exception as e:
            return FetchResult(
                source_name=self.name,
                items=[],
                error=SourceError(
                    source_name=self.name,
                    source_type=self.source_type,
                    error=str(e),
                ),
            )

    def _extract_items(self, data: Any) -> list[dict]:
        """Extract the items list from the API response."""
        items_path = self.pagination.get("items_path", "")

        if not items_path:
            # Assume the response is the list itself
            if isinstance(data, list):
                return data
            return []

        # Navigate the path to find items
        current = data
        for key in items_path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return []

        return current if isinstance(current, list) else []

    def _get_next_page_url(self, data: dict, response: httpx.Response) -> str | None:
        """Get the URL for the next page of results."""
        next_url_path = self.pagination.get("next_url_path", "")

        if not next_url_path:
            # Check for Link header (GitHub-style pagination)
            link_header = response.headers.get("Link", "")
            if 'rel="next"' in link_header:
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        url_part = part.split(";")[0].strip()
                        if url_part.startswith("<") and url_part.endswith(">"):
                            return url_part[1:-1]
            return None

        # Navigate the path to find next URL
        current = data
        for key in next_url_path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current if isinstance(current, str) else None

    def _normalize_item(self, data: dict) -> NormalizedItem:
        """Normalize an API item using the field mapping."""
        # Extract fields using mapping
        item_id = self._get_mapped_value(data, "id", str(data.get("id", "")))
        title = self._get_mapped_value(data, "title", "Untitled")
        url = self._get_mapped_value(data, "url", "")
        date_str = self._get_mapped_value(data, "date", "")
        body = self._get_mapped_value(data, "body", "")
        author = self._get_mapped_value(data, "author", "")

        # Parse date
        date = datetime.now(UTC)
        if date_str:
            with contextlib.suppress(ValueError, TypeError):
                date = ensure_utc(date_parser.parse(date_str))

        # Clean body if it contains HTML
        if "<" in body and ">" in body:
            body = clean_html(body)

        return NormalizedItem(
            title=title,
            url=url,
            date=date,
            author=author,
            body=body,
            source_name=self.name,
            source_type=self.source_type,
            item_id=item_id or url,
        )

    def _get_mapped_value(self, data: dict, field: str, default: str = "") -> str:
        """Get a value from data using the field mapping."""
        path = self.mapping.get(field, field)

        current: Any = data
        for key in path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return str(current) if current is not None else default
