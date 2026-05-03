# Regulation, Policy & Industry Notification

A small Python service that scrapes hydrogen-related regulatory, policy, and industry news from configured sources, stores article metadata in a database, scores relevance with simple NLP, and sends daily email summaries.

## Features

- Scheduled or on-demand web scraping of multiple sources
- Stores article links and metadata in MySQL
- Extracts and normalizes article content per source
- Calculates relevance and mentions using spaCy NLP
- Updates database rows with classification, region, score, tags
- Sends daily HTML email summaries to configured recipients

## How it works (architecture)

- Web scraping scripts live in `web_scraping_scripts/` and are orchestrated by `web_scraping_controller.py`.
- Scraped metadata (link, title, source, published date) are saved to the MySQL table `regulation_policy_urls`.
- `main.py` loads recent rows, fetches article HTML, parses content per-source, runs NLP to determine region and relevance, updates DB, and sends an HTML email.

## Requirements

- Python 3.11.12 Docker image
- MySQL 8.0 Docker image

## Configuration

- Copy `app_conf.yaml.template` -> `app_conf.yaml` and set your database and email credentials.
- Example keys in `app_conf.yaml`:
	- `database`: host, port, user, password, db
	- `email`: `smtp_user`, `smtp_password`, `email_recipient`
	- `keywords`: `topic` and `keyword_list`

## Important environment variables

- `SKIP_SCRAPING=1` — skip running scrapers (useful for testing DB processing only)
- `NUM_DAYS_AGO=<n>` — process articles starting from n days ago (overrides default)
- `SKIP_REPROCESSING=1` — skip reprocessing rows that already have classifications
- `SKIP_EMAIL=1` — do not send the summary email (useful for dry runs)

## Run with Docker (recommended)

Build images:

```bash
docker build -t h2-db ./database
docker build -t h2-webscraper .
```

Create a user network and run the DB and app containers:

```bash
docker network create h2-web-scraping-net
docker run -d -p 3306:3306 --name db --network h2-web-scraping-net h2-db
docker run -it --rm --name app --network h2-web-scraping-net h2-webscraper
```

Debug / test run (skip heavy steps):

```bash
docker run -it --rm --name app --network h2-web-scraping-net \
	--env SKIP_SCRAPING=1 \
	--env NUM_DAYS_AGO=2 \
	--env SKIP_REPROCESSING=1 \
	--env SKIP_EMAIL=1 \
	h2-webscraper
```

## Files to inspect
- Scrapers: `web_scraping_scripts/`
- Controller: `web_scraping_controller.py`
- Processor: `main.py`
- DB schema: `database/create_table.sql`