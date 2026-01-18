"""Base protocols and interfaces for adapters."""

from abc import ABC, abstractmethod
from typing import Any

from ..models import DigestMetadata, FetchResult, NormalizedItem, SourceConfig


class SourceAdapter(ABC):
    """Base class for source adapters."""

    source_type: str

    def __init__(self, config: SourceConfig) -> None:
        self.name = config.name
        self.config = config.config

    @abstractmethod
    async def fetch(self, rate_limit_delay: float = 1.0) -> FetchResult:
        """Fetch items from the source.

        Args:
            rate_limit_delay: Delay between paginated requests in seconds.

        Returns:
            FetchResult containing items and any errors.
        """

    def normalize(self, raw_item: dict[str, Any]) -> NormalizedItem:
        """Normalize a raw item to the common schema.

        Override this method in subclasses for custom normalization.
        """
        raise NotImplementedError


class OutputAdapter(ABC):
    """Base class for output adapters."""

    output_type: str

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    async def write(
        self,
        content: str,
        metadata: DigestMetadata,
        items: list[NormalizedItem],
    ) -> str | None:
        """Write the digest output.

        Args:
            content: The summarized content from the LLM.
            metadata: Metadata about the digest.
            items: The original items that were summarized.

        Returns:
            Path or identifier of the written output, or None if skipped.
        """


def get_source_adapter(config: SourceConfig) -> SourceAdapter:
    """Factory function to get the appropriate source adapter."""
    from .sources import (
        DiscourseAdapter,
        HyperKittyAdapter,
        RestAPIAdapter,
        RSSAdapter,
    )

    adapters: dict[str, type[SourceAdapter]] = {
        "rss": RSSAdapter,
        "discourse": DiscourseAdapter,
        "hyperkitty": HyperKittyAdapter,
        "rest_api": RestAPIAdapter,
    }

    adapter_class = adapters.get(config.type)
    if not adapter_class:
        raise ValueError(f"Unknown source type: {config.type}")

    return adapter_class(config)


def get_output_adapter(output_type: str, config: dict[str, Any]) -> OutputAdapter:
    """Factory function to get the appropriate output adapter."""
    from .outputs import EmailOutput, MarkdownOutput

    adapters: dict[str, type[OutputAdapter]] = {
        "markdown": MarkdownOutput,
        "email": EmailOutput,
    }

    adapter_class = adapters.get(output_type)
    if not adapter_class:
        raise ValueError(f"Unknown output type: {output_type}")

    return adapter_class(config)
