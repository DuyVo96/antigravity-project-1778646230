import requests
import json
import re
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

def load_config():
    if not os.path.exists("config.json"):
        raise FileNotFoundError("config.json not found.")
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def validate_url(url):
    if not url or not url.strip():
        return False, "URL is empty"
    
    url = url.strip()
    
    # Accept Pinterest and direct pinimg URLs
    valid_domains = ['pinterest.com', 'pin.it', 'i.pinimg.com', 'pinimg.com']
    if not any(domain in url for domain in valid_domains):
        return False, f"Not a Pinterest URL: {url[:50]}..."
    
    # Try to parse as URL
    try:
        result = urlparse(url)
        if not result.scheme:
            return False, f"Missing scheme (http/https): {url[:50]}..."
        if result.scheme not in ['http', 'https']:
            return False, f"Invalid scheme: {result.scheme}"
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"
    
    return True, url

def upgrade_url_quality(url):
    high_res_url = re.sub(r'/(?:736x|236x|400x|564x|1200x)/', '/originals/', url)
    return high_res_url

def download_image(url, filename, folder, timeout=30, max_retries=3):
    try:
        Path(folder).mkdir(parents=True, exist_ok=True)
        
        # Validate URL
        is_valid, msg = validate_url(url)
        if not is_valid:
            return None, f"Invalid URL: {msg}"
        
        url = url.strip()
        high_res_url = upgrade_url_quality(url)
        
        # Try high-res version first
        for attempt in range(max_retries):
            try:
                response = requests.get(high_res_url, stream=True, timeout=timeout)
                
                # If originals are blocked, fall back to 736x
                if response.status_code == 403 and high_res_url != url:
                    fallback_url = re.sub(r'/originals/', '/736x/', high_res_url)
                    response = requests.get(fallback_url, stream=True, timeout=timeout)
                
                if response.status_code == 200:
                    filepath = f"{folder}/{filename}.jpg"
                    
                    # Validate file write permissions
                    try:
                        with open(filepath, "wb") as f:
                            for chunk in response.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                    except IOError as e:
                        return None, f"Cannot write file: {e}"
                    
                    # Validate file was created and has content
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        return filepath, None
                    else:
                        return None, f"File empty or not created"
                
                elif response.status_code == 404:
                    return None, f"URL not found (404): {url[:50]}..."
                elif response.status_code in [403, 401]:
                    return None, f"Access denied ({response.status_code})"
                else:
                    if attempt < max_retries - 1:
                        continue
                    return None, f"HTTP {response.status_code}"
            
            except requests.Timeout:
                if attempt < max_retries - 1:
                    continue
                return None, "Request timeout"
            except requests.ConnectionError as e:
                if attempt < max_retries - 1:
                    continue
                return None, f"Connection error: {str(e)[:50]}"
        
        return None, "Max retries exceeded"
    
    except Exception as e:
        return None, f"Unexpected error: {str(e)[:100]}"

def main():
    try:
        config = load_config()
        links_file = config['paths']['links_file']
        config_file = config['paths']['config_file']
        niche = config['niche']
        folder = f"{config['paths']['images_dir']}/{niche}"
        max_workers = config['download']['max_workers']
        timeout = config['download']['timeout_seconds']
        
        # 1. Read URLs
        if not os.path.exists(links_file):
            print(f"⚠️  Creating {links_file}...")
            Path(links_file).touch()
            print(f"✏️  Add Pinterest image URLs (one per line) and run again")
            sys.exit(0)
        
        with open(links_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            print(f"⚠️  {links_file} is empty! Add Pinterest URLs (one per line)")
            sys.exit(0)
        
        print(f"🔍 Found {len(urls)} URLs. Validating...")
        
        # 2. Validate URLs
        valid_urls = []
        invalid_urls = []
        
        for i, url in enumerate(urls):
            is_valid, msg = validate_url(url)
            if is_valid:
                valid_urls.append((i, upgrade_url_quality(url)))
            else:
                invalid_urls.append((i+1, url[:60], msg))
        
        if invalid_urls:
            print(f"\n⚠️  Invalid URLs found ({len(invalid_urls)}):")
            for line_num, url, reason in invalid_urls[:5]:  # Show first 5
                print(f"  Line {line_num}: {url}... → {reason}")
            if len(invalid_urls) > 5:
                print(f"  ... and {len(invalid_urls) - 5} more")
        
        if not valid_urls:
            print("❌ No valid URLs to download!")
            sys.exit(1)
        
        print(f"✅ {len(valid_urls)} valid URLs to download\n")
        
        # 3. Download with parallel workers
        downloaded_paths = {}
        failed_downloads = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for orig_idx, url in valid_urls:
                filename = f"image_{orig_idx+1:03d}"
                future = executor.submit(download_image, url, filename, folder, timeout)
                futures[future] = (orig_idx, filename, url)
            
            completed = 0
            for future in as_completed(futures):
                orig_idx, filename, url = futures[future]
                completed += 1
                
                try:
                    filepath, error = future.result()
                    if error:
                        failed_downloads.append((orig_idx+1, url[:50], error))
                        print(f"❌ [{completed}/{len(valid_urls)}] {filename}: {error}")
                    else:
                        downloaded_paths[orig_idx] = f"./{filepath}"
                        print(f"✅ [{completed}/{len(valid_urls)}] {filepath}")
                except Exception as e:
                    failed_downloads.append((orig_idx+1, url[:50], str(e)))
                    print(f"❌ [{completed}/{len(valid_urls)}] {filename}: {str(e)[:80]}")
        
        if not downloaded_paths:
            print("\n❌ No images downloaded successfully!")
            sys.exit(1)
        
        print(f"\n✅ Downloaded {len(downloaded_paths)} images")
        
        if failed_downloads:
            print(f"⚠️  Failed: {len(failed_downloads)} images")
            for line_num, url, error in failed_downloads[:3]:
                print(f"  Line {line_num}: {url}... → {error}")
        
        # 4. Inject paths into config
        if not os.path.exists(config_file):
            print(f"\n❌ {config_file} not found! Run 'build_config.py' first")
            sys.exit(1)
        
        with open(config_file, "r", encoding="utf-8") as f:
            slides_config = json.load(f)
        
        updated_count = 0
        for i, slide in enumerate(slides_config):
            if i in downloaded_paths:
                old_path = slide.get("imagePath", "")
                new_path = downloaded_paths[i]
                slide["imagePath"] = new_path
                if old_path != new_path:
                    updated_count += 1
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(slides_config, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Updated {updated_count} slides in {config_file}")
        print(f"\n🎉 Complete! Ready to generate slides with 'generate-slides.js'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
