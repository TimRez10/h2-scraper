import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_playwright as fetch_page
from modules.scraper_helpers import scrape_single_page

logger = setup_logger()
db_conn = get_db_connection()
source = "FuelCellsWorks"

def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    
    try:
        main = soup.find("main")

        if not main:
            logger.error("No <main> element found in the HTML")
            return pd.DataFrame()

        articles = main.find_all("a", href=True, attrs={"data-sentry-component": "MainNewsCard"})

        for a in articles:
            try:
                # Build link
                relative_link = a.get("href")
                link = f"https://fuelcellsworks.com{relative_link}"

                # Title
                title_tag = a.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else None
                if not title:
                    raise ValueError("Missing title")

                # Date from URL
                date_parts = relative_link.strip("/").split("/")[:3]  # e.g. ['2025', '06', '27']
                date_str = "-".join(date_parts)
                timestamp = datetime.strptime(date_str, "%Y-%m-%d")

                results.append({
                    "Title": title,
                    "Date": timestamp,
                    "Link": link,
                    "Type": "General News"
                })
                
            except Exception as e:
                logger.warning("Skipping article due to error: %s", e)
                continue
                
    except Exception as e:
        logger.error("Failed to parse articles from page: %s", e)

    return pd.DataFrame(results)

def main():
    url = "https://fuelcellsworks.com/"
    
    all_articles = scrape_single_page(url, parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles found.")

main()