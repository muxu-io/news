"""Utility functions for the digest system."""

import asyncio
import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


def parse_time_window(window: str) -> timedelta:
    """Parse a time window string like '24h' or '7d' into a timedelta."""
    match = re.match(r"^(\d+)([hdwm])$", window.lower())
    if not match:
        raise ValueError(f"Invalid time window format: {window}")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    elif unit == "m":
        return timedelta(days=value * 30)  # Approximate

    raise ValueError(f"Unknown time unit: {unit}")


def get_cutoff_date(
    time_window: str, reference_date: datetime | None = None
) -> datetime:
    """Get the cutoff date based on a time window string.

    Args:
        time_window: Time window string like '24h' or '7d'.
        reference_date: Reference date to calculate from (defaults to now).

    Returns:
        The cutoff datetime.
    """
    delta = parse_time_window(time_window)
    ref = reference_date if reference_date else datetime.now(UTC)
    return ref - delta


async def rate_limited_request(
    client: httpx.AsyncClient,
    url: str,
    delay: float = 1.0,
    **kwargs,
) -> httpx.Response:
    """Make an HTTP GET request with rate limiting."""
    await asyncio.sleep(delay)
    return await client.get(url, **kwargs)


def truncate_text(text: str, max_length: int = 5000) -> str:
    """Truncate text to a maximum length, preserving word boundaries."""
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    # Find the last space to avoid cutting in the middle of a word
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]

    return truncated + "..."


def clean_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    import html as html_module

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", html)
    # Decode HTML entities
    text = html_module.unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_date_for_display(dt: datetime) -> str:
    """Format a datetime for display in digests."""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def create_http_client(timeout: float = 30.0) -> httpx.AsyncClient:
    """Create a pre-configured HTTP client for fetching feeds."""
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "DigestBot/1.0"},
    )


def extract_feed_date(entry: dict[str, Any]) -> datetime:
    """Extract and parse the date from a feedparser entry.

    Tries parsed time tuples first, then string fields, falls back to now.
    """
    # Try various parsed date fields
    for field in ["published_parsed", "updated_parsed", "created_parsed"]:
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=UTC)
            except (TypeError, ValueError):
                continue

    # Try string fields
    for field in ["published", "updated", "created"]:
        date_str = entry.get(field)
        if date_str:
            try:
                return ensure_utc(parsedate_to_datetime(date_str))
            except (TypeError, ValueError):
                continue

    return datetime.now(UTC)


def normalize_feed_entry(
    entry: dict[str, Any],
    source_name: str,
    source_type: str,
):
    """Normalize a feedparser entry to NormalizedItem.

    Works with RSS, Atom, Discourse, and HyperKitty feeds.
    """
    from .models import NormalizedItem

    # Extract URL
    url = entry.get("link", "")
    if not url and entry.get("links"):
        url = entry["links"][0].get("href", "")

    # Extract date
    date = extract_feed_date(entry)

    # Extract body from content, summary, or description
    body = ""
    if entry.get("content"):
        body = entry["content"][0].get("value", "")
    elif entry.get("summary"):
        body = entry["summary"]
    elif entry.get("description"):
        body = entry["description"]

    body = clean_html(body)

    # Extract author
    author = entry.get("author", "")
    if not author and entry.get("authors"):
        author = entry["authors"][0].get("name", "")

    return NormalizedItem(
        title=entry.get("title", "Untitled"),
        url=url,
        date=ensure_utc(date),
        author=author,
        body=body,
        source_name=source_name,
        source_type=source_type,
        item_id=entry.get("id", url),
    )
