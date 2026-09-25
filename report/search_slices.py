"""
Search Marketplace vehicles in many narrow price slices, one browser, one slice
at a time, in one or more locations.

Facebook ignores any location in the search URL (zip, city slug and lat/long
all tested 2026-09-23) and always searches the account's saved location. So
each location is set through the page's "Change location" dialog, and the
account's original location is restored at the end.

Facebook also stops a vehicle search at about 45 results (seen 2026-09-22
evening and 2026-09-23; earlier the same search returned 400+). Each price
slice returns different cars, so narrow slices run in sequence cover the range.
Output columns match the scraper's CSV where the report tools need them.

Usage:
    python report/search_slices.py --places "Atlanta:60;Ellijay, Georgia:40" \
        --min 6000 --max 11000 --step 250 --max-miles 170000 \
        --min-year 2010 --max-year 2020 --out search_X.csv
"""
import argparse
import csv
import os
import re
import sys
import time
from urllib.parse import quote

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detail_pass import open_driver  # noqa: E402

CATEGORY_VEHICLES = '546583916084032'
STATE = re.compile(r', (?:GA|AL|TN|NC|SC|FL)$')
LOCATION_LABEL = "//span[contains(text(),' · ') and contains(text(),' mi')]"


def slice_url(lo, hi, a) -> str:
    return (f"https://www.facebook.com/marketplace/category/search/?query={quote(a.query)}"
            f"&category_id={CATEGORY_VEHICLES}&exact=false&minPrice={lo}&maxPrice={hi}"
            f"&maxMileage={a.max_miles}&minYear={a.min_year}&maxYear={a.max_year}")


def current_location(driver) -> str:
    """The saved-location label, e.g. 'Atlanta · 60 mi'."""
    driver.get('https://www.facebook.com/marketplace/category/vehicles')
    time.sleep(5)
    return driver.find_element(By.XPATH, LOCATION_LABEL).text


def set_location(driver, place: str, radius: int) -> str:
    """Set the account's Marketplace location through the Change location dialog."""
    current_location(driver)
    driver.find_element(By.XPATH, LOCATION_LABEL).click()
    time.sleep(2.5)
    dialog = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")[-1]
    box = dialog.find_element(By.CSS_SELECTOR, "input[aria-label='Location']")
    box.send_keys(Keys.CONTROL, 'a')
    box.send_keys(Keys.DELETE)
    box.send_keys(place)
    time.sleep(3)
    driver.find_elements(By.CSS_SELECTOR, "[role='option']")[0].click()
    time.sleep(1.5)
    dialog.find_element(By.XPATH, ".//*[@role='combobox' and contains(., 'miles')]").click()
    time.sleep(1.5)
    driver.find_element(By.XPATH, f"//*[@role='option' and contains(., '{radius} miles')]").click()
    time.sleep(1)
    dialog.find_element(By.XPATH, ".//*[@aria-label='Apply']").click()
    time.sleep(4)
    return current_location(driver)


def read_cards(driver) -> dict:
    """Every listing card on the page, keyed by listing id."""
    cards = {}
    for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']"):
        try:
            m = re.search(r'item/(\d+)', a.get_attribute('href') or '')
            if not m or m.group(1) in cards:
                continue
            lines = [l.strip() for l in a.text.split('\n') if l.strip()]
            img = a.find_elements(By.TAG_NAME, 'img')
            cards[m.group(1)] = {
                'Listing_URL': f"https://www.facebook.com/marketplace/item/{m.group(1)}/",
                'Price': next((l for l in lines if l.startswith('$') or l == 'FREE'), ''),
                'Title': next((l for l in lines if re.match(r'(19|20)\d{2} ', l)), ''),
                'City': next((l for l in lines if STATE.search(l)), ''),
                'Mileage': next((l for l in lines if 'miles' in l.lower()), ''),
                'Image_URLs': img[0].get_attribute('src') if img else '',
                'Description': '',
            }
        except Exception:
            continue  # card re-rendered while being read
    return cards


def scroll_slice(driver, url: str, max_rounds: int = 10) -> dict:
    driver.get(url)
    time.sleep(5)
    found, stale = {}, 0
    for _ in range(max_rounds):
        before = len(found)
        found.update(read_cards(driver))
        stale = stale + 1 if len(found) == before else 0
        if stale >= 2:
            break
        driver.execute_script('window.scrollBy(0, 2200)')
        time.sleep(2.5)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--query', default='Vehicles',
                    help='search text, e.g. "Tesla Model 3"; a model name returns only that model')
    ap.add_argument('--places', required=True,
                    help='semicolon-separated "place:radius", e.g. "Atlanta:60;Ellijay, Georgia:40"')
    ap.add_argument('--min', type=int, required=True)
    ap.add_argument('--max', type=int, required=True)
    ap.add_argument('--step', type=int, default=250)
    ap.add_argument('--max-miles', type=int, default=200000)
    ap.add_argument('--min-year', type=int, default=2003)
    ap.add_argument('--max-year', type=int, default=2020)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    results = {}
    driver = open_driver()
    home = None
    try:
        home = current_location(driver)
        print(f"saved location before run: {home}", flush=True)
        for spec in [p.strip() for p in a.places.split(';') if p.strip()]:
            place, radius = spec.rsplit(':', 1)
            loc = set_location(driver, place.strip(), int(radius))
            print(f"location set: {loc}", flush=True)
            for lo in range(a.min, a.max, a.step):
                hi = min(lo + a.step - 1, a.max)
                cards = scroll_slice(driver, slice_url(lo, hi, a))
                new = 0
                for lid, c in cards.items():
                    if lid not in results:
                        results[lid] = {**c, 'Search_Location': loc}
                        new += 1
                print(f"{loc} ${lo}-{hi}: {len(cards)} cards, {new} new, {len(results)} total", flush=True)
    finally:
        if home:
            try:
                place, radius = re.match(r'(.+) · (\d+) mi', home).groups()
                print(f"restored location: {set_location(driver, place, int(radius))}", flush=True)
            except Exception as e:
                print(f"COULD NOT RESTORE LOCATION (was {home}): {e}", flush=True)
        driver.quit()

    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['Listing_URL', 'Price', 'Title', 'City', 'Mileage',
                                          'Image_URLs', 'Description', 'Search_Location'])
        w.writeheader()
        w.writerows(results.values())
    print(f"{len(results)} listings -> {a.out}")


if __name__ == "__main__":
    main()
