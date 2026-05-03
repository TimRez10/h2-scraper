from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_category_pages

logger = setup_logger()
db_conn = get_db_connection()
source = "Federal"

def parse_articles(soup, department_code):
    results = []
    articles = soup.main.find_all('article')

    for article in articles:
        try:
            title = str(article.a.string).strip()
            link = article.a['href'].strip()
            if not link.startswith("http"):
                link = "https://www.canada.ca" + link

            timestamp_str = article.find('time').string.strip()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')
            
            results.append({
                "Title": title,
                "Date": timestamp,
                "Link": link,
                "Type": department_code
            })
            
        except Exception as e:
            logger.warning("Failed to parse individual article from category %s: %s", department_code, e)
            continue
    
    return pd.DataFrame(results)

def main():
    department_codes = [
        'atlanticcanadaopportunities','canadainfrastructurebank', 
        'departmentfinance','departmentoftheenvironment', 
        'indigenousservicescanada','officeinfrastructure', 
        'departmentofindustry','nationalresearchcouncil', 
        'naturalresourcescanada','sciencesengineeringresearch', 
        'nationalenergyboard','pacificeconomicdevelopment', 
        'prairieseconomicdevelopment','departmentoftransport', 
        'westerneconomicdiversification'
    ]
    base_url = "https://www.canada.ca/en/news/advanced-news-search/news-results.html?idx=0&dprtmnt={category}"
   
    all_articles = scrape_category_pages(base_url, department_codes, parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles found across all categories.")


main()