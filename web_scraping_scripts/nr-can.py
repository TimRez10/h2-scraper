from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_single_page

logger = setup_logger()
db_conn = get_db_connection()
source = "NRCan_Funding"

# def parse_article_date(article_url):
#     try:
#         response = requests.get(article_url)
#         if response.status_code > 399:
#             logger.warning("Failed to fetch article URL %s, status %d", article_url, response.status_code)
#             return None
#         soup = BeautifulSoup(response.content, "html.parser")
#         date_text = soup.main.find(class_='mrgn-tp-md').get_text().splitlines()[1].split('\t')[-1]
#         return datetime.strptime(date_text, '%d-%m-%Y')
#     except Exception as e:
#         logger.warning("Failed to parse date for %s: %s", article_url, e)
#         logger.info("Using placeholder date: 01-01-1970")
#         return datetime.strptime("01-01-1970", '%d-%m-%Y')

# This website does not list articles dates on the main page.
# To save time, I will just set the date to current time.
def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    
    try:
        article_headers = soup.main.find_all('h4') if soup.main else []
        
        if not article_headers:
            logger.warning("No articles found in HTML")
            return pd.DataFrame()
        
        for h4 in article_headers:
            try:
                title_tag = h4.find('a')
                if not title_tag or not title_tag.string:
                    continue
                
                title = title_tag.string.strip()
                link = 'https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/policy_e/' + title_tag.attrs.get('href', '')
                #date = parse_article_date(link)
                date = datetime.now()
                
                results.append({
                    "Title": title,
                    "Date": date,
                    "Link": link
                })
                    
            except Exception as e:
                logger.warning("Failed to parse individual article: %s", e)
                continue
                
    except Exception as e:
        logger.error("Failed to parse articles from page: %s", e)
    
    return pd.DataFrame(results)

def main():
    base_url = "https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/policy_e/results.cfm?searchType=default§oranditems=all%7C0&max=50&categoryID=all®ionalDeliveryId=all&programTypes=4&keywords=&pageId=1"
    
    all_articles = scrape_single_page(base_url, parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles to save.")

main()