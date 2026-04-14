import os
import time
import json
import subprocess
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "prayers")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_youtube_id(title_english):
    """Use yt-dlp to get the first YouTube video ID for the given title."""
    query = f"{title_english} chanting"
    try:
        # Command: yt-dlp --get-id --default-search "ytsearch1" "{query}"
        result = subprocess.run(
            ["yt-dlp", "--get-id", "--default-search", "ytsearch1", query],
            capture_output=True,
            text=True,
            check=True,
            timeout=30 
        )
        video_id = result.stdout.strip()
        if video_id:
            return video_id
    except Exception as e:
        print(f"  Warning: yt-dlp search failed for '{title_english}': {e}")
    return None

def sync_youtube():
    print("Fetching all records from library table (paginating to bypass 1000 limit)...")
    all_records = []
    start = 0
    page_size = 1000

    # Pagination Loop
    while True:
        try:
            response = supabase.table("library").select("*").range(start, start + page_size - 1).execute()
            batch = response.data
            if not batch:
                break
            all_records.extend(batch)
            print(f"  Fetched {len(all_records)} records...")
            if len(batch) < page_size:
                break
            start += page_size
        except Exception as e:
            print(f"Error fetching from library: {e}")
            return

    total_records = len(all_records)
    print(f"Starting sync for {total_records} total records...")

    for index, record in enumerate(all_records):
        title = record.get("title") 
        slug = record.get("id")
        
        if not title or not slug:
            continue

        file_path = f"{slug}.json"
        counter_prefix = f"[{index+1}/{total_records}]"
        
        # 1. Download JSON and check if synced
        try:
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)
            prayer_data = json.loads(storage_response.decode('utf-8'))
            
            # RESUME LOGIC: Skip if already has a youtube_id
            if "youtube_id" in prayer_data and prayer_data["youtube_id"]:
                # Silent skip to keep the log clean
                continue

        except Exception as e:
            print(f"{counter_prefix} Error downloading {file_path}: {e}")
            continue

        print(f"{counter_prefix} Processing: {title}")
        
        # 2. Get YouTube ID
        youtube_id = get_youtube_id(title)
        if not youtube_id:
            print(f"  No YouTube video found. Skipping.")
            continue
        
        print(f"  Found ID: {youtube_id}")

        # 3. Update the dictionary
        prayer_data["youtube_id"] = youtube_id

        # 4. Upload back to Supabase
        try:
            updated_json = json.dumps(prayer_data, ensure_ascii=False, indent=2).encode('utf-8')
            supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=file_path,
                file=updated_json,
                file_options={"content-type": "application/json", "x-upsert": "true"}
            )
            print(f"  Successfully updated {file_path}")
        except Exception as e:
            try:
                supabase.storage.from_(SUPABASE_BUCKET).update(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json"}
                )
                print(f"  Updated via update() fallback")
            except Exception as e2:
                print(f"  Final error uploading {file_path}: {e2}")

        # Rate limiting sleep
        time.sleep(1.2)

if __name__ == "__main__":
    sync_youtube()