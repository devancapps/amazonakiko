# Amazon Affiliate Scraper

A lightweight Python script that scrapes Amazon's Best Sellers page and generates affiliate links.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the script:
```bash
python amazon_affiliate_scraper.py
```

## Features

- Scrapes Amazon's Best Sellers page
- Extracts product ASINs and generates affiliate links
- Includes retry logic and error handling
- Saves links to `deals.txt`
- Uses proper headers to avoid bot detection

## Output

The script will:
1. Scrape the Best Sellers page
2. Generate affiliate links with your tag
3. Save the links to `deals.txt`
4. Display a preview of the saved links

## Notes

- The script uses a basic user-agent to avoid detection
- It includes retry logic for failed requests
- Links are saved one per line in `deals.txt` 