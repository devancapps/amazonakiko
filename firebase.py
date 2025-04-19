import os
from google.cloud import firestore
from dotenv import load_dotenv

def init_firestore():
    """Initialize Firestore client with credentials from environment variables."""
    load_dotenv()
    
    # Required environment variables
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_PRIVATE_KEY'
    ]
    
    # Check if all required variables are present
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Initialize Firestore client
    try:
        db = firestore.Client(project=os.getenv('FIREBASE_PROJECT_ID'))
        return db
    except Exception as e:
        raise Exception(f"Failed to initialize Firestore client: {str(e)}")

def get_deals_collection():
    """Get the deals collection reference."""
    db = init_firestore()
    return db.collection('deals')
