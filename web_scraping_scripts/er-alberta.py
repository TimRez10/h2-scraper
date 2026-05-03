import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_single_page

logger = setup_logger()
db_conn = get_db_connection()
source = "ERA"

def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    containers = soup.find_all(
        "div",
        class_=lambda x: x and "wp-block-group" in x and "alignwide" in x and "has-blue-grey-background-color" in x
    )
    
    for article in containers:
        try:
            # Extract title
            title_tag = article.find("h2")
            title = title_tag.get_text(strip=True) if title_tag else None
            
            # Extract timestamp - handle the full datetime string properly
            time_tag = article.find("time")
            timestamp = None
            if time_tag and time_tag.get('datetime'):
                try:
                    # Handle the full datetime format: 2025-07-02T17:35:26-06:00
                    datetime_str = time_tag['datetime']
                    # Extract just the date part (first 10 characters)
                    date_part = datetime_str[:10]
                    timestamp = datetime.strptime(date_part, '%Y-%m-%d')
                except ValueError as ve:
                    logger.warning(f"Failed to parse datetime: {datetime_str}, error: {ve}")
            
            # Extract link
            link_tag = article.find("a", class_="wp-block-post-excerpt__more-link")
            link = link_tag.get('href') if link_tag else None
            
            if title and timestamp and link:
                results.append({
                    "Title": title,
                    "Date": timestamp,
                    "Link": link,
                    "Type": "news"
                })
            else:
                logger.warning(f"Skipping article due to missing data. Title: {title}, Date: {timestamp}, Link: {link}")
                
        except Exception as e:
            logger.warning("Failed to parse article: %s", e)
    
    return pd.DataFrame(results)

def main():
    logger.info("Starting ERA Alberta scraping...")

    url = "https://www.eralberta.ca/category/media-releases/"
    all_articles = scrape_single_page(url, parse_articles, fetch_page, logger)

    if all_articles:
        # Combine all DataFrames (in this case, just one)
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles to update.")

main()