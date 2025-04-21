import firebase_admin
from firebase_admin import credentials, storage, firestore
import os
import requests
from PIL import Image
import io
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload.log'),
        logging.StreamHandler()
    ]
)

class ImageUploader:
    def __init__(self):
        # Initialize Firebase
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'test1-1d33b.appspot.com'
        })
        self.db = firestore.client()
        self.bucket = storage.bucket()
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.max_workers = 5  # concurrent uploads
        self.optimize_config = {
            'max_size': (800, 800),
            'quality': 85,
            'format': 'JPEG'
        }

    def optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image before upload"""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if needed
            img.thumbnail(self.optimize_config['max_size'], Image.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            img.save(
                output,
                format=self.optimize_config['format'],
                quality=self.optimize_config['quality'],
                optimize=True
            )
            return output.getvalue()
        except Exception as e:
            logging.error(f"Image optimization failed: {str(e)}")
            return image_data  # Return original if optimization fails

    def download_image(self, url: str, retry_count: int = 0) -> Optional[bytes]:
        """Download image with retry logic"""
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            if retry_count < self.max_retries:
                logging.warning(f"Download failed (attempt {retry_count + 1}/{self.max_retries}): {str(e)}")
                time.sleep(self.retry_delay * (retry_count + 1))
                return self.download_image(url, retry_count + 1)
            logging.error(f"Download failed after {self.max_retries} attempts: {str(e)}")
            return None

    def upload_to_firebase(self, image_data: bytes, asin: str, retry_count: int = 0) -> bool:
        """Upload image to Firebase with retry logic"""
        try:
            blob = self.bucket.blob(f'products/{asin}.jpg')
            
            # Upload with metadata
            blob.upload_from_string(
                image_data,
                content_type='image/jpeg',
                metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'asin': asin
                }
            )
            
            # Make public
            blob.make_public()
            
            # Update Firestore with upload status
            self.db.collection('products').document(asin).update({
                'image_uploaded': True,
                'image_url': blob.public_url,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
            
            return True
        except Exception as e:
            if retry_count < self.max_retries:
                logging.warning(f"Upload failed (attempt {retry_count + 1}/{self.max_retries}): {str(e)}")
                time.sleep(self.retry_delay * (retry_count + 1))
                return self.upload_to_firebase(image_data, asin, retry_count + 1)
            logging.error(f"Upload failed after {self.max_retries} attempts: {str(e)}")
            return False

    def process_product(self, product: Dict) -> Dict:
        """Process a single product"""
        start_time = time.time()
        asin = product['asin']
        image_url = product['image_url']
        
        logging.info(f"Processing product {asin}")
        
        # Download image
        image_data = self.download_image(image_url)
        if not image_data:
            return {
                'asin': asin,
                'status': 'failed',
                'error': 'download_failed',
                'duration': time.time() - start_time
            }
        
        # Optimize image
        optimized_data = self.optimize_image(image_data)
        
        # Upload to Firebase
        success = self.upload_to_firebase(optimized_data, asin)
        
        return {
            'asin': asin,
            'status': 'success' if success else 'failed',
            'duration': time.time() - start_time
        }

    def process_batch(self, products: List[Dict]):
        """Process multiple products concurrently"""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_product = {
                executor.submit(self.process_product, product): product
                for product in products
            }
            
            for future in as_completed(future_to_product):
                product = future_to_product[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"Error processing {product['asin']}: {str(e)}")
                    results.append({
                        'asin': product['asin'],
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results

    def get_products_from_firestore(self, batch_size: int = 100) -> List[Dict]:
        """Get products from Firestore that need image processing"""
        products = []
        query = self.db.collection('products').where('image_uploaded', '==', False).limit(batch_size)
        docs = query.stream()
        
        for doc in docs:
            data = doc.to_dict()
            if 'image_url' in data:
                products.append({
                    'asin': doc.id,
                    'image_url': data['image_url']
                })
        
        return products

def main():
    uploader = ImageUploader()
    
    while True:
        # Get batch of products
        products = uploader.get_products_from_firestore()
        if not products:
            logging.info("No more products to process")
            break
        
        logging.info(f"Processing batch of {len(products)} products")
        
        # Process batch
        results = uploader.process_batch(products)
        
        # Log results
        success_count = sum(1 for r in results if r['status'] == 'success')
        logging.info(f"Batch complete: {success_count}/{len(products)} successful")
        
        # Save results to file
        with open('upload_results.json', 'a') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
        
        # Add delay between batches
        time.sleep(5)

if __name__ == "__main__":
    main() 