# Helper funcitons for the web scraping scripts

import logging
import logging.config
import pandas as pd
import yaml
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import requests

import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")

def setup_logger(log_conf_file="log_conf.yaml", logger_name="basicLogger"):
    with open(log_conf_file, 'r') as f:
        log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)
    return logging.getLogger(logger_name)


def fetch_page_request(url, headers=None, logger=None):
    # Fetch html using the requests module
    try:
        response = requests.get(url, headers=headers)
        if response.status_code > 399:
            logger.error("Status code %i when requesting URL: %s", response.status_code, url)
            return None
        return response.content
    except Exception as e:
        logger.error("Error fetching page with requests module: %s", str(e))
        return None

def fetch_page_playwright(url, logger=None): 
    # Fetch html using the playwright module
    try:
        with sync_playwright() as p:
            if logger:
                logger.info("Launching Playwright browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
            if logger:
                logger.info("Fetched page content.")
            return html
    except Exception as e:
        logger.error("Error fetching page with Playwright: %s", str(e))
        return None


def save_to_mysql(df, source, db_conn, logger=None):
    cursor = db_conn.cursor()
    insert_query = """
        INSERT IGNORE INTO regulation_policy_urls
        (title, link, news_type, source, date_published)
        VALUES (%s, %s, %s, %s, %s)
    """
    inserted = 0

    for _, row in df.iterrows():
        # Normalize column keys just in case
        row_dict = {k.lower(): v for k, v in row.to_dict().items()}

        title = row_dict.get("title", "")
        link = row_dict.get("link")
        news_type = row_dict.get("type", "")
        date = row_dict.get("date")

        if pd.isna(link) or pd.isna(date):
            if logger:
                logger.debug(f"Skipping row due to missing link or date: {row_dict}")
            continue

        try:
            date_published = pd.to_datetime(date)
            if date_published < pd.Timestamp("2024-01-01"):
                continue
            cursor.execute(insert_query, (
                title,
                link,
                news_type,
                source,
                date_published.strftime('%Y-%m-%d %H:%M:%S')
            ))
            inserted += 1
        except Exception as e:
            if logger:
                logger.warning(f"Failed to insert row {row_dict}: {e}")
    
    db_conn.commit()
    cursor.close()

    if logger:
        logger.info(f"Attempted to insert {inserted} records into MySQL for source '{source}' (ignoring duplicate links)")