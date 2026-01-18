"""LLM summarization for digest content."""

import logging
import os
from typing import Any

from .models import NormalizedItem, SourceError, SummarizerConfig
from .utils import format_date_for_display, truncate_text

logger = logging.getLogger(__name__)


class SummarizerError(Exception):
    """Fatal error during summarization."""


class Summarizer:
    """LLM-based content summarizer."""

    def __init__(self, config: SummarizerConfig) -> None:
        self.config = config
        self.provider = config.provider.lower()
        self._client: Any = None

    async def summarize(
        self,
        items: list[NormalizedItem],
        errors: list[SourceError],
        time_window: str,
    ) -> str:
        """Summarize the content items using the configured LLM.

        Args:
            items: Normalized items to summarize.
            errors: Source errors to include in the digest.
            time_window: Time window string for the prompt.

        Returns:
            Markdown-formatted summary.

        Raises:
            SummarizerError: If summarization fails (fatal).
        """
        if not items:
            return self._generate_empty_digest(errors)

        # Build the content for the prompt
        content = self._build_content(items)
        errors_section = self._build_errors_section(errors)

        # Format the prompt
        prompt = self.config.prompt.format(
            time_window=time_window,
            content=content,
            errors_section=errors_section,
        )

        try:
            if self.provider == "anthropic":
                return await self._summarize_anthropic(prompt)
            elif self.provider == "openai":
                return await self._summarize_openai(prompt)
            elif self.provider == "gemini" or self.provider == "google":
                return await self._summarize_gemini(prompt)
            elif self.provider == "ollama":
                return await self._summarize_ollama(prompt)
            else:
                raise SummarizerError(f"Unknown LLM provider: {self.provider}")
        except SummarizerError:
            raise
        except Exception as e:
            raise SummarizerError(f"Summarization failed: {e}") from e

    def _build_content(self, items: list[NormalizedItem]) -> str:
        """Build the content string for the prompt."""
        parts = []

        # Group items by source
        by_source: dict[str, list[NormalizedItem]] = {}
        for item in items:
            if item.source_name not in by_source:
                by_source[item.source_name] = []
            by_source[item.source_name].append(item)

        for source_name, source_items in by_source.items():
            parts.append(f"\n### Source: {source_name}\n")

            for item in source_items:
                date_str = format_date_for_display(item.date)
                body = truncate_text(item.body, max_length=2000)

                parts.append(f"**{item.title}**")
                parts.append(f"- URL: {item.url}")
                parts.append(f"- Date: {date_str}")
                if item.author:
                    parts.append(f"- Author: {item.author}")
                parts.append(f"- Content: {body}")
                parts.append("")

        return "\n".join(parts)

    def _build_errors_section(self, errors: list[SourceError]) -> str:
        """Build the errors section for the prompt."""
        if not errors:
            return ""

        lines = [
            "\nNote: The following sources could not be fetched. "
            "Please mention these in the Source Errors section of the digest:\n"
        ]

        for error in errors:
            lines.append(f"- {error.source_name}: {error.error}")

        return "\n".join(lines)

    def _generate_empty_digest(self, errors: list[SourceError]) -> str:
        """Generate a digest when there are no items."""
        parts = ["## No New Content\n"]
        parts.append("No new content was found in the configured time window.\n")

        if errors:
            parts.append("\n## Source Errors\n")
            parts.append("The following sources could not be fetched:\n")
            for error in errors:
                parts.append(f"- **{error.source_name}**: {error.error}")

        return "\n".join(parts)

    async def _summarize_anthropic(self, prompt: str) -> str:
        """Summarize using Anthropic's Claude API."""
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise SummarizerError("ANTHROPIC_API_KEY environment variable not set")

        client = anthropic.AsyncAnthropic(api_key=api_key)

        message = await client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        if not message.content:
            raise SummarizerError("Empty response from Anthropic API")

        return message.content[0].text

    async def _summarize_openai(self, prompt: str) -> str:
        """Summarize using OpenAI's API."""
        import openai

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SummarizerError("OPENAI_API_KEY environment variable not set")

        client = openai.AsyncOpenAI(api_key=api_key)

        response = await client.chat.completions.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        if not response.choices:
            raise SummarizerError("Empty response from OpenAI API")

        content = response.choices[0].message.content
        if not content:
            raise SummarizerError("Empty content in OpenAI response")

        return content

    async def _summarize_gemini(self, prompt: str) -> str:
        """Summarize using Google's Gemini API."""
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise SummarizerError(
                "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set"
            )

        client = genai.Client(api_key=api_key)

        response = await client.aio.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=self.config.max_tokens,
            ),
        )

        if not response.text:
            raise SummarizerError("Empty response from Gemini API")

        return response.text

    async def _summarize_ollama(self, prompt: str) -> str:
        """Summarize using Ollama's local API."""
        import httpx

        base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        if "response" not in data:
            raise SummarizerError("Invalid response from Ollama API")

        return data["response"]
