"""Content filtering for digest items."""

import logging
from datetime import datetime

from .models import FilterConfig, NormalizedItem
from .state import StateManager
from .utils import get_cutoff_date

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filters content items based on configuration."""

    def __init__(
        self,
        config: FilterConfig,
        state_manager: StateManager | None = None,
        reference_date: datetime | None = None,
    ) -> None:
        self.config = config
        self.state_manager = state_manager
        self.reference_date = reference_date

    def filter_items(
        self,
        items: list[NormalizedItem],
        source_name: str | None = None,
    ) -> list[NormalizedItem]:
        """Apply all filters to items.

        Args:
            items: Items to filter.
            source_name: Optional source name for state-based filtering.

        Returns:
            Filtered list of items.
        """
        original_count = len(items)

        # Apply time/state filter
        items = self._filter_by_time_or_state(items, source_name)

        # Apply keyword filters
        items = self._filter_by_keywords(items)

        # Apply minimum content length
        items = self._filter_by_length(items)

        logger.debug(
            f"Filtered {original_count} items down to {len(items)} "
            f"(source: {source_name or 'all'})"
        )

        return items

    def _filter_by_time_or_state(
        self,
        items: list[NormalizedItem],
        source_name: str | None,
    ) -> list[NormalizedItem]:
        """Filter items by state (last seen date) or time window."""
        cutoff: datetime | None = None

        # When using a reference date, the cutoff is the reference date itself
        # (we want all items from reference_date up to now)
        if self.reference_date is not None:
            cutoff = self.reference_date
            return [item for item in items if item.date > cutoff]

        # Try to use state-based filtering
        if self.config.use_state and self.state_manager and source_name:
            cutoff = self.state_manager.get_last_seen_date(source_name)

        # Fall back to time window
        if cutoff is None:
            cutoff = get_cutoff_date(self.config.time_window)

        return [item for item in items if item.date > cutoff]

    def _filter_by_keywords(self, items: list[NormalizedItem]) -> list[NormalizedItem]:
        """Filter items by include/exclude keywords."""
        filtered = items

        # Include filter (if specified, item must match at least one)
        if self.config.keywords_include:
            filtered = [
                item
                for item in filtered
                if self._matches_keywords(item, self.config.keywords_include)
            ]

        # Exclude filter (remove items matching any exclude keyword)
        if self.config.keywords_exclude:
            filtered = [
                item
                for item in filtered
                if not self._matches_keywords(item, self.config.keywords_exclude)
            ]

        return filtered

    def _matches_keywords(self, item: NormalizedItem, keywords: list[str]) -> bool:
        """Check if an item matches any of the keywords."""
        text = f"{item.title} {item.body}".lower()
        return any(kw.lower() in text for kw in keywords)

    def _filter_by_length(self, items: list[NormalizedItem]) -> list[NormalizedItem]:
        """Filter items by minimum content length."""
        if self.config.min_content_length <= 0:
            return items

        return [
            item for item in items if len(item.body) >= self.config.min_content_length
        ]


def filter_all_items(
    items: list[NormalizedItem],
    config: FilterConfig,
    state_manager: StateManager | None = None,
) -> list[NormalizedItem]:
    """Convenience function to filter items without source-specific state filtering."""
    content_filter = ContentFilter(config, state_manager)
    return content_filter.filter_items(items)
