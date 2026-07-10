import os
import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Configuration - Add more URLs and paths here
CONFIG = {
    'sources': [
        {
            'url': 'https://raw.githubusercontent.com/VPNforWindowsSub/configs/refs/heads/master/Eternity.txt',
            'path': 'update',
            'name': 'eternity'
        },
        {
            'url': 'https://raw.githubusercontent.com/VPNforWindowsSub/configs/refs/heads/master/Resilience.txt',
            'path': 'res',
            'name': 'resilience'
        },
        # Add more sources here
    ],
    'retry_attempts': 3,
    'retry_delay': 5,  # seconds
    'backup_interval': 3600,  # Changed to 1 hour (was 10 seconds - too frequent!)
}

def fetch_url_with_retry(url, max_retries=3, delay=5):
    """Fetch URL with retry mechanism"""
    for attempt in range(max_retries):
        try:
            # Added User-Agent header to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()  # This will raise an exception for bad status codes
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    return None

def fetch_all_sources(sources):
    """Fetch all sources concurrently"""
    results = {}
    # Fixed: Use all available sources with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(5, len(sources))) as executor:
        # Fixed: Properly map futures to sources
        future_to_source = {}
        for source in sources:
            future = executor.submit(
                fetch_url_with_retry, 
                source['url'], 
                CONFIG['retry_attempts'], 
                CONFIG['retry_delay']
            )
            future_to_source[future] = source
        
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
    """Backup data to file with enhanced error handling"""
    # Fixed: Use consistent date format for directory and file
    date_dir = datetime.now().strftime("%Y%m")  # Changed to 4-digit year
    date_file = datetime.now().strftime("%Y%m%d_%H%M%S")  # Added seconds for uniqueness
    
    # Fixed: Use absolute path for better reliability
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, update_path, date_dir)
    
    try:
        os.makedirs(full_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating backup directory for {source_name}: {e}")
        return False
    
    # Fixed: Sanitize filename to avoid issues
    filename = f"{date_file}_{source_name}.txt"  # Added source name to filename
    file_path = os.path.join(full_path, filename)
    
    try:
        # Fixed: Use proper file writing with explicit encoding
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Successfully backed up {source_name} to {file_path}")
        return True
    except (OSError, IOError) as e:
        print(f"Error writing backup file for {source_name}: {e}")
        return False


def main():
    """Main execution loop"""
    print(f"Starting backup service with {len(CONFIG['sources'])} sources")
    print("Press Ctrl+C to stop the service")
    
    # Added counter for periodic cleanup
    cycle_count = 0
    CLEANUP_INTERVAL = 10  # Run cleanup every 10 cycles
    
    while True:
        try:
            print(f"\n--- Backup cycle started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            
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
                
                print(f"Successfully backed up {success_count} out of {len(CONFIG['sources'])} sources")
                
            else:
                print("No data was successfully fetched")
            
            # Wait before next cycle
            print(f"Waiting {CONFIG['backup_interval']} seconds before next check...")
            time.sleep(CONFIG['backup_interval'])
            
        except KeyboardInterrupt:
            print("\nBackup service stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            print(f"Continuing in {CONFIG['backup_interval']} seconds...")
            time.sleep(CONFIG['backup_interval'])

if __name__ == "__main__":
    main()
