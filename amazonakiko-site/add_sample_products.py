import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Sample products data
sample_products = [
    {
        'asin': 'B07ZPKBL6V',  # Amazon Echo Dot
        'title': 'Echo Dot (3rd Gen) - Smart speaker with Alexa',
        'price': '$49.99',
        'rating': 4.7,
        'review_count': 100000,
        'image_url': 'https://m.media-amazon.com/images/I/71Swqqe7XAL._AC_SL1500_.jpg',
        'image_uploaded': False,
        'last_updated': datetime.utcnow()
    },
    {
        'asin': 'B07XJ8C8F5',  # Fire TV Stick
        'title': 'Fire TV Stick 4K streaming device',
        'price': '$39.99',
        'rating': 4.6,
        'review_count': 50000,
        'image_url': 'https://m.media-amazon.com/images/I/51CgKGfMelL._AC_SL1000_.jpg',
        'image_uploaded': False,
        'last_updated': datetime.utcnow()
    },
    {
        'asin': 'B07B9W9K9P',  # Kindle Paperwhite
        'title': 'Kindle Paperwhite – Now Waterproof',
        'price': '$129.99',
        'rating': 4.8,
        'review_count': 75000,
        'image_url': 'https://m.media-amazon.com/images/I/51QTIyLQJFL._AC_SL1000_.jpg',
        'image_uploaded': False,
        'last_updated': datetime.utcnow()
    }
]

def add_products():
    for product in sample_products:
        # Use ASIN as document ID
        doc_ref = db.collection('products').document(product['asin'])
        doc_ref.set(product)
        print(f"Added product: {product['title']}")

if __name__ == "__main__":
    add_products()
    print("All sample products added to Firestore!") 