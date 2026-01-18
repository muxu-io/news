"""Output adapters for writing digests."""

from .email import EmailConfigError, EmailOutput
from .markdown import MarkdownOutput

__all__ = ["MarkdownOutput", "EmailOutput", "EmailConfigError"]
