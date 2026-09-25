"""
Turn the listing-page and seller-profile text saved by detail_pass.py into one
CSV row per listing.

Usage:
    python report/parse_details.py <details.json> <parsed.csv>
Reads <details>.profiles.json alongside when it exists.
"""
import json
import os
import re
import sys

import pandas as pd

MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'

# Wording in a review that points to a problem with the car or the seller
COMPLAINT = re.compile(
    r"scam|\blie[ds]?\b|lying|liar|misfire|check engine|more miles|miles than|miles more|rolled back"
    r"|not as described|never showed|no.show|rude|broke down|beware|avoid|terrible|worst|fake"
    r"|(?:don|doesn|didn).t work|emission|salvage|rebuilt|stay away|waste"
    r"|than (?:what was )?listed|odometer|rolled|carfax|black screen"
    r"|bad (?:engine|motor|transmission|trans)\b|not honest|dishonest|lied|shady"
    r"|transmission (?:light|went|slip|fail|problem|issue|gone)|warn (?:people|everyone|you|others)",
    re.I)


# The listed price is a down payment, not the price (English and Spanish)
BAIT = re.compile(
    r"down ?payment|\$?\d[\d,]*\s*(?:de )?(?:down|inicial)\b|pago inicial|de inicial|price (?:listed )?is (?:the )?down"
    r"|compra aqu|paga aqu|buy here|bhph|financiamos|no credit|sin cr[eé]dito|todos aprobados"
    r"|easy approval|approval options",
    re.I)

# The seller's own description admits a serious problem
DESC_PROBLEM = re.compile(
    r"bad transmission|transmisi[oó]n mala|trouble codes|codes? (?:come|regarding)|no title|for parts"
    r"|replace (?:the )?(?:hybrid )?battery|body has \d+k|on body has|engine (?:was )?replaced",
    re.I)

VIN = re.compile(r'\bVIN[:#\s]*([A-HJ-NPR-Z0-9]{17})\b', re.I)


def grab(pattern: str, text: str, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def parse_listing(listing_id: str, text: str) -> dict:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    price_i = next((i for i, l in enumerate(lines) if re.fullmatch(r'\$[\d,]+', l)), None)
    miles = grab(r'Driven ([\d,]+) miles', text)
    rating = grab(r'Seller details\n[^\n]+\n\((\d+)\)', text)
    desc = grab(r"Seller's description\n(.*?)(?:\n[^\n]*Location is approximate|\nSeller information|$)",
                text, flags=re.S | re.I) or ''
    problem = DESC_PROBLEM.search(desc)
    vin = VIN.search(desc)
    return {
        'bait': bool(BAIT.search(desc)),
        'desc_problem': problem.group(0) if problem else '',
        'vin': vin.group(1).upper() if vin else '',
        'id': listing_id,
        'title': lines[price_i - 1] if price_i else None,
        'price': int(lines[price_i].replace('$', '').replace(',', '')) if price_i else None,
        'listed': grab(r'Listed (.+?) in ', text),
        'city': grab(r'Listed .+? in ([^\n]+)', text),
        'miles': int(miles.replace(',', '')) if miles else None,
        'trans': grab(r'(Automatic|Manual) transmission', text),
        'owners': grab(r'\n(\d+) owners?\n', text),
        'clean_title': 'Clean title' in text,
        'no_damage': 'no significant damage' in text.lower(),
        'paid_off': 'paid off' in text.lower(),
        'seller': grab(r'Seller details\n([^\n]+)', text),
        'ratings': int(rating) if rating else 0,
        'joined': grab(r'Joined Facebook in (\d{4})', text),
        'sold_or_gone': bool(re.search(r"\bSold\b|no longer available|isn't available|Pending", text)),
        'desc': desc.replace('See less', '').strip(),
        'url': f'https://www.facebook.com/marketplace/item/{listing_id}/',
    }


def parse_profile(text: str) -> dict:
    """Rating, volume and reviews from a seller's Marketplace profile."""
    stars = re.search(r'(\d\.\d) \((\d+)\)', text)
    strengths = grab(r"strengths\n(.*?)\nReviews of", text, flags=re.S)
    reviews = []
    for name, date, body in re.findall(rf'\n([^\n]+)\n((?:{MONTHS}) \d{{1,2}}, \d{{4}})\n(.*?)\nLike\n\d+', text, re.S):
        body = re.sub(r'Notable:\s*', '', body).replace('\n  · ', ', ').replace('\n', ' ').strip()
        reviews.append({'name': name.strip(), 'date': date, 'text': body})
    complaints = [r for r in reviews if COMPLAINT.search(r['text'])]
    return {
        'stars': float(stars.group(1)) if stars else None,
        'star_count': int(stars.group(2)) if stars else 0,
        'active_listings': int(grab(r'(\d+) active listings?', text) or 0),
        'strengths': (strengths or '').replace('\n', ' · '),
        'reviews': json.dumps(reviews, ensure_ascii=False),
        'complaints': json.dumps(complaints, ensure_ascii=False),
        'n_complaints': len(complaints),
    }


def main(src: str, out: str) -> None:
    details = json.load(open(src))
    profiles_path = src.replace('.json', '.profiles.json')
    profiles = json.load(open(profiles_path)) if os.path.exists(profiles_path) else {}

    rows = []
    for lid, v in details.items():
        row = parse_listing(lid, v['text'])
        row['profile_url'] = v.get('profile_url')
        if row['profile_url'] in profiles:
            row.update(parse_profile(profiles[row['profile_url']]))
        rows.append(row)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{len(rows)} parsed ({len(profiles)} seller profiles) -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
