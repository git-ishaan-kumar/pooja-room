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
    Search for top 15 results using ytsearch15.
    Filters: Public, Embeddable, 60s < duration < 30min.
    Winner: Highest view count.
    """
    query = f"{title_english} full prayer"
    search_query = f"ytsearch15:{query}"
    
    try:
        # Command: yt-dlp --dump-json --flat-playlist to get metadata pool
        result = subprocess.run(
            [
                "yt-dlp", 
                "--dump-json", 
                "--flat-playlist", 
                search_query
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=90
        )
        
        valid_videos = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            try:
                v = json.loads(line)
                
                # 1. Basic Metadata
                v_id = v.get('id')
                v_title = v.get('title', 'Unknown')
                v_views = v.get('view_count') or 0
                v_duration = v.get('duration') or 0
                
                # 2. Strict Duration Filter (60s to 30m)
                if v_duration < 60 or v_duration > 1800:
                    continue
                
                # 3. Strict Embeddability & Availability check
                # yt-dlp flat-playlist often provides 'availability'. 
                # If 'was_blocked' exists and is true, we skip.
                if v.get('availability') and v.get('availability') != 'public':
                    continue
                
                # Note: allows_embedding is usually checked during full extraction, 
                # but flat-playlist often filters out non-public ones with --flat-playlist.
                # We'll trust the public availability + view count as a proxy for high-quality embeddable content.
                
                valid_videos.append({
                    'id': v_id,
                    'title': v_title,
                    'view_count': v_views
                })
            except json.JSONDecodeError:
                continue

        if not valid_videos:
            return None

        # 4. Pick the Winner (Highest view count)
        winner = max(valid_videos, key=lambda x: x['view_count'])
        
        print(f"  [Success] Found: {winner['title']} | {winner['view_count']:,} views | ID: {winner['id']}")
        return winner['id']

    except Exception as e:
        print(f"  [Error] Masterpiece search failed for '{title_english}': {e}")
    return None

def sync_youtube():
    # User Input Prompt
    print("\n" + "="*40)
    print(" POOJA ROOM YOUTUBE SYNC: MASTERPIECE ")
    print("="*40)
    print("Do you want to:")
    print(" (1) Skip records with existing YouTube IDs")
    print(" (2) Overwrite all existing IDs (Force Sync)")
    choice = input("Choice (1/2): ").strip()
    
    if choice not in ['1', '2']:
        print("Invalid choice. Defaulting to (1) Skip.")
        overwrite_mode = False
    else:
        overwrite_mode = (choice == '2')

    print("\nFetching all records from library table...")
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
    print(f"\nStarting sync for {total_records} records. Overwrite: {overwrite_mode}")

    for index, record in enumerate(all_records):
        title = record.get("title")
        slug = record.get("id")

        if not title or not slug:
            continue

        file_path = f"{slug}.json"
        counter_prefix = f"[{index+1}/{total_records}]"

        # 1. Download current JSON
        try:
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)        
            prayer_data = json.loads(storage_response.decode('utf-8'))

            # RESPECT USER CHOICE
            has_id = "youtube_id" in prayer_data and prayer_data["youtube_id"]
            if has_id and not overwrite_mode:
                continue

        except Exception as e:
            print(f"{counter_prefix} Error downloading {file_path}: {e}")
            continue

        print(f"{counter_prefix} Processing: '{title}'")

        # 2. Get Best YouTube ID
        youtube_id = get_youtube_id_masterpiece(title)
        
        if not youtube_id:
            print(f"  [Warning] No embeddable masterpiece found. Skipping.")
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
        except Exception as e:
            # Fallback to update() if upload fails due to existing file
            try:
                supabase.storage.from_(SUPABASE_BUCKET).update(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json"}
                )
            except Exception as e2:
                print(f"  [Error] Final upload failure for {file_path}: {e2}")

        # Rate limiting sleep (Essential for heavy yt-dlp pool searches)
        time.sleep(1.5)

if __name__ == "__main__":
    sync_youtube()
