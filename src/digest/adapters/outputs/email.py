"""Email output adapter."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ...models import DigestMetadata, NormalizedItem
from ..base import OutputAdapter

logger = logging.getLogger(__name__)


class EmailConfigError(Exception):
    """Email configuration error."""


class EmailOutput(OutputAdapter):
    """Output adapter for sending digests via email."""

    output_type = "email"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        # Environment variable overrides config (useful for CI)
        env_enabled = os.environ.get("DIGEST_EMAIL_ENABLED", "").lower()
        if env_enabled in ("true", "1", "yes"):
            self.enabled = True
        elif env_enabled in ("false", "0", "no"):
            self.enabled = False
        else:
            self.enabled = config.get("enabled", True)
        self.format = config.get("format", "plain")
        self.to = config.get("to", "")
        self.subject_template = config.get(
            "subject", "[{name}] Digest ({time_window}) - {date}"
        )

        # Validate config if email is enabled
        if self.enabled:
            self._validate_config()

    def _validate_config(self) -> None:
        """Validate email configuration. Raises EmailConfigError if invalid."""
        missing = []

        if not self.to:
            missing.append("to (in config)")

        if not os.environ.get("SMTP_HOST"):
            missing.append("SMTP_HOST")
        if not os.environ.get("SMTP_USER"):
            missing.append("SMTP_USER")
        if not os.environ.get("SMTP_PASSWORD"):
            missing.append("SMTP_PASSWORD")
        if not os.environ.get("EMAIL_FROM"):
            missing.append("EMAIL_FROM")

        if missing:
            raise EmailConfigError(
                f"Email output is enabled but missing required settings: {', '.join(missing)}"
            )

    async def write(
        self,
        content: str,
        metadata: DigestMetadata,
        items: list[NormalizedItem],
    ) -> str | None:
        """Send the digest via email."""
        if not self.enabled:
            logger.debug("Email output is disabled")
            return None

        # Get SMTP configuration from environment
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        email_from = os.environ.get("EMAIL_FROM")

        # Build subject
        subject = self.subject_template.format(
            name=metadata.title,
            date=metadata.date,
            slug=metadata.config,
            time_window=metadata.time_window,
        )

        # Build message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = self.to

        if self.format == "html":
            # Convert markdown to simple HTML
            html_content = self._markdown_to_html(content, metadata)
            msg.attach(MIMEText(content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
        else:
            msg.attach(MIMEText(content, "plain", "utf-8"))

        # Send email
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(email_from, self.to.split(","), msg.as_string())

            logger.info(f"Email sent to: {self.to} with subject: {subject}")
            return f"email:{self.to}"

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return None

    def _markdown_to_html(self, content: str, metadata: DigestMetadata) -> str:
        """Convert markdown content to simple HTML."""

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{metadata.title} - {metadata.date}</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; ",
            "       max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }",
            "h1, h2, h3 { color: #333; }",
            "a { color: #0066cc; }",
            "ul { padding-left: 20px; }",
            "li { margin: 8px 0; }",
            ".error { color: #cc0000; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Simple markdown to HTML conversion
        lines = content.split("\n")
        in_list = False

        for line in lines:
            # Headers
            if line.startswith("### "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("# "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<h1>{line[2:]}</h1>")
            # List items
            elif line.startswith("- "):
                if not in_list:
                    html_parts.append("<ul>")
                    in_list = True
                item = self._convert_inline(line[2:])
                html_parts.append(f"<li>{item}</li>")
            # Empty line
            elif not line.strip():
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append("<br>")
            # Regular paragraph
            else:
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<p>{self._convert_inline(line)}</p>")

        if in_list:
            html_parts.append("</ul>")

        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    def _convert_inline(self, text: str) -> str:
        """Convert inline markdown elements to HTML."""
        import re

        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Links
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)

        return text
