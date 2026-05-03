import subprocess
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import spacy
import yaml
import logging
import logging.config
import sys
import os
from zoneinfo import ZoneInfo
from modules.db import get_db_connection
from modules.analysis import get_region, calculate_relevance_score
from modules.email import send_email, format_email_html
from modules.web_scraping import fetch_page_playwright, fetch_page_request
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")

# Load config and logging
app_conf_file = "app_conf.yaml"
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f)

log_conf_file = "log_conf.yaml"
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Setup DB and NLP
db_conn = get_db_connection()
cursor = db_conn.cursor()
nlp = spacy.load("en_core_web_trf")

# Use Pacific Time
pacific = ZoneInfo("America/Los_Angeles")

# Setup dates in Pacific Time
today = datetime.now(pacific).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday = today - timedelta(days=1)
includingWeekends = today - timedelta(days=3)
dayOfWeek = today.weekday()
if os.environ.get('NUM_DAYS_AGO'):
    custom_date = today - timedelta(days=int(os.environ.get('NUM_DAYS_AGO')))

if dayOfWeek in [5, 6]:
    logger.warning("Today is a weekend! Exiting main.py")
    sys.exit()

# Topic and keywords
topic = app_config["keywords"]["topic"]
keywords = app_config["keywords"]["keyword_list"]

if not os.environ.get('SKIP_SCRAPING'):
    # Run scraper
    logger.debug("Running web_scraping_controller.py")
    subprocess.run([sys.executable, 'web_scraping_controller.py'])
    logger.info(f"\n############ FINISHED RUNNING WEB SCRAPING SCRIPTS ############")


# Query articles from DB
query = """
    SELECT * FROM regulation_policy_urls
    WHERE date_published >= %s AND date_published < %s
"""

if os.environ.get('NUM_DAYS_AGO'):
    start_date = custom_date
else:
    start_date = yesterday if dayOfWeek > 0 else includingWeekends
logger.debug(f"Getting articles between {start_date} and {today}")
updates = pd.read_sql(query, db_conn, params=(start_date, today))
logger.info(f"Loaded {len(updates)} updates from DB")

# Process articles
for idx, row in updates.iterrows():
    url = row['link']

    if os.environ.get('SKIP_REPROCESSING'):
        # Skip article if already processed
        if row['classification']:
            logger.debug("Skipping update: %i/%i: %s", idx + 1, len(updates), url)
            continue 
    logger.debug("Processing update %i/%i: %s", idx + 1, len(updates), url)
        
    # Determine source-based content parsing
    title = row['title']
    source = row['source']
    classification = 'General News'
    region = 'Check'
    mainContent = ""
    news_type = row['news_type'] if row['news_type'] else ""
    
    if source in ["FuelCellsWorks", "HydrogenInsights", "EnergyGovNews"]:
        html = fetch_page_playwright(url, logger=logger)
    else:
        html = fetch_page_request(url, logger=logger)
    
    if not html:
        logger.error("Skipping update: %i/%i due to error: %s", idx + 1, len(updates), url)
        continue
    
    soup = BeautifulSoup(html, "html.parser")
    
    try:
        match source:
            case 'Federal':
                mainContent = soup.find_all(class_='cmp-text')
                region = 'Federal'
            case 'DrivingHydrogen':
                main = soup.find(class_="postarticles_left")
                title_element = soup.find("h1")
                mainContent = main.find_all('p')
                title = title_element.get_text()
                classification = 'Market News'
                # Convert list of elements to string for get_region
                mainText_for_region = ' '.join([p.get_text() for p in mainContent if p.get_text().strip()])
                region = get_region(title, mainText_for_region, nlp, logger=logger)
            case 'HydrogenInsights':
                main = soup.find(id="dn-content")
                mainContent = main.find_all(class_='dn-text')
                title_element = soup.find("h1")
                title = title_element.get_text()
                classification = 'Market News'
                # Convert list of elements to string for get_region
                mainText_for_region = ' '.join([elem.get_text() for elem in mainContent if elem.get_text().strip()])
                region = get_region(title, mainText_for_region, nlp, logger=logger)
            case 'CEC':
                mainContent = soup.main.find_all(class_='rich-text')
                region = 'CA'
            case 'ERA':
                mainContent = soup.main.find_all(class_="entry-content wp-block-post-content is-layout-constrained")
                region = 'AB'
            case 'CEC_Funding':
                mainContent = soup.main.find_all(class_="rich-text field field--name-field-purpose field--type-text-long field--label-above")
                classification = "Funding Website"
                region = 'CA'
            case 'NRCan_Funding':
                header_elements = soup.main.find_all(class_='programDetailHeader')
                mainContent = header_elements[0].parent
                classification = "Funding Website"
                region = 'CAN'
            case 'FuelCellsWorks':
                content_element = soup.find(class_='col-span-12 md:col-span-8 main-article-section')
                mainContent = soup.main.find_all("p")
                title_element = soup.find("h1")
                title = title_element.get_text()
                # Convert list of elements to string for get_region
                mainText_for_region = ' '.join([elem.get_text() for elem in mainContent if elem.get_text().strip()])
                region = get_region(title, mainText_for_region, nlp, logger=logger)
                classification = 'Market News'
                #logger.debug(mainText_for_region)
                news_type = soup.find(class_='text-primary-600 uppercase hover:underline underline-offset-2').get_text().lower()
            case 'HydrogenFuelNews':
                content_element = soup.find(class_='single-entry-summary')
                title_element = soup.find(class_='single-title')
                mainContent = content_element.find_all("p")
                title = title_element.get_text()
                classification = 'Market News'
                # Convert list of paragraphs to string for get_region
                mainText_for_region = ' '.join([p.get_text() for p in mainContent if p.get_text().strip()])
                region = get_region(title, mainText_for_region, nlp, logger=logger)
            case 'EnergyGov':
                content_element = soup.find(class_="block block-layout-builder block-inline-blockbasic")
                mainContent = content_element
                region = 'US'
            case 'EnergyGovNews':
                content_element = soup.find(id="block-main-page-content")
                mainContent = content_element
                region = 'US'
            case _:
                logger.error(f"Could not match source \"{source}\" for the link: {url}")
                continue
    except Exception as e:
        logger.error("Parsing failed for %s: %s", url, e)
        continue

    try:
        # Handle different types of mainContent
        if isinstance(mainContent, list):
            # Join all text from all elements in the list
            logger.debug(f"Found {len(mainContent)} paragraphs.")
            mainText = ' '.join([
                elem.get_text() if hasattr(elem, 'get_text') else str(elem) 
                for elem in mainContent 
                if elem and (hasattr(elem, 'get_text') and elem.get_text().strip() or str(elem).strip())
            ])
        elif hasattr(mainContent, 'get_text'):
            mainText = mainContent.get_text()
        elif isinstance(mainContent, str):
            mainText = mainContent
        else:
            mainText = str(mainContent)
        
        keywords_found, relevance, hydrogen_mentioned = calculate_relevance_score(mainText, topic, keywords, logger=logger)
        relevance_score = int(round((relevance / len(keywords)) * 100))
        if relevance_score > 100:
            relevance_score = 100
        if hydrogen_mentioned > 100:
            hydrogen_mentioned = 100
        keywords_str = ", ".join(keywords_found)
        keywords_str = keywords_str[:150] if len(keywords_str) <= 150 else keywords_str[:147] + "..."
        
    except Exception as e:
        logger.warning("Failed NLP for %s: %s", url, e)
        continue

    try:
        # Update rows in database
        cursor.execute("""
            UPDATE regulation_policy_urls
            SET title=%s, classification=%s, region=%s, rel_score=%s, h2_mentioned=%s, tags=%s, news_type=%s
            WHERE link=%s
        """, (
            title,
            classification,
            region,
            relevance_score,
            hydrogen_mentioned,
            keywords_str,
            news_type,
            url,
        ))
        db_conn.commit()
        logger.debug("Updated database row: classification=%s, region=%s, rel_score=%s, h2_mentioned=%s, news_type=%s"%(
                        classification,region,relevance_score,hydrogen_mentioned,news_type
        ))
    except Exception as e:
        logger.error("DB update failed for %s: %s", url, e)
        continue

# Send email with HTML table
logger.info(f"\n############ SENDING EMAIL NOTIFICATION ############")
if os.environ.get('SKIP_EMAIL'):
    logger.info(f"Skipping sending email. Exiting main.py")
    exit()
articles_to_send = pd.read_sql(query, db_conn, params=(start_date, today))

try:
    articles_to_send.sort_values(by=['h2_mentioned', 'rel_score'], ascending=False, inplace=True)

    msg_html = format_email_html(articles_to_send)

    # file_path = today.strftime('%Y-%m-%d') + ".html"
    # with open(file_path, "w") as f:
    #     f.write(html_table)

    send_email(
        subject=f"Daily Industry, Policy and Regulation News Updates - {today.strftime('%Y-%m-%d')}",
        sender=app_config["email"]["smtp_user"],
        recipient=app_config["email"]["email_recipient"],
        msg_string='Hello,\nPlease find attached today\'s article list.\nBest,\nYour automated system',
        msg_html=msg_html,
        #attachment_file_paths=[file_path, "./app.log"],
        attachment_file_paths=["./app.log"],
        smtp_username=app_config["email"]["smtp_user"],
        smtp_password=app_config["email"]["smtp_password"],
        logger=logger
    )
except Exception as e:
    logger.error("Failed to generate or send summary email: %s", e)

cursor.close()
db_conn.close()
