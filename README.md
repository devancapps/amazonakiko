# Amazon to Firestore Affiliate System

A Python tool that scrapes Amazon Best Sellers, generates affiliate links, and stores the data in Firebase Firestore.

## Features

- Scrapes Amazon Best Sellers page
- Extracts product details (title, ASIN, price, image URL)
- Generates affiliate links with your tag
- Stores data in Firebase Firestore
- Includes retry logic and error handling
- Uses environment variables for configuration

## Setup

1. Clone the repository:
```bash
git clone https://github.com/devancapps/amazonakiko.git
cd amazon-scoopy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase:
   - Create a Firebase project
   - Generate a service account key
   - Download the credentials JSON file

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your Firebase credentials:
     ```
     FIREBASE_PROJECT_ID=your-project-id
     FIREBASE_CLIENT_EMAIL=your-client-email@project.iam.gserviceaccount.com
     FIREBASE_PRIVATE_KEY="your-private-key"
     ```

## Usage

Run the script:
```bash
python amazon_to_firestore.py
```

The script will:
1. Scrape Amazon Best Sellers
2. Extract product details
3. Generate affiliate links
4. Upload data to Firestore
5. Display the number of products uploaded

## Project Structure

```
amazon-scoopy/
├── amazon_to_firestore.py  # Main script
├── firebase.py            # Firestore initialization
├── .env                   # Local config (gitignored)
├── .env.example           # Example config
├── .gitignore            # Git ignore rules
└── requirements.txt      # Python dependencies
```

## Notes

- The script uses a basic user-agent to avoid detection
- Includes retry logic for failed requests
- Products are stored in the 'deals' collection in Firestore
- ASIN is used as the document ID
- Existing documents are updated with new data
