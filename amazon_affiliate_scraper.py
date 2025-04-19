import requests
from bs4 import BeautifulSoup
import time
import random
import re

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def extract_asin(url):
    # Extract ASIN from various Amazon URL formats
    asin_pattern = r'/([A-Z0-9]{10})(?:[/?]|$)'
    match = re.search(asin_pattern, url)
    return match.group(1) if match else None

def create_affiliate_link(url):
    asin = extract_asin(url)
    if asin:
        return f'https://www.amazon.com/dp/{asin}/?tag=87868584-20'
    return None

def scrape_amazon_deals():
    url = 'https://www.amazon.com/Best-Sellers/zgbs'
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product_links = []
            
            # Find product links in the Best Sellers page
            for link in soup.select('div[data-asin] a[href*="/dp/"]'):
                href = link.get('href')
                if href and '/dp/' in href:
                    full_url = f'https://www.amazon.com{href}' if href.startswith('/') else href
                    affiliate_link = create_affiliate_link(full_url)
                    if affiliate_link and affiliate_link not in product_links:
                        product_links.append(affiliate_link)
                        if len(product_links) >= 10:
                            break
            
            return product_links
            
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay + random.uniform(0, 1))
                continue
            print(f"Error after {max_retries} attempts: {str(e)}")
            return []

def save_links_to_file(links, filename='deals.txt'):
    try:
        with open(filename, 'w') as f:
            for link in links:
                f.write(f"{link}\n")
        print(f"✅ Saved {len(links)} Amazon affiliate links to {filename}")
    except IOError as e:
        print(f"Error saving to file: {str(e)}")

def main():
    print("Scraping Amazon Best Sellers...")
    affiliate_links = scrape_amazon_deals()
    
    if affiliate_links:
        save_links_to_file(affiliate_links)
        print("\nPreview of saved links:")
        for i, link in enumerate(affiliate_links[:3], 1):
            print(f"{i}. {link}")
        if len(affiliate_links) > 3:
            print("...")
    else:
        print("No links were scraped successfully.")

if __name__ == "__main__":
    main() 