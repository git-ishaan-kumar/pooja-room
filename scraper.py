import os
import time
import json
import requests
import cloudscraper
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from slugify import slugify

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "prayers")
TEST_MODE = os.getenv("TEST_MODE", "True").lower() == "true"

# Target Categories

def get_soup(url):
    """Fetch URL and return BeautifulSoup object with Cloudflare bypass."""
    time.sleep(3)
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True
            }
        )
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def upload_to_supabase(slug, data, category_name):
    """Upload JSON to storage and upsert metadata to DB using REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    # 1. Upload JSON to Storage
    storage_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{slug}.json"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "x-upsert": "true"
    }
    
    try:
        # Encode data to bytes for UTF-8 support (Sanskrit characters)
        storage_data = json.dumps(data).encode('utf-8')
        storage_resp = requests.post(storage_url, headers=headers, data=storage_data)
        
        if storage_resp.status_code == 400:
            print(f"  Warning: 400 Bad Request for {slug}. Response: {storage_resp.text}")
            
        storage_resp.raise_for_status()
        json_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{slug}.json"
    except Exception as e:
        print(f"Storage Upload Error for {slug}: {e}")
        return

    # 2. Upsert to Library Table
    db_url = f"{SUPABASE_URL}/rest/v1/library"
    db_headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    payload = {
        "id": slug,
        "category": category_name,
        "title": data["title_english"],
        "json_url": json_url
    }
    
    try:
        db_resp = requests.post(db_url, headers=db_headers, data=json.dumps(payload))
        db_resp.raise_for_status()
    except Exception as e:
        print(f"Database Upsert Error for {slug}: {e}")

def scrape_prayer(url, category_name):
    """Scrape a single prayer in all available languages."""
    soup = get_soup(url)
    if not soup:
        return None

    # Get English Title
    title_el = soup.find("p", id="stitle")
    title_english = title_el.text.strip() if title_el else "Unknown Title"
    slug = slugify(title_english)

    # Check if already exists locally
    local_path = f"prayers/{slug}.json"
    if os.path.exists(local_path):
        print(f"Skipping {title_english} (Already exists)")
        return None

    # Language Map
    languages = {}
    
    # Extract language links from languageView table
    lang_view = soup.find("div", class_="languageView")
    lang_links = {"english": url}
    if lang_view:
        for a in lang_view.find_all("a"):
            lang_name = a.text.strip().lower()
            # Handle relative paths by removing leading dots if present
            href = a["href"]
            if href.startswith(".."):
                href = href.lstrip(".")
            lang_url = urljoin("https://www.vignanam.org", href)
            lang_links[lang_name] = lang_url

    # Scrape each language
    for lang, l_url in lang_links.items():
        l_soup = get_soup(l_url) if lang != "english" else soup
        if l_soup:
            text_div = l_soup.find("div", id="stext")
            if text_div:
                # Extract lines, filtering out empty ones and "Browse Related Categories:"
                lines = [
                    p.text.strip() for p in text_div.find_all("p") 
                    if p.text.strip() and "Browse Related Categories:" not in p.text
                ]
                if not lines:
                    # Fallback if text is not in <p> tags
                    lines = [
                        line.strip() for line in text_div.text.split("\n") 
                        if line.strip() and "Browse Related Categories:" not in line
                    ]
                languages[lang] = lines

    if not languages.get("english"):
        return None

    prayer_data = {
        "id": slug,
        "category": category_name,
        "title_english": title_english,
        "body": languages
    }

    # Save locally
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(prayer_data, f, ensure_ascii=False, indent=2)

    # Upload to Supabase
    upload_to_supabase(slug, prayer_data, category_name)
    
    return slug

def main():
    print("Starting Pooja Room Scraper (Dynamic Category Mode)...")
    base_url = "https://www.vignanam.org/"
    soup = get_soup(base_url)
    if not soup:
        print("Failed to fetch homepage.")
        return

    processed_count = 0
    tree = soup.find("ul", class_="aqtree3clickable")
    if not tree:
        print("Could not find prayer tree.")
        return

    for li in tree.find_all("li", recursive=False):
        # Find category name
        cat_link = li.find("a", class_="link1")
        if not cat_link:
            continue
        
        # Clean category name: split at ( and replace \xa0
        category_name = cat_link.get_text().split('(')[0].replace('\xa0', ' ').strip()
        print(f"\nScraping Category: {category_name}")

        # Find all prayers in this category
        prayer_links = li.find_all("a", class_="link4")
        for a in prayer_links:
            href = a.get("href", "")
            if href.startswith("english/"):
                full_url = urljoin(base_url, href)
                print(f"  Processing: {full_url}")
                
                slug = scrape_prayer(full_url, category_name)
                if slug:
                    processed_count += 1
                    print(f"  Successfully processed: {slug}")
                
                if TEST_MODE and processed_count >= 3:
                    print("\nTEST_MODE: Processed 3 prayers. Stopping.")
                    return

    print(f"\nScraping Complete. Total processed: {processed_count}")

if __name__ == "__main__":
    main()
