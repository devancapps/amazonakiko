import firebase_admin
from firebase_admin import credentials, storage
import os
import requests
from urllib.parse import urlparse
import time

# Initialize Firebase Admin SDK
cred = credentials.Certificate('serviceAccountKey.json')  # You'll need to download this from Firebase Console
firebase_admin.initialize_app(cred, {
    'storageBucket': 'test1-1d33b.appspot.com'
})

def download_image(url, filename):
    """Download image from URL and save it locally"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def upload_to_firebase(local_path, asin):
    """Upload image to Firebase Storage"""
    try:
        bucket = storage.bucket()
        blob = bucket.blob(f'products/{asin}.jpg')
        
        # Upload the file
        blob.upload_from_filename(local_path)
        
        # Make the blob publicly viewable
        blob.make_public()
        
        print(f"Uploaded {asin}.jpg successfully")
        return True
    except Exception as e:
        print(f"Error uploading {asin}.jpg: {str(e)}")
        return False

def process_products():
    """Process products from Firestore and upload their images"""
    # Create temp directory if it doesn't exist
    if not os.path.exists('temp_images'):
        os.makedirs('temp_images')
    
    # Get products from Firestore (you'll need to implement this part)
    # For now, we'll use a sample product
    products = [
        {
            'asin': 'B07ZPKBL6V',  # Example ASIN
            'image_url': 'https://m.media-amazon.com/images/I/71Swqqe7XAL._AC_SL1500_.jpg'
        }
        # Add more products as needed
    ]
    
    for product in products:
        asin = product['asin']
        image_url = product['image_url']
        
        # Download image
        local_path = f'temp_images/{asin}.jpg'
        if download_image(image_url, local_path):
            # Upload to Firebase
            if upload_to_firebase(local_path, asin):
                print(f"Successfully processed {asin}")
            else:
                print(f"Failed to upload {asin}")
        
        # Clean up
        if os.path.exists(local_path):
            os.remove(local_path)
        
        # Add delay to avoid rate limiting
        time.sleep(1)

if __name__ == "__main__":
    process_products() 