# Digest

A configuration-driven content aggregator that fetches content from multiple sources, filters it, summarizes via LLM, and outputs to markdown files or email.

## Features

- **Multiple source types**: RSS, Discourse forums, HyperKitty mailing lists, REST APIs
- **Smart filtering**: Time-based, keyword include/exclude, deduplication, minimum content length
- **State tracking**: Avoids reprocessing items across runs
- **LLM summarization**: Supports Anthropic Claude, OpenAI, Google Gemini, and Ollama
- **Multiple outputs**: Markdown files with YAML frontmatter, email (plain text or HTML)
- **GitHub Action ready**: Runs on schedule, commits digests to git

## Installation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install poetry in the venv
pip install poetry

# Install dependencies
poetry install
```

## Usage

```bash
# Run a digest
poetry run digest --config config/image-based-linux.yaml

# Dry run (fetch & summarize, don't write outputs)
poetry run digest --config config/embedded-yocto.yaml --dry-run

# Verbose logging
poetry run digest --config config/image-based-linux.yaml --verbose
```

## Available Configs

| Config | Description |
|--------|-------------|
| `image-based-linux.yaml` | bootc, ostree, Fedora Atomic, Flatcar, Talos, Kairos |
| `embedded-yocto.yaml` | Yocto Project, Raspberry Pi, NXP i.MX, NVIDIA Jetson BSP layers |

## Configuration

Create a YAML config file in `config/`:

```yaml
meta:
  name: "My Digest"
  slug: "my-digest"
  description: "Daily digest of interesting content"

sources:
  # RSS Feed
  - name: "Blog"
    type: rss
    url: "https://example.org/feed.xml"

  # Discourse Forum
  - name: "Forum"
    type: discourse
    base_url: "https://forum.example.org"
    categories:
      - path: "category/subcategory"
        id: 123
    tags:
      - "relevant-tag"

  # Mailing List (HyperKitty/Mailman 3)
  - name: "Mailing List"
    type: hyperkitty
    base_url: "https://lists.example.org/archives/list"
    list_address: "list@lists.example.org"

  # REST API
  - name: "API"
    type: rest_api
    url: "https://api.example.org/items"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    mapping:
      title: "name"
      url: "html_url"
      date: "created_at"
      body: "description"

filters:
  time_window: "24h"
  use_state: true
  keywords:
    include: []
    exclude:
      - "unsubscribe"
      - "out of office"
  min_content_length: 50

rate_limit:
  delay_between_sources: 2
  delay_between_requests: 1

summarizer:
  provider: anthropic
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  prompt: |
    Summarize the following content...
    {content}

outputs:
  - type: markdown
    path: "digests/{slug}/{date}.md"
    frontmatter: true

  - type: email
    enabled: false
    format: plain
    to: "${EMAIL_TO}"
    subject: "[{name}] {date}"
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | If using Claude |
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI |
| `GEMINI_API_KEY` | Google Gemini API key | If using Gemini |
| `OLLAMA_HOST` | Ollama server URL | If using Ollama |
| `SMTP_HOST` | SMTP server hostname | If email enabled |
| `SMTP_PORT` | SMTP port (default: 587) | If email enabled |
| `SMTP_USER` | SMTP username | If email enabled |
| `SMTP_PASSWORD` | SMTP password | If email enabled |
| `EMAIL_FROM` | Sender email address | If email enabled |
| `EMAIL_TO` | Recipient email(s) | If email enabled |

## Running Manually

### Local

```bash
# Set required environment variables
export GEMINI_API_KEY="your-api-key"

# Run with a specific config
poetry run digest --config config/image-based-linux.yaml

# Dry run - fetches and summarizes but doesn't write files
poetry run digest --config config/embedded-yocto.yaml --dry-run

# Specify custom output and state directories
poetry run digest \
  --config config/image-based-linux.yaml \
  --state-dir state/image-based-linux \
  --output-dir digests/image-based-linux

# With verbose logging
poetry run digest --config config/embedded-yocto.yaml --verbose
```

### GitHub Action

The included workflow (`.github/workflows/digest.yaml`) runs daily at 07:00 UTC.

**Setup:**
1. Add required secrets in repository Settings > Secrets and variables > Actions
2. At minimum, add `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` depending on your config)
3. If email is enabled, add all SMTP secrets

**Manual trigger:**
1. Go to Actions > Daily Digest
2. Click "Run workflow"
3. Select a config (or "all" to run all configs)
4. Click "Run workflow"

## Project Structure

```
├── config/                 # Digest configurations
├── state/                  # State files (auto-generated)
├── digests/                # Output markdown files
└── src/digest/
    ├── main.py             # CLI entry point
    ├── config.py           # Config loading
    ├── state.py            # State persistence
    ├── models.py           # Data classes
    ├── filters.py          # Content filtering
    ├── summarizer.py       # LLM integration
    └── adapters/
        ├── sources/        # RSS, Discourse, HyperKitty, REST API
        └── outputs/        # Markdown, Email
```

## License

MIT
