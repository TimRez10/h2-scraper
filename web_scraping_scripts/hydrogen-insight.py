import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_request as fetch_page
from modules.scraper_helpers import scrape_category_pages

logger = setup_logger()
db_conn = get_db_connection()
source = "HydrogenInsights"

def parse_articles(soup, category):
    """
    Parse articles from BeautifulSoup object with category information.
    """
    results = []
    
    try:
        main = soup.find(class_="dn-collection-top")
        articles = main.find_all(class_="dn-link") if main else []
        
        for article in articles:
            try:
                # Title and Link
                title_tag = article.find('h3')
                link_tag = article.find('a')
                title = link_tag.get_text(strip=True)
                link = "https://www.hydrogeninsight.com" + link_tag['href']
                
                # Date
                #date_span = article.find('span', class_='published-at')
                #date_text = date_span.get_text(strip=True).replace('Published', '').strip()
                #timestamp = datetime.strptime(date_text, "%d %B %Y %H:%M %Z")
                
                results.append({
                    "Title": title,
                    "Date": datetime.now(), # placeholder
                    "Link": link,
                    "Type": category
                })
                
            except Exception as e:
                logger.warning("Failed to parse individual article from category %s: %s", category, e)
                continue
                
    except Exception as e:
        logger.error("Failed to parse articles from category %s: %s", category, e)
    
    return pd.DataFrame(results)

def main():
    categories = ["production", "transport", "industrial", "power", "innovation", "policy", "analysis"]
    base_url = "https://www.hydrogeninsight.com/{category}"
    
    all_articles = scrape_category_pages(base_url, categories, parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles found across all categories.")

main()
