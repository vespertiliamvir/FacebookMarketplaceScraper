"""
Revisit listing pages in the logged-in Master Profile and save each page's own
text, plus the seller's Marketplace profile (rating, active listings, reviews).

The scraper's description step picks up text from the "related listings" panel.
This pass reads the listing page itself and cuts before that panel, so the
"About this vehicle" block (mileage, title status, owners) and the seller's
join date come through clean. Each seller profile is fetched once, even when
the seller has several listings in the shortlist. Resumable: saved ids are skipped.

Usage:
    python report/detail_pass.py <shortlist.csv with an 'id' or 'Listing_URL' column> <out.json>
Writes <out.json> (listings) and <out>.profiles.json (sellers).
"""
import csv
import json
import os
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

MASTER_PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".facebook_scraper_master_profile")

# The listing's own text ends where one of these panels begins
CUT_MARKERS = ("Today's picks", "Sponsored", "More from this seller", "Related listings",
               "Similar vehicles", "Browse more", "See all")


def open_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={MASTER_PROFILE_DIR}")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def listing_id(row: dict) -> str:
    if row.get('id'):
        return row['id']
    return re.search(r'item/(\d+)', row['Listing_URL']).group(1)


def read_listing(driver, lid: str) -> dict:
    driver.get(f"https://www.facebook.com/marketplace/item/{lid}/")
    time.sleep(3.5)
    for el in driver.find_elements(By.XPATH, "//*[text()='See more']")[:2]:
        try:
            el.click()
            time.sleep(0.6)
        except Exception:
            pass
    text = driver.find_element(By.TAG_NAME, 'body').text
    cut = min([text.find(m) for m in CUT_MARKERS if text.find(m) > 0] or [len(text)])
    profiles = [a.get_attribute('href').split('?')[0]
                for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/profile/']")]
    return {'url': driver.current_url, 'text': text[:cut][:6000],
            'profile_url': profiles[0] if profiles else None}


def read_profile(driver, url: str) -> str:
    """The seller's Marketplace profile, from the rating header through the reviews."""
    driver.get(url)
    time.sleep(4.5)
    text = driver.find_element(By.TAG_NAME, 'body').text
    # The page opens with the viewer's feed; the seller's card starts at the rating line
    start = re.search(r'\n\d\.\d \(\d+\)\n|\nNo ratings yet\n|\nJoined Facebook in', text)
    end = text.find('Things in common')
    if end < 0:
        end = len(text)
    return text[(start.start() if start else 0):end][:8000]


def main(src: str, out: str) -> None:
    profiles_out = out.replace('.json', '.profiles.json')
    rows = list(csv.DictReader(open(src, encoding='utf-8')))
    done = json.load(open(out)) if os.path.exists(out) else {}
    profiles = json.load(open(profiles_out)) if os.path.exists(profiles_out) else {}

    driver = open_driver()
    try:
        for i, row in enumerate(rows, 1):
            lid = listing_id(row)
            if lid not in done or 'profile_url' not in done[lid]:  # older runs lack the profile link
                done[lid] = read_listing(driver, lid)
                json.dump(done, open(out, 'w'), indent=1)
            purl = done[lid].get('profile_url')
            if purl and purl not in profiles:
                profiles[purl] = read_profile(driver, purl)
                json.dump(profiles, open(profiles_out, 'w'), indent=1)
            print(f"[{i}/{len(rows)}] {lid}", flush=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
