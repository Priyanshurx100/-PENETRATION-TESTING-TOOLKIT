import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, urljoin
import random
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from urllib.robotparser import RobotFileParser
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of User-Agent strings for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
]

# Rate limiting and retry settings
RATE_LIMIT_DELAY = 1  # Delay between requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def check_robots_txt(url):
    """Check robots.txt and return a RobotFileParser object."""
    robots_url = urljoin(url, '/robots.txt')
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        logging.info(f"Robots.txt found and parsed for {url}")
    except Exception as e:
        logging.warning(f"Error parsing robots.txt for {url}: {e}")
    return rp

def fetch_page(url, retries=MAX_RETRIES):
    """Fetch a page with retries and exponential backoff."""
    headers = {'User-Agent': get_random_user_agent()}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None

def scrape_page(url, max_depth=1, current_depth=0, visited=set(), rp=None):
    """Scrape a page and extract links recursively."""
    if current_depth > max_depth or url in visited or (rp and not rp.can_fetch("*", url)):
        return []

    logging.info(f"Scraping {url} (depth {current_depth})")
    response = fetch_page(url)
    if not response:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    links = set()
    base_url = urlparse(url).netloc

    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href)
        parsed_url = urlparse(full_url)

        # Validate the URL
        if parsed_url.netloc == base_url and full_url not in visited:
            visited.add(full_url)
            links.add(full_url)
            if current_depth < max_depth:
                links.update(scrape_page(full_url, max_depth, current_depth + 1, visited, rp))

    return links

def save_links(links, format='console', output_file='scraped_links'):
    """Save links to the specified format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_file}_{timestamp}"

    if format == 'console':
        for link in links:
            print(link)
    elif format == 'csv':
        with open(f'{output_file}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for link in links:
                writer.writerow([link])
        logging.info(f"Links saved to {output_file}.csv")
    elif format == 'json':
        with open(f'{output_file}.json', 'w') as file:
            json.dump(list(links), file, indent=2)
        logging.info(f"Links saved to {output_file}.json")

def scrape_concurrently(url, max_depth, output_format, output_file):
    """Scrape a website concurrently using a thread pool."""
    rp = check_robots_txt(url)
    visited = set()
    all_links = set()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        initial_links = scrape_page(url, max_depth, 0, visited, rp)
        all_links.update(initial_links)

        for link in initial_links:
            futures.append(executor.submit(scrape_page, link, max_depth, 1, visited, rp))

        for future in as_completed(futures):
            try:
                all_links.update(future.result())
            except Exception as e:
                logging.error(f"Error in future: {e}")

    save_links(all_links, output_format, output_file)
    logging.info(f"Total links found: {len(all_links)}")

if __name__ == "__main__":
    url = input("Enter target URL: ")
    max_depth = int(input("Enter maximum depth for scraping (default 1): ") or "1")
    output_format = input("Enter output format (console/csv/json, default console): ").lower() or "console"
    output_file = input("Enter output file name (default scraped_links): ") or "scraped_links"

    start_time = time.time()
    scrape_concurrently(url, max_depth, output_format, output_file)

    logging.info(f"Scraping completed in {time.time() - start_time:.2f} seconds.")