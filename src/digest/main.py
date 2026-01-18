"""CLI entry point for the digest system."""

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime, time
from pathlib import Path

from .adapters.base import get_output_adapter, get_source_adapter
from .config import ConfigError, load_config
from .filters import ContentFilter
from .models import DigestMetadata, FetchResult, NormalizedItem, SourceError
from .state import StateManager
from .summarizer import Summarizer, SummarizerError

logger = logging.getLogger(__name__)


async def fetch_all_sources(
    config,
    state_manager: StateManager,
    content_filter: ContentFilter,
) -> tuple[list[NormalizedItem], list[SourceError]]:
    """Fetch and filter items from all configured sources."""
    all_items: list[NormalizedItem] = []
    all_errors: list[SourceError] = []

    for source_config in config.sources:
        logger.info(f"Fetching source: {source_config.name} ({source_config.type})")

        try:
            adapter = get_source_adapter(source_config)
            result: FetchResult = await adapter.fetch(
                rate_limit_delay=config.rate_limit.delay_between_requests
            )

            if result.error:
                logger.warning(f"Source error: {result.error.error}")
                all_errors.append(result.error)

            if result.items:
                # Filter items for this source
                filtered = content_filter.filter_items(
                    result.items, source_name=source_config.name
                )
                all_items.extend(filtered)

                # Update state with the newest item
                if filtered:
                    newest = max(filtered, key=lambda x: x.date)
                    state_manager.update_source(
                        source_name=source_config.name,
                        last_seen_date=newest.date,
                        last_seen_id=newest.item_id or newest.url,
                    )

        except Exception as e:
            logger.error(f"Failed to fetch {source_config.name}: {e}")
            all_errors.append(
                SourceError(
                    source_name=source_config.name,
                    source_type=source_config.type,
                    error=str(e),
                )
            )

        # Delay between sources
        await asyncio.sleep(config.rate_limit.delay_between_sources)

    return all_items, all_errors


async def run_digest(
    config_path: Path,
    state_dir: Path,
    output_dir: Path,
    dry_run: bool = False,
    verbose: bool = False,
    target_date: datetime | None = None,
) -> int:
    """Run the digest generation process.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Load configuration
        logger.info(f"Loading config: {config_path}")
        config = load_config(config_path)

        # Initialize state manager
        state_manager = StateManager(state_dir)

        # Initialize content filter
        content_filter = ContentFilter(config.filters, state_manager, target_date)

        # Fetch from all sources
        logger.info("Fetching content from sources...")
        items, errors = await fetch_all_sources(config, state_manager, content_filter)

        logger.info(f"Fetched {len(items)} items from {len(config.sources)} sources")
        logger.info(f"Source errors: {len(errors)}")

        # Apply global deduplication
        seen_urls: set[str] = set()
        unique_items: list[NormalizedItem] = []
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)
        items = unique_items

        # Sort by date (newest first)
        items.sort(key=lambda x: x.date, reverse=True)

        # Summarize content
        logger.info("Summarizing content...")
        summarizer = Summarizer(config.summarizer)

        try:
            summary = await summarizer.summarize(
                items=items,
                errors=errors,
                time_window=config.filters.time_window,
            )
        except SummarizerError as e:
            logger.error(f"Summarization failed (fatal): {e}")
            return 1

        # Build metadata
        now = datetime.now(UTC)
        digest_date = target_date if target_date else now
        metadata = DigestMetadata(
            title=config.name,
            date=digest_date.strftime("%Y-%m-%d"),
            generated_at=now.isoformat(),
            config=config.slug,
            sources_fetched=len(config.sources) - len(errors),
            sources_failed=len(errors),
            items_processed=len(items),
            time_window=config.filters.time_window,
            errors=[{"source": e.source_name, "error": e.error} for e in errors],
        )

        if dry_run:
            logger.info("Dry run - not writing outputs")
            print("\n" + "=" * 60)
            print("DIGEST PREVIEW")
            print("=" * 60)
            print(f"Title: {metadata.title}")
            print(f"Date: {metadata.date}")
            print(f"Items: {metadata.items_processed}")
            print(f"Errors: {metadata.sources_failed}")
            print("=" * 60)
            print(summary)
            print("=" * 60)
            return 0

        # Write outputs
        logger.info("Writing outputs...")
        digest_file = None

        for output_config in config.outputs:
            # Override output path if output_dir is specified
            if output_config.type == "markdown" and output_dir:
                output_config.config["path"] = str(output_dir / "{date}.md")

            adapter = get_output_adapter(output_config.type, output_config.config)
            result = await adapter.write(summary, metadata, items)

            if result and output_config.type == "markdown":
                digest_file = result

        # Update state
        state_manager.record_run(
            success=True,
            items_processed=len(items),
            digest_file=digest_file,
        )
        state_manager.save()

        logger.info("Digest generation complete")
        return 0

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 2
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a content digest from configured sources."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        required=True,
        help="Path to the configuration YAML file",
    )
    parser.add_argument(
        "--state-dir",
        "-s",
        type=Path,
        default=None,
        help="Directory for state files (default: state/{slug})",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Directory for output files (default: digests/{slug})",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Fetch and summarize but don't write outputs",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        default=None,
        help="Target date for digest (YYYY-MM-DD). Fetches content from time_window before this date.",
    )

    args = parser.parse_args()

    # Parse target date if provided
    target_date = None
    if args.date:
        try:
            # Parse date and set to end of day in UTC
            parsed = datetime.strptime(args.date, "%Y-%m-%d")
            target_date = datetime.combine(parsed.date(), time(23, 59, 59), tzinfo=UTC)
        except ValueError:
            parser.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")

    # Set default directories based on config slug if not specified
    if args.state_dir is None:
        args.state_dir = Path("state")
    if args.output_dir is None:
        args.output_dir = Path("digests")

    exit_code = asyncio.run(
        run_digest(
            config_path=args.config,
            state_dir=args.state_dir,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            verbose=args.verbose,
            target_date=target_date,
        )
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
