import os
import time
import json
import subprocess
import re
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

def get_keywords(text):
    """Extract words longer than 3 letters for the title guardrail."""
    # Remove special characters and split into lowercase words
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if len(w) > 3]

def get_youtube_id_masterpiece(title_english):
    """
    Find the ultimate version of a prayer:
    - Strict Exact Match Query
    - Search pool of 15 results
    - Filter for public availability & embeddability
    - Guardrail: Title must contain at least one keyword from the database title
    - Winner: Highest view count
    """
    # Strict Exact Match Search
    query = f'"{title_english}"'
    search_query = f"ytsearch15:{query}"
    
    # Pre-extract keywords for guardrail
    keywords = get_keywords(title_english)
    
    try:
        # Command: yt-dlp with dump-json and strict embeddability filter
        result = subprocess.run(
            [
                "yt-dlp", 
                "--dump-json", 
                "--flat-playlist", 
                "--match-filter", "allows_embedding",
                search_query
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=90
        )
        
        valid_pool = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            try:
                v = json.loads(line)
                
                # 1. Basic Metadata
                v_id = v.get('id')
                v_title = v.get('title', '').lower()
                v_views = v.get('view_count') or 0
                
                # 2. Availability Check
                if v.get('availability') and v.get('availability') != 'public':
                    continue
                
                # 3. Guardrail: Keyword Check
                # The YT title MUST contain at least one word (>3 chars) from the original title
                if keywords and not any(k in v_title for k in keywords):
                    continue
                
                valid_pool.append({
                    'id': v_id,
                    'title': v.get('title'),
                    'view_count': v_views
                })
            except json.JSONDecodeError:
                continue

        if not valid_pool:
            return None

        # 4. Pick the Winner (Highest view count)
        winner = max(valid_pool, key=lambda x: x['view_count'])
        
        print(f"  [Success] Found: {winner['title']} | {winner['view_count']:,} views | ID: {winner['id']}")
        return winner['id']

    except Exception as e:
        print(f"  [Error] Masterpiece search failed for '{title_english}': {e}")
    return None

def sync_youtube():
    # User Input Prompt
    print("\n" + "="*50)
    print(" POOJA ROOM ULTIMATE YOUTUBE SYNC ")
    print("="*50)
    print(" (1) Skip records with existing YouTube IDs")
    print(" (2) Overwrite all existing IDs (Force Sync)")
    choice = input("\nChoice (1/2): ").strip()
    
    overwrite_mode = (choice == '2')

    print("\nFetching library metadata...")
    all_records = []
    start = 0
    page_size = 1000

    while True:
        try:
            response = supabase.table("library").select("*").range(start, start + page_size - 1).execute()
            batch = response.data
            if not batch: break
            all_records.extend(batch)
            if len(batch) < page_size: break
            start += page_size
        except Exception as e:
            print(f"Error connecting to Supabase: {e}")
            return

    total = len(all_records)
    print(f"Starting sync for {total} records. Overwrite: {overwrite_mode}")

    for index, record in enumerate(all_records):
        title = record.get("title")
        slug = record.get("id")
        if not title or not slug: continue

        file_path = f"{slug}.json"
        counter = f"[{index+1}/{total}]"

        # 1. Download & Skip Check
        try:
            storage_res = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)
            prayer_data = json.loads(storage_res.decode('utf-8'))
            
            if not overwrite_mode and prayer_data.get("youtube_id"):
                continue
        except Exception:
            # Silent skip if file missing
            continue

        print(f"{counter} Processing: '{title}'")

        # 2. Find Masterpiece
        yt_id = get_youtube_id_masterpiece(title)
        
        if not yt_id:
            print(f"  [Skip] No valid/embeddable version found.")
            continue

        # 3. Update & Upload
        prayer_data["youtube_id"] = yt_id
        try:
            updated_json = json.dumps(prayer_data, ensure_ascii=False, indent=2).encode('utf-8')
            # Attempt update first for speed
            try:
                supabase.storage.from_(SUPABASE_BUCKET).update(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json"}
                )
            except Exception:
                # Fallback to upsert upload
                supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json", "x-upsert": "true"}
                )
        except Exception as e:
            print(f"  [Error] Failed to save {file_path}: {e}")

        # 4. Rate Limiting
        time.sleep(1.5)

if __name__ == "__main__":
    sync_youtube()
