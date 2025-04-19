import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
cred_dict = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL').replace('@', '%40')}"
}

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

def test_firestore_connection():
    try:
        test_doc = {
            "message": "Hello from amazon-scoopy",
            "timestamp": datetime.utcnow().isoformat()
        }
        db.collection("test_collection").document("hello_world").set(test_doc)
        print("✅ Firestore test document written successfully.")
    except Exception as e:
        print("❌ Firestore test write failed:", str(e))

def get_headers():
    # List of common user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]
    
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

def get_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def scrape_amazon_best_sellers():
    print("Starting Amazon Best Sellers scrape...")
    url = "https://www.amazon.com/Best-Sellers/zgbs"
    session = get_session()
    
    try:
        # Add a much longer initial delay
        print("Waiting before making request...")
        time.sleep(random.uniform(10, 15))
        
        response = session.get(url, headers=get_headers())
        response.raise_for_status()
        
        # Save the HTML for debugging
        with open('amazon_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all product items
        products = soup.select('div[data-asin]')
        print(f"Found {len(products)} products")
        
        for i, product in enumerate(products, 1):
            try:
                # Extract product details
                asin = product.get('data-asin')
                
                # Try to find the title by looking for any div with text content
                title_div = None
                for div in product.find_all('div'):
                    if div.text.strip() and len(div.text.strip()) > 10:  # Basic check for meaningful text
                        title_div = div
                        break
                
                price = product.select_one('span._cDEzb_p13n-sc-price_3mJ9Z')
                rating = product.select_one('span.a-icon-alt')
                review_count = product.select_one('span.a-size-small')
                
                print(f"\n🔍 Processing product {i}/{len(products)}")
                print(f"ASIN: {asin}")
                print(f"Title element found: {title_div is not None}")
                if title_div:
                    print(f"Title text: {title_div.text.strip()}")
                
                if not asin or not title_div:
                    print("❌ Skipping product - missing ASIN or title")
                    continue
                
                product_data = {
                    'asin': asin,
                    'title': title_div.text.strip(),
                    'price': price.text.strip() if price else 'N/A',
                    'rating': rating.text.split()[0] if rating else 'N/A',
                    'review_count': review_count.text.strip() if review_count else '0',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'amazon_best_sellers'
                }
                
                print(f"📦 Ready to upload ASIN: {asin} - Title: {title_div.text.strip()}")
                
                try:
                    db.collection("products").document(asin).set(product_data)
                    print(f"✅ Uploaded {title_div.text.strip()} to Firestore.")
                except Exception as e:
                    print(f"❌ Failed to upload {asin}: {str(e)}")
                
                # Add a longer random delay between products
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                print(f"❌ Error processing product: {str(e)}")
                continue
                
    except Exception as e:
        print(f"❌ Error scraping Amazon Best Sellers: {str(e)}")

if __name__ == "__main__":
    print("Starting Amazon Best Sellers scraper...")
    test_firestore_connection()
    scrape_amazon_best_sellers()
    print("Scraping completed!")
