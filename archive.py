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
            'url': 'https://raw.githubusercontent.com/VPNforWindowsSub/configs/refs/heads/master/Resilience.txt',
            'path': 'Res',
            'name': 'resilience'
        },
        # Add more sources here
    ],
    'retry_attempts': 3,
    'retry_delay': 5,  # seconds
    'backup_interval': 10,  # seconds between checks
}

def fetch_url_with_retry(url, max_retries=3, delay=5):
    """Fetch URL with retry mechanism"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            if response.ok:
                return response.text
            else:
                print(f"Attempt {attempt + 1} failed for {url}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(delay)
    
    return None

def fetch_all_sources(sources):
    """Fetch all sources concurrently"""
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(fetch_url_with_retry, source['url'], 
                          CONFIG['retry_attempts'], CONFIG['retry_delay']): source 
            for source in sources
        }
        
        for future in as_completed(future_to_url):
            source = future_to_url[future]
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
    date_dir = datetime.now().strftime("%y%m")
    date_file = datetime.now().strftime("%y%m%d_%H%M")
    
    # Create full path with source name for better organization
    full_path = f"./{update_path}/{date_dir}"
    
    try:
        os.makedirs(full_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating backup directory for {source_name}: {e}")
        return False
    
    file_path = f"{full_path}/{date_file}.txt"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Successfully backed up {source_name} to {file_path}")
        return True
    except OSError as e:
        print(f"Error writing backup file for {source_name}: {e}")
        return False

def main():
    """Main execution loop"""
    print(f"Starting backup service with {len(CONFIG['sources'])} sources")
    
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
            break
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            time.sleep(CONFIG['backup_interval'])

if __name__ == "__main__":
    main()
