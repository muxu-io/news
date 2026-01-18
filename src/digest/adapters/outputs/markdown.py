"""Markdown file output adapter."""

import logging
from pathlib import Path

import yaml

from ...models import DigestMetadata, NormalizedItem
from ..base import OutputAdapter

logger = logging.getLogger(__name__)


class MarkdownOutput(OutputAdapter):
    """Output adapter for markdown files with YAML frontmatter."""

    output_type = "markdown"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.path_template = config.get("path", "digests/{slug}/{date}.md")
        self.include_frontmatter = config.get("frontmatter", True)

    async def write(
        self,
        content: str,
        metadata: DigestMetadata,
        items: list[NormalizedItem],
    ) -> str | None:
        """Write the digest to a markdown file."""
        # Build the output path
        output_path = self._build_path(metadata)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build the file content
        file_content = self._build_content(content, metadata)

        # Write the file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        logger.info(f"Markdown output written to: {output_path}")
        return str(output_path)

    def _build_path(self, metadata: DigestMetadata) -> Path:
        """Build the output file path from the template."""
        path_str = self.path_template.format(
            slug=metadata.config,
            date=metadata.date,
            title=metadata.title,
        )
        return Path(path_str)

    def _build_content(self, content: str, metadata: DigestMetadata) -> str:
        """Build the complete file content with optional frontmatter."""
        parts = []

        if self.include_frontmatter:
            frontmatter = self._build_frontmatter(metadata)
            parts.append("---")
            parts.append(
                yaml.dump(
                    frontmatter, default_flow_style=False, allow_unicode=True
                ).strip()
            )
            parts.append("---")
            parts.append("")

        parts.append(content)

        # Add source errors section if there were errors
        if metadata.errors:
            parts.append("")
            parts.append("## Source Errors")
            parts.append("")
            parts.append("The following sources could not be fetched:")
            for error in metadata.errors:
                parts.append(f"- **{error['source']}**: {error['error']}")

        return "\n".join(parts)

    def _build_frontmatter(self, metadata: DigestMetadata) -> dict:
        """Build the YAML frontmatter dictionary."""
        frontmatter = {
            "title": metadata.title,
            "date": metadata.date,
            "generated_at": metadata.generated_at,
            "config": metadata.config,
            "sources_fetched": metadata.sources_fetched,
            "sources_failed": metadata.sources_failed,
            "items_processed": metadata.items_processed,
            "time_window": metadata.time_window,
        }

        if metadata.errors:
            frontmatter["errors"] = metadata.errors

        return frontmatter
