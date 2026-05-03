import pandas as pd
from bs4 import BeautifulSoup
from typing import Callable, List, Union

def scrape_single_page(url: str, parsing_function: Callable, fetch_page: Callable, 
                       logger) -> List[pd.DataFrame]:
    """
    Helper function for scraping a single webpage.
    """
    all_articles = []
    
    logger.info(f"Scraping single page: {url}")
    
    try:
        # Step 2: Fetch the page
        html = fetch_page(url, logger=logger)
        
        if not html:
            logger.warning(f"Failed to fetch page: {url}")
            return all_articles
        
        # Step 3: Create soup with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Step 4: Pass soup into parsing function
        # Step 5: Parsing function returns DataFrame
        df = parsing_function(soup)
        
        # Step 6: Add DataFrame to all_articles list
        if df is not None and not df.empty:
            all_articles.append(df)
            logger.info(f"Found {len(df)} articles")
        else:
            logger.info("No articles found")
            
    except Exception as e:
        logger.error(f"Error scraping single page {url}: {str(e)}")
    
    return all_articles


def scrape_paginated_pages(base_url: str, page_range: Union[int, range, List[int]], 
                          parsing_function: Callable, fetch_page: Callable, logger) -> List[pd.DataFrame]:
    """
    Helper function for scraping multiple pages with page numbers.
    """
    all_articles = []
    
    # Convert page_range to iterable if it's an integer
    if isinstance(page_range, int):
        pages_to_scrape = range(page_range)
    else:
        pages_to_scrape = page_range
    
    for page_num in pages_to_scrape:
        # Step 1: Define the URL
        url = base_url.format(page=page_num)
        logger.info(f"Scraping page {page_num}: {url}")
        
        try:
            # Step 2: Fetch the page
            html = fetch_page(url, logger=logger)
            
            if not html:
                logger.warning(f"Failed to fetch page {page_num}: {url}")
                continue
            
            # Step 3: Create soup with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Step 4/5: Pass soup into parsing function. Parsing function returns DataFrame
            df = parsing_function(soup)
            
            # Step 6: Add DataFrame to all_articles list
            if df is not None and not df.empty:
                all_articles.append(df)
                logger.debug(f"Page {page_num}: Found {len(df)} articles")
            else:
                logger.warning(f"No articles found on page {page_num}")
                
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {str(e)}")
            continue
    
    return all_articles


def scrape_infinite_pages(base_url: str, parsing_function: Callable, fetch_page: Callable, logger, 
                         start_page: int = 1, max_empty_pages: int = 3) -> List[pd.DataFrame]:
    """
    Helper function for scraping pages with infinite scrolling (keeps going until no more articles).
    """
    all_articles = []
    page = start_page
    consecutive_empty_pages = 0
    
    while True:
        # Step 1: Define the URL
        url = base_url.format(page=page)
        logger.info(f"Scraping page {page}: {url}")
        
        try:
            # Step 2: Fetch the page
            html = fetch_page(url, logger=logger)
            
            if not html:
                logger.warning(f"Failed to fetch page {page}: {url}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_empty_pages:
                    logger.info(f"Stopping after {consecutive_empty_pages} consecutive failed fetches")
                    break
                page += 1
                continue
            
            # Step 3: Create soup with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Step 4/5: Pass soup into parsing function. Parsing function returns DataFrame
            df = parsing_function(soup)
            
            # Step 6: Add DataFrame to all_articles list
            if df is not None and not df.empty:
                all_articles.append(df)
                logger.debug(f"Page {page}: Found {len(df)} articles")
                consecutive_empty_pages = 0
            else:
                consecutive_empty_pages += 1
                logger.warning(f"No articles found on page {page}")
                
                if consecutive_empty_pages >= max_empty_pages:
                    logger.info(f"Stopping after {consecutive_empty_pages} consecutive empty pages")
                    break
                    
        except Exception as e:
            logger.error(f"Error scraping page {page}: {str(e)}")
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= max_empty_pages:
                logger.info(f"Stopping after {consecutive_empty_pages} consecutive errors")
                break
        
        page += 1
    
    return all_articles


def scrape_category_pages(base_url: str, categories: List[str], parsing_function: Callable, 
                         fetch_page: Callable, logger) -> List[pd.DataFrame]:
    """
    Helper function for scraping multiple pages with different categories.
    """
    all_articles = []
    
    logger.info(f"Starting category scraping for {len(categories)} categories")
    
    for category in categories:
        # Step 1: Define the URL
        if "{category}" in base_url:
            url = base_url.format(category=category)
        else:
            url = base_url + category
        
        logger.info(f"Scraping category '{category}': {url}")
        
        try:
            # Step 2: Fetch the page
            html = fetch_page(url, logger=logger)
            
            if not html:
                logger.warning(f"Failed to fetch category '{category}': {url}")
                continue
            
            # Step 3: Create soup with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Step 4/5: Pass soup into parsing function. Parsing function returns DataFrame
            df = parsing_function(soup, category)
            
            # Step 6: Add DataFrame to all_articles list
            if df is not None and not df.empty:
                all_articles.append(df)
                logger.debug(f"Category '{category}': Found {len(df)} articles")
            else:
                logger.warning(f"No articles found for category '{category}'")
                
        except Exception as e:
            logger.error(f"Error scraping category '{category}': {str(e)}")
            continue
    
    return all_articles