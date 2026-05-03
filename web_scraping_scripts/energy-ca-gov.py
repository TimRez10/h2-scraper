import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_single_page

logger = setup_logger()
db_conn = get_db_connection()
source = "CEC"

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
                date_str = article.find(class_='abstract-description').get_text(strip=True)
                timestamp = datetime.strptime(date_str, '%B %d, %Y')
                link = 'https://www.energy.ca.gov' + article.a['href']
                
                results.append({
                    "Title": title,
                    "Date": timestamp,
                    "Link": link,
                    "Type": "news"
                })
                
            except Exception as e:
                logger.warning("Failed to parse individual article: %s", e)
                continue
                
    except Exception as e:
        logger.error("Failed to parse articles from page: %s", e)
    
    return pd.DataFrame(results)

def main():
    url = "https://www.energy.ca.gov/newsroom/news-releases?page=0"
    
    # Use the helper function
    all_articles = scrape_single_page(url, parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames (in this case, just one)
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles found.")

main()