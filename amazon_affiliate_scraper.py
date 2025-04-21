import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firebase
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization error: {str(e)}")
    db = None

def get_headers():
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }

def extract_asin(url):
    # Extract ASIN from various Amazon URL formats
    asin_patterns = [
        r'/([A-Z0-9]{10})(?:[/?]|$)',  # Standard ASIN pattern
        r'dp/([A-Z0-9]{10})',          # dp pattern
        r'product/([A-Z0-9]{10})',     # product pattern
        r'deal/([A-Z0-9]{10})'         # deal pattern
    ]
    
    for pattern in asin_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def create_affiliate_link(url):
    asin = extract_asin(url)
    if asin:
        return f'https://www.amazon.com/dp/{asin}/?tag=87868584-20'
    return None

def safe_extract_text(element, default=""):
    """Safely extract text from a BeautifulSoup element"""
    if element and hasattr(element, 'text'):
        return element.text.strip()
    return default

def safe_convert_price(price_text):
    """Safely convert price text to a standardized format"""
    if not price_text:
        return None
    
    # Remove currency symbols and whitespace
    price_text = re.sub(r'[^\d.,]', '', price_text)
    
    try:
        # Handle different price formats
        if ',' in price_text and '.' in price_text:
            price_text = price_text.replace(',', '')
        elif ',' in price_text:
            price_text = price_text.replace(',', '.')
        
        price = float(price_text)
        return f"${price:.2f}"
    except (ValueError, TypeError):
        return None

def safe_convert_rating(rating_text):
    """Safely convert rating text to a float"""
    if not rating_text:
        return None
    
    try:
        # Extract first number from text (e.g., "4.5 out of 5" -> 4.5)
        match = re.search(r'(\d+\.?\d*)', rating_text)
        if match:
            return float(match.group(1))
    except (ValueError, TypeError):
        pass
    return None

def extract_product_info(soup, asin):
    try:
        # Multiple selectors for different page layouts
        title_selectors = ['span#productTitle', 'h1.product-title-word-break', 'h1.a-size-large']
        price_selectors = ['span.a-price-whole', 'span.a-offscreen', 'span.a-color-price']
        rating_selectors = ['span.a-icon-alt', 'i.a-icon-star span.a-icon-alt']
        review_selectors = ['span#acrCustomerReviewText', 'span.a-size-base.a-color-secondary']
        image_selectors = ['img#landingImage', 'img#imgBlkFront', 'img.a-dynamic-image']

        # Try different selectors for each field
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = safe_extract_text(title_elem)
                break

        price = None
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = safe_convert_price(safe_extract_text(price_elem))
                break

        rating = None
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                rating = safe_convert_rating(safe_extract_text(rating_elem))
                break

        reviews = 0
        for selector in review_selectors:
            reviews_elem = soup.select_one(selector)
            if reviews_elem:
                reviews_text = safe_extract_text(reviews_elem)
                try:
                    reviews = int(re.sub(r'[^\d]', '', reviews_text))
                    break
                except ValueError:
                    continue

        image = None
        for selector in image_selectors:
            image_elem = soup.select_one(selector)
            if image_elem and 'src' in image_elem.attrs:
                image = image_elem['src']
                break

        return {
            'asin': asin,
            'title': title,
            'price': price,
            'rating': rating,
            'review_count': reviews,
            'image': image,
            'timestamp': datetime.utcnow(),
            'last_updated': datetime.utcnow()
        }
    except Exception as e:
        print(f"Error extracting product info for ASIN {asin}: {str(e)}")
        return None

def save_to_firestore(product_data):
    if not db:
        print("Firebase not initialized. Skipping database save.")
        return False
    
    try:
        if not product_data.get('asin'):
            print("Missing ASIN, skipping Firestore save")
            return False
            
        # Use ASIN as document ID
        doc_ref = db.collection('products').document(product_data['asin'])
        doc_ref.set(product_data, merge=True)
        return True
    except Exception as e:
        print(f"Error saving to Firestore: {str(e)}")
        return False

def scrape_deals_page():
    """Specialized function for scraping the deals page"""
    deals_urls = [
        'https://www.amazon.com/deals?ref_=nav_cs_gb',
        'https://www.amazon.com/gp/goldbox',
        'https://www.amazon.com/gp/todays-deals'
    ]
    
    products = []
    for url in deals_urls:
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different selectors for deal items
            deal_selectors = [
                'div[data-testid="deal-card"]',
                'div.DealGridItem-module__dealItem',
                'div.a-section.a-spacing-none.tallCellView',
                'div[data-component-type="deal"]'
            ]
            
            for selector in deal_selectors:
                deals = soup.select(selector)
                if deals:
                    for deal in deals:
                        try:
                            link = deal.find('a', href=True)
                            if link and '/dp/' in link['href']:
                                full_url = f"https://www.amazon.com{link['href']}" if link['href'].startswith('/') else link['href']
                                affiliate_link = create_affiliate_link(full_url)
                                if affiliate_link:
                                    response = requests.get(affiliate_link, headers=get_headers(), timeout=10)
                                    response.raise_for_status()
                                    product_soup = BeautifulSoup(response.text, 'html.parser')
                                    asin = extract_asin(affiliate_link)
                                    if asin:
                                        product_data = extract_product_info(product_soup, asin)
                                        if product_data:
                                            products.append(product_data)
                                            save_to_firestore(product_data)
                                            
                                            if len(products) >= 12:  # Limit to 12 products
                                                return products
                                            
                                            time.sleep(random.uniform(1, 2))  # Random delay
                        except Exception as e:
                            print(f"Error processing deal: {str(e)}")
                            continue
                    
                    if products:  # If we found products with this selector, stop trying others
                        break
            
            if products:  # If we found products on this URL, stop trying others
                break
                
        except requests.RequestException as e:
            print(f"Error accessing deals page {url}: {str(e)}")
            continue
            
    return products

def scrape_amazon_page(url, source_name):
    max_retries = 3
    retry_delay = 2
    products = []
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product_links = []
            
            # Find product links
            for link in soup.select('div[data-asin] a[href*="/dp/"]'):
                href = link.get('href')
                if href and '/dp/' in href:
                    full_url = f'https://www.amazon.com{href}' if href.startswith('/') else href
                    affiliate_link = create_affiliate_link(full_url)
                    if affiliate_link and affiliate_link not in product_links:
                        product_links.append(affiliate_link)
                        if len(product_links) >= 12:  # Increased to 12 products per page
                            break
            
            # Get detailed product info
            for link in product_links:
                asin = extract_asin(link)
                if asin:
                    try:
                        response = requests.get(link, headers=get_headers(), timeout=10)
                        response.raise_for_status()
                        product_soup = BeautifulSoup(response.text, 'html.parser')
                        product_data = extract_product_info(product_soup, asin)
                        
                        if product_data:
                            product_data['source'] = source_name
                            products.append(product_data)
                            # Save to Firestore
                            save_to_firestore(product_data)
                            
                        time.sleep(random.uniform(1, 2))  # Random delay between requests
                    except Exception as e:
                        print(f"Error processing product {asin}: {str(e)}")
                        continue
            
            return products
            
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay + random.uniform(0, 1))
                continue
            print(f"Error after {max_retries} attempts: {str(e)}")
            return []

def scrape_all_sources():
    sources = {
        'amazon_best_sellers': 'https://www.amazon.com/Best-Sellers/zgbs',
        'amazon_movers_shakers': 'https://www.amazon.com/gp/movers-and-shakers/',
        'amazon_most_wished': 'https://www.amazon.com/gp/most-wished-for/',
        'amazon_new_releases': 'https://www.amazon.com/gp/new-releases/'
    }
    
    all_products = []
    
    # Scrape regular pages
    for source_name, url in sources.items():
        print(f"\nScraping {source_name}...")
        products = scrape_amazon_page(url, source_name)
        all_products.extend(products)
        print(f"Found {len(products)} products from {source_name}")
        time.sleep(random.uniform(2, 3))  # Delay between different sources
    
    # Scrape deals page separately
    print("\nScraping amazon_deals...")
    deal_products = scrape_deals_page()
    if deal_products:
        for product in deal_products:
            product['source'] = 'amazon_deals'
        all_products.extend(deal_products)
        print(f"Found {len(deal_products)} products from amazon_deals")
    
    return all_products

def save_links_to_file(products, filename='deals.txt'):
    try:
        with open(filename, 'w') as f:
            for product in products:
                f.write(f"https://www.amazon.com/dp/{product['asin']}/?tag=87868584-20\n")
        print(f"✅ Saved {len(products)} Amazon affiliate links to {filename}")
    except IOError as e:
        print(f"Error saving to file: {str(e)}")

def main():
    print("Starting Amazon product scraper...")
    products = scrape_all_sources()
    
    if products:
        save_links_to_file(products)
        print(f"\nTotal products scraped: {len(products)}")
        print("\nPreview of saved products:")
        for i, product in enumerate(products[:3], 1):
            print(f"{i}. {product['title']} - {product['price']}")
        if len(products) > 3:
            print("...")
    else:
        print("No products were scraped successfully.")

if __name__ == "__main__":
    main() 