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
            check=True
        )
        video_id = result.stdout.strip()
        if video_id:
            return video_id
    except subprocess.CalledProcessError as e:
        print(f"Error searching YouTube for '{title_english}': {e}")
    except Exception as e:
        print(f"Unexpected error for '{title_english}': {e}")
    return None

def sync_youtube():
    print("Fetching records from library table...")
    try:
        # Fetch all records from library table
        response = supabase.table("library").select("*").execute()
        records = response.data
    except Exception as e:
        print(f"Error fetching from library: {e}")
        return

    print(f"Found {len(records)} records. Starting sync...")

    for record in records:
        title = record.get("title") # In scraper.py, payload['title'] = data["title_english"]
        slug = record.get("id")
        
        if not title or not slug:
            print(f"Skipping record with missing title or id: {record}")
            continue

        print(f"Processing: {title} ({slug})")
        
        # 1. Get YouTube ID
        youtube_id = get_youtube_id(title)
        if not youtube_id:
            print(f"  No YouTube video found for '{title}'. Skipping.")
            continue
        
        print(f"  Found YouTube ID: {youtube_id}")

        # 2. Download JSON from storage
        file_path = f"{slug}.json"
        try:
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)
            # storage_response is bytes
            prayer_data = json.loads(storage_response.decode('utf-8'))
        except Exception as e:
            print(f"  Error downloading {file_path}: {e}")
            continue

        # 3. Update JSON
        prayer_data["youtube_id"] = youtube_id

        # 4. Upload updated JSON
        try:
            updated_json = json.dumps(prayer_data, ensure_ascii=False, indent=2).encode('utf-8')
            supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=file_path,
                file=updated_json,
                file_options={"content-type": "application/json", "x-upsert": "true"}
            )
            print(f"  Successfully updated and uploaded {file_path}")
        except Exception as e:
            # If upload fails, try update (though x-upsert should handle it)
            try:
                supabase.storage.from_(SUPABASE_BUCKET).update(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json"}
                )
                print(f"  Successfully updated {file_path} via update()")
            except Exception as e2:
                print(f"  Error uploading {file_path}: {e2}")

        # Wait to stay safe
        time.sleep(1)

if __name__ == "__main__":
    sync_youtube()
