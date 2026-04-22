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

# Generic words that often cause false positives
GENERIC_BLACKLIST = {
    'stotram', 'stotra', 'suktam', 'sahasranamam', 'ashtottara', 
    'satanama', 'shatanama', 'namavali', 'chalisa', 'kavacham', 
    'kavach', 'mantra', 'mantram', 'sloka', 'parayana'
}

def get_keywords(text):
    """
    Extracts high-value identifying keywords.
    - Filters words <= 3 chars.
    - Filters generic religious terms.
    """
    # All significant words (lowercase, > 3 chars)
    all_words = [w for w in re.findall(r'\w+', text.lower()) if len(w) > 3]
    # Filtered unique keywords (not in blacklist)
    unique_keywords = [w for w in all_words if w not in GENERIC_BLACKLIST]
    
    return unique_keywords, all_words

def get_youtube_id_masterpiece(title_english):
    """
    Search for top 15 results.
    Apply Brutal Guardrail: 
    - If unique keywords exist, YT title MUST contain at least one.
    - If title is purely generic, YT title MUST contain ALL original words.
    - Winner: Highest view count among embeddable/public videos.
    """
    query = f'"{title_english}"'
    search_query = f"ytsearch15:{query}"
    
    unique_keywords, all_words = get_keywords(title_english)
    
    try:
        # Fetch metadata pool with embeddability filter
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
                
                v_id = v.get('id')
                v_title = v.get('title', '').lower()
                v_views = v.get('view_count') or 0
                
                # 1. Availability Check
                if v.get('availability') and v.get('availability') != 'public':
                    continue
                
                # 2. Brutal Guardrail Logic
                if unique_keywords:
                    # Must contain at least one unique identifier (e.g., 'annapurna')
                    if not any(k in v_title for k in unique_keywords):
                        continue
                    if 'chalisa' in all_words and 'chalisa' not in v_title:
                        continue
                    if 'kavach' in all_words and 'kavach' not in v_title and 'kavacham' not in v_title:
                        continue
                    if 'suktam' in all_words and 'suktam' not in v_title and 'sukta' not in v_title:
                        continue
                else:
                    # If the title was purely generic (e.g. "Stotram Mantra"), 
                    # require ALL words to be present to be safe.
                    if not all(w in v_title for w in all_words):
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

        # 3. Pick the Winner (Highest view count)
        winner = max(valid_pool, key=lambda x: x['view_count'])
        
        print(f"  [Success] Found: {winner['title']} | {winner['view_count']:,} views | ID: {winner['id']}")
        return winner['id']

    except Exception as e:
        print(f"  [Error] Search failed for '{title_english}': {e}")
    return None

def sync_youtube():
    print("\n" + "="*50)
    print(" POOJA ROOM BRUTAL SYNC: MASTERPIECE EDITION ")
    print("="*50)
    print(" (1) Skip records with existing YouTube IDs")
    print(" (2) Overwrite all existing IDs (Force Sync)")
    choice = input("\nChoice (1/2): ").strip()
    
    overwrite_mode = (choice == '2')

    print("\nConnecting to database...")
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
            print(f"Connection Error: {e}")
            return

    total = len(all_records)
    print(f"Syncing {total} records. Overwrite: {overwrite_mode}")

    for index, record in enumerate(all_records):
        title = record.get("title")
        slug = record.get("id")
        if not title or not slug: continue

        file_path = f"{slug}.json"
        counter = f"[{index+1}/{total}]"

        try:
            storage_res = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)
            prayer_data = json.loads(storage_res.decode('utf-8'))
            
            if not overwrite_mode and prayer_data.get("youtube_id"):
                continue
        except Exception:
            continue

        print(f"{counter} Processing: '{title}'")

        yt_id = get_youtube_id_masterpiece(title)
        
        if not yt_id:
            print(f"  [Skip] No valid/unique version found.")
            continue

        prayer_data["youtube_id"] = yt_id
        try:
            updated_json = json.dumps(prayer_data, ensure_ascii=False, indent=2).encode('utf-8')
            try:
                supabase.storage.from_(SUPABASE_BUCKET).update(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json"}
                )
            except Exception:
                supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=file_path,
                    file=updated_json,
                    file_options={"content-type": "application/json", "x-upsert": "true"}
                )
        except Exception as e:
            print(f"  [Error] Save failed for {file_path}: {e}")

        time.sleep(1.5)

if __name__ == "__main__":
    sync_youtube()
