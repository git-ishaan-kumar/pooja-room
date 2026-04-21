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

def get_youtube_id_masterpiece(title_english):
    """
    Search for top 5 results using ytsearch5.
    Fetch metadata using --dump-json --flat-playlist.
    Return the ID of the most viewed video.
    """
    query = f"{title_english} chanting"
    try:
        # Command: yt-dlp --dump-json --flat-playlist --default-search "ytsearch5" "{query}"
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--flat-playlist", "--default-search", "ytsearch5", query],
            capture_output=True,
            text=True,
            check=True,
            timeout=45
        )
        
        # result.stdout will contain multiple JSON objects (one per line)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            try:
                video_data = json.loads(line)
                # Ensure it has an id and view_count
                if 'id' in video_data:
                    videos.append({
                        'id': video_data['id'],
                        'view_count': video_data.get('view_count') or 0
                    })
            except json.JSONDecodeError:
                continue

        if not videos:
            return None

        # Sort by view_count descending
        sorted_videos = sorted(videos, key=lambda x: x['view_count'], reverse=True)
        best_video = sorted_videos[0]
        
        return best_video['id']

    except Exception as e:
        print(f"  Warning: masterpiece search failed for '{title_english}': {e}")
    return None

def sync_youtube():
    # User Input Prompt
    print("\n--- POOJA ROOM YOUTUBE SYNC ---")
    print("Do you want to:")
    print(" (1) Skip records with existing YouTube IDs")
    print(" (2) Overwrite all existing IDs (Force Sync)")
    choice = input("Choice (1/2): ").strip()
    
    if choice not in ['1', '2']:
        print("Invalid choice. Defaulting to (1) Skip.")
        overwrite_mode = False
    else:
        overwrite_mode = (choice == '2')

    print("\nFetching all records from library table (paginating)...")
    all_records = []
    start = 0
    page_size = 1000

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
    print(f"Starting sync for {total_records} total records. Overwrite mode: {overwrite_mode}")

    for index, record in enumerate(all_records):
        title = record.get("title")
        slug = record.get("id")

        if not title or not slug:
            continue

        file_path = f"{slug}.json"
        counter_prefix = f"[{index+1}/{total_records}]"

        # 1. Download JSON
        try:
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)        
            prayer_data = json.loads(storage_response.decode('utf-8'))

            # RESPECT USER CHOICE
            has_id = "youtube_id" in prayer_data and prayer_data["youtube_id"]
            if has_id and not overwrite_mode:
                # Skip
                continue

        except Exception as e:
            print(f"{counter_prefix} Error downloading {file_path}: {e}")
            continue

        print(f"{counter_prefix} Syncing '{title}'...")

        # 2. Get Best YouTube ID
        youtube_id = get_youtube_id_masterpiece(title)
        if not youtube_id:
            print(f"  No YouTube video found. Skipping.")
            continue

        # 3. Update the data
        prayer_data["youtube_id"] = youtube_id

        # 4. Upload back to Supabase
        try:
            updated_json = json.dumps(prayer_data, ensure_ascii=False, indent=2).encode('utf-8')  
            supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=file_path,
                file=updated_json,
                file_options={"content-type": "application/json", "x-upsert": "true"}
            )
            print(f"  Successfully updated: {youtube_id}")
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

        # Rate limiting sleep (Masterpiece search is heavier)
        time.sleep(1.5)

if __name__ == "__main__":
    sync_youtube()
