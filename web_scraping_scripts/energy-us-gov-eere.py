from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_paginated_pages

logger = setup_logger()
db_conn = get_db_connection()
source = "EnergyGov"

def parse_articles(soup):
    results = []
    articles = soup.find_all("article", class_="listing-item")

    for article in articles:
        try:
            # Extract title
            title_container = article.find(class_='listing-item__title title-sm')
            link_tag = title_container.find('a') if title_container else None
            title_span = link_tag.find('span') if link_tag else None
            if not title_span:
                logger.warning("Skipping article due to missing title span: %s", article)
                continue
            title = title_span.get_text(strip=True)

            # Extract link
            raw_link = link_tag.get('href', '') if link_tag else ''
            link = raw_link if raw_link.startswith("https://") else "https://www.energy.gov" + raw_link

            # Extract timestamp
            date_tag = article.find("time")
            if not date_tag:
                logger.warning("Skipping article due to missing date: %s", title)
                continue

            timestamp = datetime.strptime(date_tag.get_text(strip=True), "%B %d, %Y")
            
            results.append({
                "Title": title,
                "Date": timestamp,
                "Link": link,
                "Type": "news"
            })

        except Exception as e:
            logger.warning("Failed to parse article: %s", e)

    return pd.DataFrame(results)

def main():
    all_articles = []
    base_url = "https://www.energy.gov/eere/fuelcells/listings/hydrogen-and-fuel-cell-news?page={page}"

    all_articles = scrape_paginated_pages(base_url, range(3), parse_articles, fetch_page, logger)

    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles to update.")

main()