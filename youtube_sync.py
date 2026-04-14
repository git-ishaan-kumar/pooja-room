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
            timeout=30 # Prevent yt-dlp from hanging forever
        )
        video_id = result.stdout.strip()
        if video_id:
            return video_id
    except Exception as e:
        print(f"  Warning: yt-dlp search failed for '{title_english}': {e}")
    return None

def sync_youtube():
    print("Fetching records from library table (requesting up to 2000)...")
    try:
        # FIX: Using .range(0, 2000) to bypass the default 1000 record limit
        response = supabase.table("library").select("*").range(0, 2000).execute()
        records = response.data
    except Exception as e:
        print(f"Error fetching from library: {e}")
        return

    total_records = len(records)
    print(f"Found {total_records} records. Starting sync...")

    for index, record in enumerate(records):
        title = record.get("title") 
        slug = record.get("id")
        
        if not title or not slug:
            continue

        file_path = f"{slug}.json"
        counter_prefix = f"[{index+1}/{total_records}]"
        
        # 1. Download JSON first to check if we already have the YouTube ID
        try:
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)
            prayer_data = json.loads(storage_response.decode('utf-8'))
            
            # --- RESUME LOGIC ---
            if "youtube_id" in prayer_data and prayer_data["youtube_id"]:
                print(f"{counter_prefix} Skipping {title}: Already synced.")
                continue
            # --------------------

        except Exception as e:
            # If the file doesn't exist or times out, we skip and log
            print(f"{counter_prefix} Error downloading {file_path}: {e}")
            continue

        print(f"{counter_prefix} Processing: {title}")
        
        # 2. Get YouTube ID
        youtube_id = get_youtube_id(title)
        if not youtube_id:
            print(f"  No YouTube video found for '{title}'. Skipping.")
            continue
        
        print(f"  Found YouTube ID: {youtube_id}")

        # 3. Update the dictionary
        prayer_data["youtube_id"] = youtube_id

        # 4. Upload updated JSON back to Supabase
        try:
            updated_json = json.dumps(prayer_data, ensure_ascii=False, indent=2).encode('utf-8')
            supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=file_path,
                file=updated_json,
                file_options={"content-type": "application/json", "x-upsert": "true"}
            )
            print(f"  Successfully updated and uploaded {file_path}")
        except Exception as e:
            # Fallback if upload/upsert fails
            try:
                supabase.storage.from_(SUPABASE_BUCKET).update(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json"}
                )
                print(f"  Successfully updated {file_path} via update()")
            except Exception as e2:
                print(f"  Final error uploading {file_path}: {e2}")

        # Safety wait to avoid being blocked by YouTube or overwhelming the Pi
        time.sleep(1.2)

if __name__ == "__main__":
    sync_youtube()