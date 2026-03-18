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
        "User-Agent": "Mozilla/5.0"
    }
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_clean_title(url):
    try:
        parts = url.strip("/").split("/")
        series = parts[-2].replace('-', ' ').title()
        chapter = parts[-1].replace('-', ' ').title()
        return f"{series} - {chapter}"
    except:
        return f"Comic_Chapter_{int(time.time())}"

def download_chapter(target_url):
    nice_title = get_clean_title(target_url)
    print(f"\n[*] Processing: {nice_title}")
    
    try:
        start_res = make_request(f"{API_BASE}/extractions", method="POST", data={"url": target_url})
        extraction_id = start_res['data']['id']

        status = "pending"
        images = []
        while status not in ["done", "error"]:
            time.sleep(3) 
            poll_res = make_request(f"{API_BASE}/extractions/{extraction_id}")
            status = poll_res['data']['status']
            if status == "done":
                images = poll_res['data']['images']

        if not images:
            print(f"    [!] No images found for {nice_title}")
            return

        cbz_filename = f"{nice_title}.cbz".replace(" ", "_").replace("/", "-")
        
        with zipfile.ZipFile(cbz_filename, 'w') as zip_file:
            for i, img_data in enumerate(images):
                img_url = img_data['url']
                print(f"    -> [{i+1:02d}/{len(images):02d}] Downloading...", end="\r")
                
                try:
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://comix.to/"})
                    with urllib.request.urlopen(img_req) as img_res:
                        ext = img_url.split('.')[-1].split('?')[0] if '.' in img_url else 'jpg'
                        zip_file.writestr(f"{i+1:03d}.{ext}", img_res.read())
                except:
                    continue

        print(f"\n[+] Saved: {cbz_filename}")
        time.sleep(2)

    except Exception as e:
        print(f"\n[!] Failed {nice_title}: {e}")

def run_script():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("====================================================")
        print("[!] ERROR: API KEY MISSING")
        print("    Please open this file in Notepad and paste your")
        print("    extract.pics API key into the API_KEY variable.")
        print("====================================================")
        return

    print("Paste all links (separated by spaces) then press Enter:")
    user_input = input("> ").strip()
    
    urls = user_input.split()
    if not urls:
        print("[!] No links provided.")
        return
        
    print(f"\n[!] Batch mode started. {len(urls)} chapters in queue.")
    
    for url in urls:
        if "comix.to" in url:
            download_chapter(url)
    
    print("\n[=== ALL DOWNLOADS COMPLETE ===]")

if __name__ == "__main__":
    try:
        run_script()
    except Exception as fatal_error:
        print("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"CRITICAL ERROR: {fatal_error}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
    # This ensures the window stays open NO MATTER WHAT
    input("\nPress Enter to close this window...")
