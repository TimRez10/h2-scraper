from datetime import datetime
import pandas as pd
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_paginated_pages

logger = setup_logger()
db_conn = get_db_connection()
source = "HydrogenFuelNews"

def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    articles = soup.body.find_all("article")
    
    if not articles:
        logger.warning("No articles found in HTML")
        return pd.DataFrame()
    
    for article in articles:
        try:
            title_tag = article.find(class_='entry-title')
            link_tag = title_tag.a if title_tag else None
            date_tag = article.find(class_='posted-date')
            
            if not (title_tag and link_tag and date_tag and date_tag.string):
                raise ValueError("Missing title, link, or date")
            
            title = title_tag.a.string.strip()
            link = link_tag.attrs.get('href')
            timestamp = datetime.strptime(date_tag.string.strip(), '%B %d, %Y')
            
            results.append({
                "Title": title,
                "Date": timestamp,
                "Link": link
            })
            
        except Exception as e:
            logger.warning("Skipping article due to error: %s", e)
    
    return pd.DataFrame(results)

def main():
    base_url = "https://www.hydrogenfuelnews.com/featured-news/page/{page}/"
    
    all_articles = scrape_paginated_pages(base_url, range(3),parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles found.")

main()