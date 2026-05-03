import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_single_page

logger = setup_logger()
db_conn = get_db_connection()
source = "DrivingHydrogen"

def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    
    try:
        main = soup.find(id="main")
        if not main:
            logger.error("No <main> element with id='main' found")
            return pd.DataFrame()

        articles = main.find_all(class_='article_preview_details')

        for article in articles:
            try:
                title_tag = article.h3.a
                title = title_tag.get_text(strip=True)
                link = title_tag['href']

                # Extract date from URL path: e.g., /2025/06/12/...
                date_parts = link.split('/')[3:6]  # skip leading empty '' from split
                date_str = '-'.join(date_parts)
                timestamp = datetime.strptime(date_str, '%Y-%m-%d')

                results.append({
                    "Title": title,
                    "Date": timestamp,
                    "Link": link
                })
                
            except Exception as e:
                logger.warning("Skipping article due to error: %s", e)
                continue
                
    except Exception as e:
        logger.error("Failed to parse articles from page: %s", e)

    return pd.DataFrame(results)

def main():
    url = "https://drivinghydrogen.com/"
    
    all_articles = scrape_single_page(url, parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFramesc
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles found.")

main()
