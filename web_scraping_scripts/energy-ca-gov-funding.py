from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_infinite_pages

logger = setup_logger()
db_conn = get_db_connection()
source = "CEC_Funding"

def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    
    try:
        articles = soup.main.find_all(class_='col-12 position-relative')

        for article in articles:
            try:
                title = article.h3.get_text(strip=True)
                date_str = article.time.get_text(strip=True)
                timestamp = datetime.strptime(date_str, '%B %d, %Y')
                link = 'https://www.energy.ca.gov' + article.a['href']
                
                results.append({
                    "Title": title,
                    "Date": timestamp,
                    "Link": link,
                    "Type": "funding"
                })
                
            except Exception as e:
                logger.warning("Failed to parse article: %s", e)
                continue
                
    except Exception as e:
        logger.error("Failed to parse articles from page: %s", e)

    return pd.DataFrame(results)

def main():
    base_url = (
        "https://www.energy.ca.gov/funding-opportunities/solicitations"
        "?field_solicitation_status_target_id%5B32%5D=32"
        "&field_solicitation_type_target_id=All"
        "&field_division_1_target_id=All"
        "&page={page}"
    )
    
    # Use the helper function for infinite scrolling
    all_articles = scrape_infinite_pages(base_url, parse_articles, fetch_page, logger, start_page=0, max_empty_pages=1)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No articles found across all pages.")

main()