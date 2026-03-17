import sys
import json
import time
import urllib.request
import zipfile
import os

# === PASTE YOUR API KEY HERE ===
API_KEY = "YOUR_API_KEY_HERE" 
# ===============================

API_BASE = "https://api.extract.pics/v0"

def make_request(url, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_clean_title(url):
    try:
        parts = url.strip("/").split("/")
        series = parts[-2].split('-', 1)[-1].replace('-', ' ').title()
        chapter = parts[-1].split('-', 1)[-1].replace('-', ' ').title()
        return f"{series} - {chapter}"
    except:
        return "Comic_Chapter"

def main():
    print("=======================================")
    print("       Comix.to CBZ Downloader         ")
    print("=======================================\n")

    if API_KEY == "YOUR_API_KEY_HERE":
        print("[!] ERROR: Please paste your extract.pics API key into the script.")
        input("Press Enter to exit...")
        return

    # Get URL from command line or ask the user
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = input("Paste the comix.to chapter URL: ").strip()

    if not target_url.startswith("http"):
        print("[!] Invalid URL.")
        return

    nice_title = get_clean_title(target_url)
    print(f"\n[*] Target: {nice_title}")
    
    try:
        # 1. Start API Extraction
        print("[*] Bypassing Cloudflare and scanning for images...")
        start_res = make_request(f"{API_BASE}/extractions", method="POST", data={"url": target_url})
        extraction_id = start_res['data']['id']

        # 2. Polling for completion
        status = "pending"
        images = []
        while status not in ["done", "error"]:
            time.sleep(3) 
            poll_res = make_request(f"{API_BASE}/extractions/{extraction_id}")
            status = poll_res['data']['status']
            if status == "done":
                images = poll_res['data']['images']

        if not images:
            raise Exception("No images found on the page.")

        total_images = len(images)
        print(f"[*] Success! Found {total_images} pages.")

        # 3. Setup File Path (Saves in the folder where you run the script)
        current_dir = os.getcwd()
        cbz_filename = f"{nice_title}.cbz".replace(" ", "_")
        cbz_path = os.path.join(current_dir, cbz_filename)

        print(f"[*] Downloading and packaging into: {cbz_filename}")

        # 4. Download and Zip
        with zipfile.ZipFile(cbz_path, 'w') as zip_file:
            for i, img_data in enumerate(images):
                img_url = img_data['url']
                
                # Print progress (e.g., [ 5/32] Downloading...)
                print(f"    -> [{i+1:02d}/{total_images:02d}] Downloading page...", end="\r")
                
                try:
                    img_req = urllib.request.Request(img_url)
                    img_req.add_header("User-Agent", "Mozilla/5.0")
                    img_req.add_header("Referer", "https://comix.to/") 
                    
                    with urllib.request.urlopen(img_req) as img_res:
                        # Determine extension, default to jpg
                        ext = "jpg"
                        if "." in img_url.split('/')[-1]:
                            ext = img_url.split('/')[-1].split('.')[-1].split('?')[0]
                        
                        zip_file.writestr(f"{i+1:03d}.{ext}", img_res.read())
                except Exception as e:
                    print(f"\n    [!] Failed to download page {i+1}: {e}")

        print(f"\n\n[+] DONE! Saved to: {cbz_path}")

    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")

    if len(sys.argv) == 1:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()