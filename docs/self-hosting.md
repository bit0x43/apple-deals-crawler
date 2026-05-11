# Self-Hosting

Run apple-deals-crawler as a continuous service using Docker and GitHub Actions.

## Docker Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
- [docker-compose](https://docs.docker.com/compose/)

### Usage

```bash
# Start the crawler (reads .env file)
docker-compose up

# Run in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f
```

The Docker image includes Playwright Chromium with all system dependencies -- no manual Playwright installation needed.

## GitHub Actions

The project includes a pre-configured GitHub Actions workflow for daily crawling.

### Configure Secrets

Go to your repository **Settings > Secrets and variables > Actions** and add:

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (optional, for production) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional, for alerts) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (optional, for alerts) |

The workflow runs daily at 8:00 AM UTC and can be triggered manually via `workflow_dispatch`.

## Neon PostgreSQL Setup

1. Create a free [Neon](https://neon.tech) account
2. Create a project and copy the connection string
3. Set it as `DATABASE_URL` in your GitHub repository secrets

!!! tip "Neon auto-suspend"
    Neon suspends idle databases, making it cost-free for daily cron workloads.

## Verifying the Setup

- Check the **Actions** tab in your GitHub repository to confirm daily crawl runs
- If configured, check your Telegram for price drop alerts after each crawl
