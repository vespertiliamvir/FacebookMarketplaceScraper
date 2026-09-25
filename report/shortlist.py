"""
First-pass filter over a scrape CSV: reliable models, private sellers,
established profiles, no salvage / not-running / financing-bait wording.
Optionally narrows by price and card mileage, and caps the list so the
detail pass (two page loads per car) stays a reasonable size.

The output feeds detail_pass.py, which re-reads each listing page.

Usage:
    python report/shortlist.py <scrape.csv> <shortlist.csv>
        [--min-price 4000] [--max-price 6000] [--max-miles 170000] [--cap 120]
"""
import argparse
import re

import pandas as pd

RELIABLE = (r'toyota (?:corolla|camry|yaris|prius|matrix|echo|rav4)|honda (?:civic|accord|fit|cr-v|crv|insight)'
            r'|mazda (?:mazda3|mazda6|3|6|cx-5|mx-5|miata)\b|mx-5|miata|scion x[abd]|pontiac vibe'
            r'|hyundai elantra|lexus (?:es|is)\b'
            r'|subaru (?:impreza|crosstrek|xv|outback|forester|legacy)')

PRIORITY = {'toyota corolla', 'honda civic', 'mazda mazda3', 'mazda 3'}

# Subaru's 2.5 EJ engines before the 2012 FB redesign are known for head-gasket failures
OLD_SUBARU = r'\b(?:19\d\d|200\d|201[01]) subaru'

BAD_WORDING = (r'salvage|rebuilt|rebuild|reconstructed|not running|doesn.t run|does not run'
               r'|needs (?:a )?(?:motor|engine|transmission|trans)|for parts|parts car|blown|mechanic special'
               r'|down payment|buy here|bhph|no credit|overheat|check engine|flood')


def card_miles(v) -> float:
    """'120K miles' / '120,000 miles' -> 120000; unknown -> NaN."""
    m = re.search(r'([\d,.]+)\s*([kK])?\s*mi', str(v))
    if not m:
        return float('nan')
    n = float(m.group(1).replace(',', ''))
    return n * 1000 if m.group(2) else n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scrape')
    ap.add_argument('out')
    ap.add_argument('--newest-profile', type=int, default=2022,
                    help='drop sellers who joined Facebook after this year')
    ap.add_argument('--min-price', type=float)
    ap.add_argument('--max-price', type=float)
    ap.add_argument('--max-miles', type=float, help='drop cars whose result card shows more miles')
    ap.add_argument('--cap', type=int, help='keep only this many, newest and lowest-mileage first')
    a = ap.parse_args()

    d = pd.read_csv(a.scrape)
    d['id'] = d['Listing_URL'].str.extract(r'item/(\d+)')[0]
    d = d.drop_duplicates('id')
    print(f"{len(d)} unique listings")

    d['price'] = pd.to_numeric(d['Price'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
    if a.min_price:
        d = d[d['price'] >= a.min_price]
    if a.max_price:
        d = d[d['price'] <= a.max_price]

    title = d['Title'].str.lower().fillna('')
    d = d[title.str.contains(RELIABLE) & ~title.str.contains(OLD_SUBARU)]
    print(f"{len(d)} reliable models in range")

    text = (d['Title'].fillna('') + ' ' + d['Description'].fillna('')).str.lower()
    d = d[~text.str.contains(BAD_WORDING)]
    # Seller columns exist only when the scraper's description step was on
    if 'Seller_Type' in d:
        d = d[~d['Seller_Type'].isin(['Dealer/Business', 'Suspected Dealer'])]
    if 'Profile_Age' in d and d['Profile_Age'].notna().any():
        d = d[d['Profile_Age'].isna() | (d['Profile_Age'] <= a.newest_profile)]

    d['card_miles'] = d['Mileage'].map(card_miles)
    if a.max_miles:
        d = d[d['card_miles'].isna() | (d['card_miles'] <= a.max_miles)]
    print(f"{len(d)} after wording, seller and mileage filters")

    if a.cap and len(d) > a.cap:
        # Take turns across models so one common model can't fill the list,
        # newest and lowest-mileage first within each model
        d['year'] = pd.to_numeric(d['Title'].str.extract(r'^((?:19|20)\d\d)')[0], errors='coerce')
        d['model'] = d['Title'].str.lower().str.extract(r'^\d{4} (\w+ \w+)')[0]
        d = d.sort_values(['year', 'card_miles'], ascending=[False, True], na_position='last')
        d['turn'] = d.groupby('model').cumcount().astype(float)
        d.loc[d['model'].isin(PRIORITY), 'turn'] /= 2  # the operator's first choices get two turns per round
        d = d.sort_values(['turn', 'year'], ascending=[True, False]).head(a.cap)
        print(f"capped to {len(d)} (round-robin across models, newest first)")

    d.drop(columns=['price']).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
