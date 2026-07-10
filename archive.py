import os
import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration - Add more URLs and paths here
CONFIG = {
    'sources': [
        {
            'url': 'https://raw.githubusercontent.com/VPNforWindowsSub/configs/refs/heads/master/Eternity.txt',
            'path': 'update',
            'name': 'eternity'
        },
        {
            'url': 'https://raw.githubusercontent.com/VPNforWindowsSub/configs/refs/heads/master/Diversity.txt',
            'path': 'div',
            'name': 'diversity'
        },
        # Add more sources here
    ],
    'retry_attempts': 3,
    'retry_delay': 5,  # seconds
}

def fetch_url_with_retry(url, max_retries=3, delay=5):
    """Fetch URL with retry mechanism"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    return None

def fetch_all_sources(sources):
    """Fetch all sources concurrently"""
    results = {}
    
    with ThreadPoolExecutor(max_workers=min(10, len(sources))) as executor:
        future_to_source = {
            executor.submit(fetch_url_with_retry, source['url'], 
                          CONFIG['retry_attempts'], CONFIG['retry_delay']): source 
            for source in sources
        }
        
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                data = future.result()
                if data:
                    results[source['name']] = {
                        'data': data,
                        'source': source
                    }
                else:
                    print(f"Failed to fetch {source['name']} from {source['url']}")
            except Exception as e:
                print(f"Error fetching {source['name']}: {str(e)}")
    
    return results

def backup(data, update_path, source_name):
    """Backup data to file"""
    date_dir = datetime.now().strftime("%Y%m")
    full_path = f"./{update_path}/{date_dir}"
    
    try:
        os.makedirs(full_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating backup directory for {source_name}: {e}")
        return False
    
    date_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{full_path}/{date_file}_{source_name}.txt"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"✓ Backed up {source_name} to {file_path}")
        return True
    except OSError as e:
        print(f"Error writing backup file for {source_name}: {e}")
        return False

def main():
    """Run backup once"""
    print(f"🚀 Starting backup for {len(CONFIG['sources'])} sources...")
    start_time = time.time()
    
    # Fetch all sources concurrently
    results = fetch_all_sources(CONFIG['sources'])
    
    if results:
        # Backup each successful fetch
        success_count = 0
        for name, result in results.items():
            source = result['source']
            data = result['data']
            
            if backup(data, source['path'], name):
                success_count += 1
        
        elapsed = time.time() - start_time
        print(f"✅ Backed up {success_count}/{len(CONFIG['sources'])} sources in {elapsed:.2f}s")
    else:
        print("❌ No data was successfully fetched")
    
    print("🏁 Backup completed")

if __name__ == "__main__":
    main()
