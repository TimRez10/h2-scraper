import pandas as pd
from datetime import datetime
from modules.db import get_db_connection
from modules.web_scraping import setup_logger, save_to_mysql, fetch_page_playwright as fetch_page
from modules.scraper_helpers import scrape_paginated_pages

logger = setup_logger()
db_conn = get_db_connection()
source = "EnergyGovNews"

def parse_articles(soup):
    """
    Parse articles from BeautifulSoup object.
    """
    results = []
    
    try:
        main_list = soup.find(
            "ul",
            class_=lambda c: c and "MuiList-root MuiList-padding" in c
        )
        if not main_list:
            logger.error("Could not find main list container.")
            return pd.DataFrame(results)

        articles = main_list.find_all(
            "span",
            class_=lambda c: c and "MuiTypography-root MuiTypography-body1 MuiListItemText-primary" in c
        )

        for article in articles:
            try:
                link_tag = article.find("a")
                if not link_tag:
                    logger.warning("Skipping article due to missing link: %s", article)
                    continue

                title = link_tag.get_text(strip=True)
                link = "https://www.energy.gov" + link_tag["href"]

                date_tags = article.find_all("p")
                if len(date_tags) < 2:
                    logger.warning("Skipping article due to missing date: %s", article)
                    continue

                date_str = date_tags[1].get_text(strip=True)
                timestamp = datetime.strptime(date_str, "%B %d, %Y")

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
    base_url = "https://www.energy.gov/search?page={page}&sort_by=date&f%5B0%5D=content_type_rest%3Aarticle"
    
    # Use the helper function for paginated scraping
    all_articles = scrape_paginated_pages(base_url, range(3), parse_articles, fetch_page, logger)
    
    if all_articles:
        # Combine all DataFrames
        df = pd.concat(all_articles, ignore_index=True)
        save_to_mysql(df, source, db_conn, logger)
    else:
        logger.info("No new articles to update.")

main()