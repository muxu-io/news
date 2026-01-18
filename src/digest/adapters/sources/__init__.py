"""Source adapters for fetching content."""

from .discourse import DiscourseAdapter
from .hyperkitty import HyperKittyAdapter
from .rest_api import RestAPIAdapter
from .rss import RSSAdapter

__all__ = ["RSSAdapter", "DiscourseAdapter", "HyperKittyAdapter", "RestAPIAdapter"]
