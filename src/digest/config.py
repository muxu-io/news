"""Configuration loading and validation."""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from .models import (
    DigestConfig,
    FilterConfig,
    OutputConfig,
    RateLimitConfig,
    SourceConfig,
    SummarizerConfig,
)


class ConfigError(Exception):
    """Configuration error."""


def interpolate_env_vars(value: str, strict: bool = False) -> str:
    """Replace ${VAR} patterns with environment variable values.

    Args:
        value: String potentially containing ${VAR} patterns.
        strict: If True, raise error on missing vars. If False, keep pattern as-is.

    Returns:
        String with environment variables interpolated.
    """
    pattern = r"\$\{([^}]+)\}"

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            if strict:
                raise ConfigError(f"Environment variable '{var_name}' not set")
            # Keep the original pattern for lazy evaluation at runtime
            return match.group(0)
        return env_value

    return re.sub(pattern, replacer, value)


def interpolate_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively interpolate environment variables in a dictionary."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = interpolate_env_vars(value)
        elif isinstance(value, dict):
            result[key] = interpolate_dict(value)
        elif isinstance(value, list):
            result[key] = interpolate_list(value)
        else:
            result[key] = value
    return result


def interpolate_list(data: list[Any]) -> list[Any]:
    """Recursively interpolate environment variables in a list."""
    result = []
    for item in data:
        if isinstance(item, str):
            result.append(interpolate_env_vars(item))
        elif isinstance(item, dict):
            result.append(interpolate_dict(item))
        elif isinstance(item, list):
            result.append(interpolate_list(item))
        else:
            result.append(item)
    return result


def load_config(config_path: Path) -> DigestConfig:
    """Load and validate a digest configuration from a YAML file."""
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    if not raw_config:
        raise ConfigError("Config file is empty")

    # Interpolate environment variables
    config = interpolate_dict(raw_config)

    # Validate required sections
    if "meta" not in config:
        raise ConfigError("Missing 'meta' section in config")
    if "sources" not in config:
        raise ConfigError("Missing 'sources' section in config")
    if "summarizer" not in config:
        raise ConfigError("Missing 'summarizer' section in config")

    meta = config["meta"]
    if "name" not in meta:
        raise ConfigError("Missing 'meta.name' in config")
    if "slug" not in meta:
        raise ConfigError("Missing 'meta.slug' in config")

    # Parse sources
    sources = []
    for source_data in config["sources"]:
        if "name" not in source_data:
            raise ConfigError("Source missing 'name' field")
        if "type" not in source_data:
            raise ConfigError(f"Source '{source_data['name']}' missing 'type' field")

        source_type = source_data.pop("type")
        source_name = source_data.pop("name")
        sources.append(
            SourceConfig(name=source_name, type=source_type, config=source_data)
        )

    # Parse filters
    filters_data = config.get("filters", {})
    filters = FilterConfig(
        time_window=filters_data.get("time_window", "24h"),
        use_state=filters_data.get("use_state", True),
        keywords_include=filters_data.get("keywords", {}).get("include", []),
        keywords_exclude=filters_data.get("keywords", {}).get("exclude", []),
        min_content_length=filters_data.get("min_content_length", 50),
    )

    # Parse rate limit
    rate_limit_data = config.get("rate_limit", {})
    rate_limit = RateLimitConfig(
        delay_between_sources=rate_limit_data.get("delay_between_sources", 2.0),
        delay_between_requests=rate_limit_data.get("delay_between_requests", 1.0),
    )

    # Parse summarizer
    summarizer_data = config["summarizer"]
    if "provider" not in summarizer_data:
        raise ConfigError("Missing 'summarizer.provider' in config")
    if "model" not in summarizer_data:
        raise ConfigError("Missing 'summarizer.model' in config")

    # Load prompt from file or inline
    prompt = None
    if "prompt_file" in summarizer_data:
        prompt_path = config_path.parent / summarizer_data["prompt_file"]
        if not prompt_path.exists():
            raise ConfigError(f"Prompt file not found: {prompt_path}")
        prompt = prompt_path.read_text()
    elif "prompt" in summarizer_data:
        prompt = summarizer_data["prompt"]
    else:
        raise ConfigError(
            "Missing 'summarizer.prompt' or 'summarizer.prompt_file' in config"
        )

    summarizer = SummarizerConfig(
        provider=summarizer_data["provider"],
        model=summarizer_data["model"],
        max_tokens=summarizer_data.get("max_tokens", 4096),
        prompt=prompt,
    )

    # Parse outputs
    outputs = []
    for output_data in config.get("outputs", []):
        if "type" not in output_data:
            raise ConfigError("Output missing 'type' field")
        output_type = output_data.pop("type")
        outputs.append(OutputConfig(type=output_type, config=output_data))

    # Default to markdown output if none specified
    if not outputs:
        outputs.append(
            OutputConfig(
                type="markdown",
                config={"path": "digests/{slug}/{date}.md", "frontmatter": True},
            )
        )

    return DigestConfig(
        name=meta["name"],
        slug=meta["slug"],
        description=meta.get("description", ""),
        schedule=meta.get("schedule", ""),
        sources=sources,
        filters=filters,
        rate_limit=rate_limit,
        summarizer=summarizer,
        outputs=outputs,
    )
