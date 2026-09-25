"""
Build one self-contained HTML car report, one tab per search.

Each --run takes three files:
    SCRAPE   the scraper's or search_slices.py's CSV (photo URLs, total count)
    DETAILS  parse_details.py output (mileage, title, seller rating and reviews)
    PICKS    a JSON of hand-picked tiers and rejections with notes, plus
             "label" and "budget" for the tab

Photos are downloaded once into report/data/img/ and embedded in the page,
because Facebook's CDN links expire after a few days.

Usage:
    python report/build_report.py \
        --run scrape_A.csv report/data/parsed_A.csv report/data/picks_A.json \
        --run scrape_B.csv report/data/parsed_B.csv report/data/picks_B.json \
        --out "../Human Reference Files/Car Hunt.html"
"""
import argparse
import base64
import html
import io
import json
import os
import re
from datetime import datetime

import pandas as pd
import requests
from PIL import Image

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'img')
MAX_MILES = 190_000
ACTIVE_LISTINGS_LIMIT = 6  # more than this many live listings reads as a flipper, not an owner


# ---------------------------------------------------------------- data

def load(scrape_csv: str, details_csv: str, picks_json: str):
    scrape = pd.read_csv(scrape_csv)
    scrape['id'] = scrape['Listing_URL'].str.extract(r'item/(\d+)')[0]
    scrape = scrape.drop_duplicates('id').set_index('id')

    cars = pd.read_csv(details_csv, dtype={'id': str, 'joined': 'Int64', 'owners': 'Int64'})
    cars['image_url'] = cars['id'].map(scrape['Image_URLs'])
    if 'Seller_Type' in scrape:  # only the scraper's own CSV has it
        cars['seller_type'] = cars['id'].map(scrape['Seller_Type'])
    cars['seller_count'] = cars['seller'].map(cars['seller'].value_counts())
    if 'vin' in cars:
        vins = cars['vin'].fillna('')
        cars['vin_count'] = vins.map(vins[vins != ''].value_counts()).fillna(0)
    # Down-payment listings show a deposit, not a price — leave them out entirely.
    # (Counted after seller_count on purpose: a seller's bait listings still count toward "Seller has N cars".)
    if 'bait' in cars:
        down = cars['bait'].fillna(False).astype(bool)
        cars = cars[~down].copy()
        cars.attrs['down_removed'] = int(down.sum())
    cars['flags'] = cars.apply(auto_flags, axis=1)

    picks = json.load(open(picks_json, encoding='utf-8'))
    return scrape, cars.set_index('id', drop=False), picks


def auto_flags(r) -> list:
    """Reasons a car drops out of the shortlist, computed from the listing page."""
    flags = []
    if not r['clean_title']:
        flags.append(('warn', 'Title not stated'))
    if r['seller_count'] > 1:
        flags.append(('bad', f"Seller has {int(r['seller_count'])} cars"))
    if r['sold_or_gone']:
        flags.append(('bad', 'Sold / pending'))
    if pd.notna(r['miles']) and r['miles'] > MAX_MILES:
        flags.append(('warn', 'Over 190k mi'))
    year = re.match(r'(\d{4})', str(r['title']))
    if pd.notna(r['miles']) and year and r['miles'] < 4_000 * (2026 - int(year.group(1))):
        flags.append(('warn', 'Mileage looks wrong'))
    # Seller-profile flags, present when detail_pass fetched the profile
    if pd.notna(r.get('stars')) and r['stars'] < 4.5:
        flags.append(('bad' if r['stars'] < 4.0 else 'warn', f"Rated {r['stars']:.1f}★"))
    if r.get('active_listings', 0) >= ACTIVE_LISTINGS_LIMIT:
        flags.append(('warn', f"{int(r['active_listings'])} active listings"))
    if r.get('bait') == True:  # noqa: E712 - numpy bool or NaN, not a Python bool
        flags.append(('bad', 'Price is a down payment'))
    if isinstance(r.get('desc_problem'), str) and r['desc_problem']:
        flags.append(('bad', f"Listing says “{r['desc_problem']}”"))
    if r.get('vin_count', 0) > 1:
        flags.append(('bad', 'Same VIN listed twice'))
    if year and pd.notna(r['price']) and int(year.group(1)) >= 2017 and r['price'] < 5000:
        flags.append(('warn', 'Very cheap for its year — ask if this is the full price'))
    if pd.notna(r['joined']) and int(r['joined']) >= 2025:
        flags.append(('warn', f"Profile made {r['joined']}"))
    if r.get('n_complaints', 0) > 0:
        n = int(r['n_complaints'])
        flags.append(('bad', f"{n} complaint{'s' if n > 1 else ''} in reviews"))
    return flags


CHECKS = {}  # listing id -> car-specific checks, filled from --checks


def checks_html(listing_id: str) -> str:
    items = CHECKS.get(listing_id)
    if not items:
        return ''
    lis = ''.join(f'<li>{e(c)}</li>' for c in items)
    return f'<details class="checks"><summary>When you go · {len(items)}</summary><ul>{lis}</ul></details>'


def complaints(r) -> list:
    raw = r.get('complaints')
    return json.loads(raw) if isinstance(raw, str) and raw else []


def complaint_html(r, limit: int = 2, chars: int = 220) -> str:
    items = complaints(r)[:limit]
    if not items:
        return ''
    quotes = ''.join(
        f'<blockquote>“{e(c["text"][:chars])}{"…" if len(c["text"]) > chars else ""}”'
        f'<cite>Buyer review · {e(c["date"])}</cite></blockquote>' for c in items)  # reviewer names left out: the page gets shared
    return f'<div class="complaints">{quotes}</div>'


def photo(listing_id: str, url, size: int = 440) -> str:
    """Return a data: URI for the listing photo, downloading it once."""
    os.makedirs(IMG_DIR, exist_ok=True)
    path = os.path.join(IMG_DIR, f'{listing_id}.jpg')
    if not os.path.exists(path):
        if not isinstance(url, str) or not url.startswith('http'):
            return ''
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert('RGB')
            img.thumbnail((640, 640))
            img.save(path, 'JPEG', quality=78)
        except Exception as e:
            print(f"  photo failed for {listing_id}: {e}")
            return ''
    # Embed smaller than the cached copy: a four-tab page carries hundreds of photos
    img = Image.open(path)
    img.thumbnail((size, size))
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=68 if size > 200 else 60)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- formatting

def e(v) -> str:
    return html.escape('' if v is None or (isinstance(v, float) and pd.isna(v)) else str(v))


def nice_title(t: str) -> str:
    """'2008 Toyota camry LE Sedan 4D' -> '2008 Toyota Camry LE' (drop body-style tail)."""
    t = re.sub(r'\s+(Sedan|Coupe|Hatchback|Wagon|Sport Utility|Sport SUV)\s+\dD$', '', str(t))
    t = ' '.join(w[:1].upper() + w[1:] if w.islower() else w for w in t.split())
    for wrong, right in (('Mazda Mazda3', 'Mazda3'), ('Mazda Mazda6', 'Mazda6'), ('Cr-v', 'CR-V'),
                         ('Rav4', 'RAV4'), ('Cx-5', 'CX-5'), ('Lexus Es', 'Lexus ES'),
                         ('Mx-5', 'MX-5'), ('Subaru Xv ', 'Subaru XV '), ('Prius C ', 'Prius c ')):
        t = t.replace(wrong, right)
    return t


def money(v) -> str:
    return f'${v:,.0f}' if pd.notna(v) else '—'


def miles(v) -> str:
    return f'{v:,.0f} mi' if pd.notna(v) else 'not listed'


def seller_line(r) -> str:
    bits = [e(r['seller'])]
    if r['ratings']:
        bits.append(f"{r['ratings']} ratings")
    if pd.notna(r['joined']):
        bits.append(f"on Facebook since {r['joined']}")
    return ' · '.join(bits)


def chips(r) -> str:
    out = []
    if r['clean_title']:
        out.append('<span class="chip ok">Clean title</span>')
    if pd.notna(r['owners']) and r['owners'] == 1:
        out.append('<span class="chip ok">1 owner</span>')
    if pd.notna(r.get('stars')) and r['stars'] >= 4.5:
        out.append(f'<span class="chip ok">{r["stars"]:.1f}★ ({int(r["star_count"])})</span>')
    elif pd.isna(r.get('stars')) and r['ratings'] >= 30:
        out.append(f'<span class="chip acc">{r["ratings"]} ratings</span>')
    if r['trans'] == 'Manual':
        out.append('<span class="chip">Manual</span>')
    out += [f'<span class="chip {k}">{e(t)}</span>' for k, t in r['flags']]
    return ''.join(out)


# ---------------------------------------------------------------- sections

def pick_card(r, pick, rank) -> str:
    src = photo(r['id'], r['image_url'])
    img = f'<img src="{src}" alt="{e(nice_title(r["title"]))}" loading="lazy">' if src else '<div class="noimg">no photo</div>'
    return f'''
    <article class="card pick">
      <a class="ph" href="{e(r['url'])}" target="_blank" rel="noopener">{img}<span class="rank">{e(rank) if isinstance(rank, str) else f'#{rank}'}</span></a>
      <div class="body">
        <div class="eyebrow">{e(pick['headline'])}</div>
        <h3>{e(nice_title(r['title']))}</h3>
        <div class="price num">{money(r['price'])}</div>
        <dl class="kv">
          <dt>Miles</dt><dd class="num">{miles(r['miles'])}</dd>
          <dt>Where</dt><dd>{e(r['city'])}</dd>
          <dt>Listed</dt><dd>{e(r['listed'])}</dd>
          <dt>Seller</dt><dd>{seller_line(r)}</dd>
        </dl>
        <div class="chips">{chips(r)}</div>
        <p class="note">{e(pick['note'])}</p>
        {complaint_html(r)}
        {checks_html(r['id'])}
        <a class="btn" href="{e(r['url'])}" target="_blank" rel="noopener">Open on Facebook →</a>
      </div>
    </article>'''


def all_row(r, tier) -> str:
    src = photo(r['id'], r['image_url'], size=150)  # shown at 72px; 2x for sharp screens
    thumb = f'<img src="{src}" alt="" loading="lazy">' if src else ''
    status = {'top': 'Top pick', 'backup': 'Backup', 'rejected': 'Rejected'}.get(tier, '')
    return f'''
      <tr data-price="{r['price'] if pd.notna(r['price']) else 0}" data-miles="{r['miles'] if pd.notna(r['miles']) else 9e9}"
          data-clean="{int(bool(r['clean_title']))}" data-flagged="{int(bool(r['flags']) or tier == 'rejected')}">
        <td class="th">{thumb}</td>
        <td><a class="car" href="{e(r['url'])}" target="_blank" rel="noopener">{e(nice_title(r['title']))}</a>
            {f'<span class="tier {tier}">{status}</span>' if status else ''}
            <div class="chips">{chips(r)}</div>{complaint_html(r, limit=1, chars=140)}</td>
        <td class="num">{money(r['price'])}</td>
        <td class="num">{miles(r['miles'])}</td>
        <td>{e(r['city'])}<div class="mute small">{e(r['listed'])}</div></td>
        <td class="small">{seller_line(r)}</td>
      </tr>'''


def reject_card(r, reason) -> str:
    return f'''
    <div class="rule">
      <h3><a href="{e(r['url'])}" target="_blank" rel="noopener">{e(nice_title(r['title']))}</a>
        <span class="num mute">{money(r['price'])}</span></h3>
      <p>{e(reason)}</p>
    </div>'''


GUIDE = """
<div class="run" id="checklist" role="tabpanel" hidden>
  <div class="sheet">
    <div class="sheet-head">
      <div>
        <div class="eyebrow">Viewing checklist</div>
        <h1>2015 Subaru Crosstrek 2.0i Premium</h1>
        <p class="sheet-meta">Sat Sep 26, 11:00 AM &middot; Roswell &middot; asking $5,950 &middot; 165k mi &middot; VIN JF2GPAFC3F8255044</p>
      </div>
      <button type="button" class="print-btn noprint" id="printBtn">Print this page</button>
    </div>

    <div class="sheet-cols">
      <div class="sheet-block">
        <h3>1. When you get there</h3>
        <ul class="ticks">
          <li>Hand on the hood before it starts. Cool is good; warm means it was already run.</li>
          <li>Key on, engine off: every dash light comes on.</li>
          <li>Cold start. Listen to the first few seconds: rattle or knock? Blue smoke = oil, thick white = coolant.</li>
          <li>Engine running: check engine, AWD and AT OIL TEMP lights all go off.</li>
        </ul>
      </div>

      <div class="sheet-block mech">
        <h3>2. With the mechanic <span>$150 diagnostic</span></h3>
        <ul class="ticks">
          <li>Mention the CVT is your main worry.</li>
          <li>Ask for a transmission (CVT) module scan along with the engine scan.</li>
          <li>Ask him to check the readiness monitors (shows if codes were cleared recently).</li>
          <li>Ask for a look underneath for oil or CVT fluid leaks.</li>
          <li>Ask him to check the oil and coolant.</li>
          <li>Ask about the CV axle boots, wheel bearings and suspension.</li>
          <li>If he has time, ask him to ride along on the test drive.</li>
        </ul>
      </div>

      <div class="sheet-block">
        <h3>3. Test drive, about 15 min</h3>
        <ul class="ticks">
          <li>A few gentle starts from a stop: smooth, no shudder.</li>
          <li>Steady 30&ndash;45 mph, light throttle: no whine or drone.</li>
          <li>One firm acceleration: revs and speed climb together, no flaring.</li>
          <li>Parking lot, wheel all the way left, then right, slow circles.<br>
            <i>Clicking</i> = CV joint ($150&ndash;400, negotiate). <i>Hopping or tires scrubbing</i> = AWD clutch, walk.</li>
          <li>Highway 55&ndash;65: no hum that changes when you weave a little (wheel bearing).</li>
          <li>Brakes stop straight, no grinding or pulsing. A/C cold. Windows and locks work.</li>
        </ul>
        <p class="walk-line"><b>Walk away:</b> shudder, whine, rev flare, flashing AT OIL TEMP, hopping in turns.</p>
      </div>

      <div class="sheet-block">
        <h3>4. Questions for Sean</h3>
        <ul class="ticks">
          <li>What was it doing before the CVT repair in Dec 2022? Fluid changed since?</li>
          <li>Were all four tires replaced together in 2025?</li>
          <li>Any warning lights since you've had it? Why are you selling?</li>
        </ul>
      </div>

      <div class="sheet-block">
        <h3>5. Price</h3>
        <p class="script">&ldquo;Drives well and I can buy today. The CVT fluid's never been changed on record, that's about $300 right away, and it's the Premium, not the Limited. Would you do $5,400?&rdquo;</p>
        <ul class="plain-list">
          <li>Also on your side: repossessed in 2023, 165k miles.</li>
          <li>$5,600&ndash;5,700 counter: take it. Firm at $5,950: still buy.</li>
        </ul>
      </div>

      <div class="sheet-block">
        <h3>6. Paperwork, then pay</h3>
        <ul class="ticks">
          <li>Name on the title = his driver's license.</li>
          <li>VIN on the title = dash = driver's door sticker.</li>
          <li>No lienholder listed, or he has the release letter.</li>
          <li>He signs the title. Price and mileage filled in, no cross-outs or white-out.</li>
          <li>Bill of sale (Georgia T-7): price, date, VIN, both signatures.</li>
          <li>Insurance on the car before you drive it off. Plates stay with him.</li>
          <li>Pay last.</li>
        </ul>
      </div>
    </div>

    <div class="sheet-after">
      <b>After:</b>
      <span class="tick-inline">Call insurance: swap the Maxima for the Crosstrek</span>
      <span class="tick-inline">Cobb tag office within 7 business days (7% TAVT on the state's value; move the Maxima plate, $20)</span>
      <span class="tick-inline">CVT drain-and-fill with Subaru fluid, then every ~30k</span>
    </div>
  </div>
</div>
"""


CSS = r'''
:root{
  --bg:#f1f5f9; --bg2:#e2e8f0; --line:#cbd5e1; --line2:#94a3b8;
  --ink:#0f172a; --ink2:#334155; --mute:#4b5666; --head:#1d4ed8; --strong:#020617;
  --acc:#7e22ce; --acc2:#0369a1; --warn:#b45309; --ok:#15803d; --bad:#be123c; --gold:#a16207;
  --card:#ffffff; --shadow:0 1px 0 rgba(0,43,54,.06), 0 6px 20px -12px rgba(0,43,54,.25);
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", Arial, sans-serif;
  color-scheme: light;
}
:root[data-theme="dark"]{
  --bg:#221a0f; --bg2:#2c2215; --line:#3f3120; --line2:#5e452b;
  --ink:#d3af86; --ink2:#c8a67a; --mute:#a57a4c; --head:#f2a750; --strong:#eccfa6;
  --acc:#8ab1b0; --acc2:#8ab1b0; --warn:#f06431; --ok:#98ac52; --bad:#dc3958; --gold:#f79a32;
  --card:#281e11; --shadow:0 1px 0 rgba(0,0,0,.35), 0 8px 24px -14px rgba(0,0,0,.7);
  color-scheme: dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding-inline:16px;padding-block:0 64px}
h1,h2,h3{font-family:var(--serif);color:var(--head);text-wrap:balance;margin:0;font-weight:600;letter-spacing:-.01em}
h1{font-size:clamp(30px,4.6vw,44px);line-height:1.1}
h2{font-size:clamp(22px,3vw,28px);line-height:1.2}
h3{font-size:18px;line-height:1.3}
p{margin:0} a{color:var(--acc2)} strong{color:var(--strong);font-weight:650}
.eyebrow{font:600 11px/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--acc)}
.mute{color:var(--mute)} .small{font-size:12.5px} .num{font-variant-numeric:tabular-nums}

.top{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line)}
@supports (background:color-mix(in srgb,red 50%,blue)){.top{background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:saturate(1.2) blur(10px);-webkit-backdrop-filter:saturate(1.2) blur(10px)}}
.top .wrap{padding-block:10px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;font-family:var(--serif);font-size:18px;color:var(--head);font-weight:600;margin-right:auto}
.brand svg{width:26px;height:26px}
nav.tabs{display:flex;gap:2px;flex-wrap:wrap}
nav.tabs a{font:600 12px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;text-decoration:none;color:var(--ink2);padding:8px 10px;border-radius:6px}
nav.tabs a:hover,nav.tabs a:focus-visible{background:var(--bg2);color:var(--head);outline:none}
.toggle{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line2);background:var(--bg2);color:var(--ink);border-radius:999px;padding:6px 10px;font:600 12px var(--sans);cursor:pointer}
.toggle svg{width:16px;height:16px}

.hero{padding-block:40px 28px;display:grid;grid-template-columns:1.4fr 1fr;gap:28px;align-items:end;border-bottom:1px solid var(--line)}
.hero .sub{font:600 16px var(--sans);color:var(--acc2);margin:6px 0 12px}
.lede{font-size:16.5px;color:var(--ink2);max-width:58ch}
.facts{display:grid;grid-template-columns:repeat(2,1fr);border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--card)}
.facts div{padding:14px 16px;border-left:1px solid var(--line);border-top:1px solid var(--line)}
.facts div:nth-child(odd){border-left:0} .facts div:nth-child(-n+2){border-top:0}
.facts b{display:block;font:600 28px/1 var(--serif);color:var(--head);margin-bottom:4px}
.facts span{font-size:11.5px;color:var(--mute);letter-spacing:.06em;text-transform:uppercase}
@media (max-width:760px){.hero{grid-template-columns:1fr}}

section{padding-block:40px;border-bottom:1px solid var(--line);scroll-margin-top:64px}
section:last-of-type{border-bottom:0}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}
.sec-head p{color:var(--ink2);max-width:62ch}
.callout{border-left:3px solid var(--acc);background:var(--bg2);padding:12px 16px;border-radius:0 8px 8px 0;margin-block:14px;color:var(--ink)}
.callout.warn{border-color:var(--warn)}

.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media (max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:560px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column}
.card .ph{position:relative;display:block;aspect-ratio:4/3;background:var(--bg2)}
.card .ph img{width:100%;height:100%;object-fit:cover;display:block}
.card .noimg{display:grid;place-items:center;height:100%;color:var(--mute);font-size:12px}
.rank{position:absolute;top:10px;left:10px;font:700 13px/1 var(--sans);background:var(--card);color:var(--head);border:1px solid var(--line2);border-radius:999px;padding:6px 9px}
.card .body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:9px;flex:1}
.card .price{font:600 26px/1 var(--serif);color:var(--strong)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px;margin:0}
.kv dt{color:var(--mute);letter-spacing:.04em;text-transform:uppercase;font-size:11px;padding-top:2px}
.kv dd{margin:0;color:var(--ink)}
.note{color:var(--ink2);font-size:13.5px;border-left:2px solid var(--acc);padding-left:10px}
.card .btn{margin-top:auto;align-self:flex-start}
.complaints{display:grid;gap:6px}
.complaints blockquote{margin:0;border-left:2px solid var(--bad);background:var(--bg2);border-radius:0 6px 6px 0;padding:7px 10px;font-size:12.5px;color:var(--ink2);font-style:italic}
.complaints cite{display:block;font-style:normal;font-size:11px;color:var(--mute);margin-top:3px}
td .complaints{margin-top:6px;max-width:52ch}
.btn{font:600 12px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--line2);background:var(--bg2);color:var(--ink);border-radius:8px;padding:9px 12px;cursor:pointer;text-decoration:none}
.btn:hover{border-color:var(--acc2);color:var(--head)}

.chips{display:flex;gap:5px;flex-wrap:wrap}
.chip{--c:var(--mute);font:600 10.5px/1 var(--sans);letter-spacing:.05em;text-transform:uppercase;color:var(--c);border:1px solid var(--c);border-radius:999px;padding:4px 7px;white-space:nowrap}
@supports (background:color-mix(in srgb,red 50%,blue)){.chip{background:color-mix(in srgb,var(--c) 11%,transparent)}}
.chip.ok{--c:var(--ok)} .chip.warn{--c:var(--warn)} .chip.bad{--c:var(--bad)} .chip.acc{--c:var(--acc2)}

.seg{display:inline-flex;border:1px solid var(--line2);border-radius:8px;overflow:hidden;background:var(--bg2)}
.seg button{font:600 12px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;padding:8px 12px;border:0;background:transparent;color:var(--ink2);cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--card);color:var(--head);box-shadow:inset 0 0 0 1px var(--line2)}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:760px;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--line)}
thead th{font:600 11px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--mute);background:var(--bg2);position:sticky;top:0}
thead th[data-sort]{cursor:pointer} thead th[data-sort]:hover{color:var(--head)}
tbody tr:last-child td{border-bottom:0}
td.num{white-space:nowrap} thead th{white-space:nowrap}
td.th{width:84px;padding-right:0} td.th img{width:72px;height:54px;object-fit:cover;border-radius:6px;display:block;background:var(--bg2)}
a.car{font-family:var(--serif);font-weight:600;color:var(--head);text-decoration:none;font-size:15px}
a.car:hover{text-decoration:underline}
td .chips{margin-top:5px}
.tier{font:700 10px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;margin-left:6px;padding:3px 6px;border-radius:4px;background:var(--bg2);color:var(--ink2)}
.tier.top{background:var(--ok);color:var(--card)} .tier.backup{background:var(--acc2);color:var(--card)} .tier.rejected{background:var(--bad);color:var(--card)}
tr.hide{display:none}

.rules{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
@media (max-width:760px){.rules{grid-template-columns:1fr}}
.rule{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.rule h3{margin-bottom:6px;font-size:16px;display:flex;justify-content:space-between;gap:10px}
.rule h3 a{color:var(--head);text-decoration:none}
.rule p{color:var(--ink2);font-size:14px}
ol.how{margin:0;padding-left:20px;color:var(--ink2);display:grid;gap:6px;max-width:70ch}
footer{padding-block:28px;color:var(--mute);font-size:12.5px;border-top:1px solid var(--line)}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
'''

# ---------------------------------------------------------------- page

def area_table(scrape, cars, tier) -> str:
    """Compare seller trust between search areas, when the run searched more than one."""
    if 'Search_Location' not in scrape or scrape['Search_Location'].nunique() < 2:
        return ''
    c = cars.copy()
    c['area'] = c['id'].map(scrape['Search_Location']).fillna('?').str.replace(r' · \d+ mi$', '', regex=True)
    rows = []
    for area, g in c.groupby('area'):
        rated = g[g['stars'].notna()] if 'stars' in g else g.iloc[0:0]
        pct = lambda n, d: f'{100 * n / d:.0f}%' if d else '—'
        clean = sum(1 for i, r in g.iterrows() if not r['flags'] and tier.get(i) != 'rejected')
        rows.append(f'''<tr><td class="who">{e(area)}</td><td class="num">{len(g)}</td>
          <td class="num">{pct((rated['stars'] < 4.5).sum(), len(rated))}</td>
          <td class="num">{pct((g.get('active_listings', 0) >= ACTIVE_LISTINGS_LIMIT).sum(), len(g))}</td>
          <td class="num">{pct((g.get('n_complaints', 0) > 0).sum(), len(g))}</td>
          <td class="num">{pct(clean, len(g))}</td></tr>''')
    return f'''
  <section class="areas">
    <div class="sec-head"><h2>Is North Georgia more trustworthy?</h2>
      <p>Same checks, split by where the car was found. Cars inside both circles count for the first area searched.</p></div>
    <div class="tbl"><table class="plain">
      <thead><tr><th>Area</th><th>Cars checked</th><th>Seller under 4.5★</th><th>Flipper (6+ listings)</th>
        <th>Complaint in reviews</th><th>No red flags</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>
  </section>'''


def run_panel(n: int, scrape, cars, picks) -> tuple:
    """One run's tab button and its panel."""
    rid = f'run{n}'
    tier = {p['id']: p['tier'] for p in picks['picks']}
    tier.update({x['id']: 'rejected' for x in picks['rejected']})
    tops = [p for p in picks['picks'] if p['tier'] == 'top' and p['id'] in cars.index]
    backups = [p for p in picks['picks'] if p['tier'] == 'backup' and p['id'] in cars.index]
    clean = int(sum(1 for i, r in cars.iterrows() if not r['flags'] and tier.get(i) != 'rejected'))

    top_html = ''.join(pick_card(cars.loc[p['id']], p, i) for i, p in enumerate(tops, 1))
    backup_html = ''.join(pick_card(cars.loc[p['id']], p, i) for i, p in enumerate(backups, len(tops) + 1))
    rows = ''.join(all_row(r, tier.get(i)) for i, r in cars.sort_values('price').iterrows())
    rejects = ''.join(reject_card(cars.loc[x['id']], x['reason']) for x in picks['rejected'] if x['id'] in cars.index)
    multi = cars[cars['seller_count'] > 1].groupby('seller').size().sort_values(ascending=False)
    multi_html = ', '.join(f'{e(s)} ({n})' for s, n in multi.items())
    label, budget = picks.get('label', f'Run {n}'), picks.get('budget', '')

    # "hidden": true in the picks file keeps the tab out of sight until the theme button is
    # clicked 10 times quickly (a way to keep a tab from casual viewers, not a real lock)
    secret = ' hidden data-secret="1"' if picks.get('hidden') else ''
    tab = (f'<button type="button" role="tab" data-run="{rid}" aria-selected="false"{secret}>'
           f'<b>{e(label)}</b><span>{e(budget)}</span></button>')
    panel = RUN.format(
        rid=rid, n=n, label=e(label), budget=e(budget), search=e(picks['search']), date=e(picks['date']),
        n_scraped=f'{len(scrape):,}', n_reliable=len(cars), n_clean=clean, n_picks=len(tops) + len(backups),
        top=top_html, rejects=rejects, rows=rows, areas=area_table(scrape, cars, tier),
        backups=f'''<section id="{rid}-backups"><div class="sec-head"><h2>Backups</h2>
          <p>Good cars with a catch: higher miles, a thin listing, a flipper, or a longer drive.</p></div>
          <div class="grid">{backup_html}</div></section>''' if backups else '',
        multi=f'''<div class="callout warn"><b>Multi-car sellers</b> — one person, several “1 owner, paid off” cars is
          a curbstoner (an unlicensed dealer posing as a private seller): {multi_html}.</div>''' if len(multi) else '',
    )
    return tab, panel


def best_panel(runs, order=None) -> tuple:
    """A tab with every run's top picks side by side: in the given overall order, else cheapest first."""
    found = {}
    for scrape, cars, picks in runs:
        tops = [p for p in picks['picks'] if p['tier'] == 'top' and p['id'] in cars.index]
        for p in tops:
            found[p['id']] = (cars.loc[p['id']], p, picks.get('label', ''))
    if order:
        ids = [o['id'] for o in order['order'] if o['id'] in found]
        why = {o['id']: o.get('why', '') for o in order['order']}
    else:
        ids = sorted(found, key=lambda i: found[i][0]['price'])
        why = {}
    cards = []
    for n, i in enumerate(ids, 1):
        r, p, label = found[i]
        if why.get(i):
            p = {**p, 'note': f"{why[i]} {p['note']}"}
        cards.append((r['price'], pick_card(r, p, f"#{n} · {label}")))
    prices = [c[0] for c in cards]
    ranked = f", ranked {order.get('basis', 'best first')}" if order else ' and sorted cheapest first'
    # Unique listings behind the visible tabs; a hidden tab's search isn't counted
    n_scraped = len(set().union(*(set(s.index) for s, _, p in runs if not p.get('hidden'))))

    # The car chosen to go see, pinned above the ranking with why and what could still change it
    winner_html = ''
    w = (order or {}).get('winner')
    if w and w['id'] in found:
        r, p, label = found[w['id']]
        card = pick_card(r, {**p, 'headline': w['headline'], 'note': w['note']}, f"Front-runner · {label}")
        reasons = ''.join(f'<li>{e(x)}</li>' for x in w.get('why', []))
        dealbreakers = ''.join(f'<li>{e(x)}</li>' for x in w.get('dealbreakers', []))
        winner_html = f'''
  <section id="best-winner" class="winner">
    <div class="sec-head"><h2>The front-runner</h2><p>{e(w.get('status', ''))}</p></div>
    <div class="winner-grid">
      {card}
      <div class="rule"><h3>Why this one</h3><ul>{reasons}</ul>
        <h3 style="margin-top:14px">What would still knock it out</h3><ul>{dealbreakers}</ul></div>
    </div>
  </section>'''
    tab = ('<button type="button" role="tab" data-run="best" aria-selected="false">'
           '<b>All top picks</b><span>every budget</span></button>')
    panel = f'''
<div class="run" id="best" role="tabpanel" hidden>
  <header class="hero">
    <div>
      <div class="eyebrow">Every search · Facebook Marketplace</div>
      <h1 style="margin-top:10px">All top picks</h1>
      <span class="budget">{money(min(prices))} – {money(max(prices))}</span>
      <p class="lede">The cars ranked <strong>#1–5</strong> in each budget tab, together on one screen{ranked}.
      Each photo's badge shows its overall place and the tab it came from; the reasoning is on the card.
      {'Market values are estimates, not looked up.' if order else ''}</p>
    </div>
    <div class="facts">
      <div><b class="num">{len(cards)}</b><span>top picks</span></div>
      <div><b class="num">{n_scraped:,}</b><span>listings scraped</span></div>
      <div><b class="num">{money(min(prices))}</b><span>cheapest</span></div>
      <div><b class="num">{money(max(prices))}</b><span>priciest</span></div>
    </div>
  </header>
  {winner_html}
  <section id="best-picks">
    <div class="sec-head"><h2>{'Every top pick, best first' if order else 'Every top pick, cheapest first'}</h2>
      <p>Backups, the full tables and the rejections stay in each budget's own tab.</p></div>
    <div class="grid">{''.join(c[1] for c in cards)}</div>
  </section>
</div>'''
    return tab, panel


def build(runs, order=None) -> str:
    tabs, panels = map(list, zip(*(run_panel(n, *r) for n, r in enumerate(runs, 1))))
    best_tab, best = best_panel(runs, order)
    tabs.insert(0, best_tab)  # far left, and the default
    panels.insert(0, best)
    tabs.insert(1, '<button type="button" role="tab" data-run="checklist" aria-selected="false">'
                   '<b>Saturday checklist</b><span>printable</span></button>')
    panels.insert(1, GUIDE)
    return PAGE.format(tabs=''.join(tabs), panels=''.join(panels), css=CSS, js=JS,
                       generated=datetime.now().strftime('%Y-%m-%d %H:%M'))


CSS_EXTRA = r'''
.runs{display:flex;gap:6px;flex-wrap:wrap;padding-block:0 10px}
.runs button{display:grid;gap:3px;text-align:left;border:1px solid var(--line2);background:var(--bg2);color:var(--ink2);border-radius:10px;padding:8px 12px;cursor:pointer;font:inherit}
.runs button b{font:600 14px/1.1 var(--serif);color:var(--head)}
.runs button span{font:600 10.5px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}
.runs button[aria-selected="true"]{background:var(--card);border-color:var(--acc2);box-shadow:inset 0 -2px 0 var(--acc2)}
.runs button:focus-visible{outline:2px solid var(--acc2);outline-offset:2px}
.runs button[hidden]{display:none}
.winner-grid{display:grid;grid-template-columns:1fr 1.4fr;gap:16px;align-items:start}
@media (max-width:760px){.winner-grid{grid-template-columns:1fr}}
.winner .card{border:2px solid var(--ok)}
.winner .rank{background:var(--ok);color:var(--card);border-color:var(--ok)}
.winner .rule ul{margin:6px 0 0;padding-left:18px;display:grid;gap:5px;color:var(--ink2);font-size:14px}
details.checks{border:1px solid var(--line);border-radius:8px;background:var(--bg2);font-size:13px}
details.checks summary{cursor:pointer;padding:7px 10px;font:600 11px/1.2 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--acc2)}
details.checks ul{margin:0;padding:0 12px 10px 28px;display:grid;gap:5px;color:var(--ink2)}
.walk{border-left:3px solid var(--bad)}
.hero .budget{display:inline-block;font:700 13px/1 var(--sans);letter-spacing:.04em;color:var(--ok);border:1px solid var(--ok);border-radius:999px;padding:6px 10px;margin:4px 0 12px}
section{scroll-margin-top:150px}
table.plain{min-width:640px} td.who{font-family:var(--serif);font-weight:600;color:var(--head)}
.sheet{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px 24px;margin:18px 0 28px;box-shadow:var(--shadow)}
.sheet-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;border-bottom:2px solid var(--ink);padding-bottom:10px;margin-bottom:14px}
.sheet-head h1{margin:6px 0 4px;font-size:26px}
.sheet-meta{margin:0;color:var(--ink2);font-size:14px}
.print-btn{font:600 14px/1 var(--sans);border:1px solid var(--acc2);color:var(--acc2);background:var(--bg2);border-radius:8px;padding:10px 14px;cursor:pointer;white-space:nowrap}
.print-btn:hover{background:var(--card)}
.sheet-cols{columns:2;column-gap:28px}
@media (max-width:760px){.sheet-cols{columns:1}.sheet-head{flex-direction:column}}
.sheet-block{break-inside:avoid;margin:0 0 16px}
.sheet-block h3{font:700 15px/1.2 var(--serif);color:var(--head);margin:0 0 6px;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.sheet-block h3 span{font:600 10.5px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}
.sheet-block.mech{border:1.5px solid var(--acc2);border-radius:8px;padding:10px 12px;background:var(--bg2)}
.mech-note{margin:0 0 7px;font-size:13.5px;font-style:italic;color:var(--ink2)}
.ticks{list-style:none;margin:0;padding:0;display:grid;gap:5px}
.ticks li{position:relative;padding-left:24px;font-size:14px;line-height:1.4;color:var(--ink)}
.ticks li::before{content:"";position:absolute;left:0;top:2px;width:13px;height:13px;border:1.5px solid var(--ink2);border-radius:3px;background:var(--card)}
.plain-list{margin:6px 0 0;padding-left:18px;font-size:14px;color:var(--ink);display:grid;gap:4px}
.script{margin:0;font-size:14px;font-style:italic;color:var(--ink);border-left:3px solid var(--line2);padding-left:10px}
.walk-line{margin:8px 0 0;font-size:13.5px;color:var(--bad)}
.sheet-after{border-top:1px solid var(--line);padding-top:10px;font-size:13.5px;display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline}
.tick-inline{position:relative;padding-left:20px}
.tick-inline::before{content:"";position:absolute;left:0;top:2px;width:12px;height:12px;border:1.5px solid var(--ink2);border-radius:3px}
@page{size:letter;margin:0.45in}
@media print{
  html.print-sheet body{background:#fff}
  html.print-sheet .top, html.print-sheet footer, html.print-sheet #how, html.print-sheet .noprint,
  html.print-sheet .run:not(#checklist){display:none!important}
  html.print-sheet #checklist{display:block!important}
  html.print-sheet main.wrap{max-width:none;padding:0}
  html.print-sheet .sheet{border:0;box-shadow:none;padding:0;margin:0;background:#fff}
  html.print-sheet .sheet, html.print-sheet .sheet *{color:#000!important;background:transparent!important}
  html.print-sheet .sheet-block.mech{border-color:#000!important}
  html.print-sheet .ticks li::before, html.print-sheet .tick-inline::before{border-color:#000!important}
  html.print-sheet .sheet-head{border-bottom-color:#000}
  html.print-sheet .sheet-head h1{font-size:20px}
  html.print-sheet .ticks li, html.print-sheet .plain-list, html.print-sheet .script{font-size:11.5px;line-height:1.35}
  html.print-sheet .sheet-block{margin-bottom:11px}
  html.print-sheet .sheet-cols{columns:2;column-gap:22px}
  html.print-sheet .sheet-head{flex-direction:row}
  html.print-sheet .walk-line, html.print-sheet .mech-note{font-size:11px}
  html.print-sheet .sheet-after{font-size:11px}
}
'''

JS = r'''
(function(){
  var root=document.documentElement, btn=document.getElementById('themeBtn'),
      icon=document.getElementById('themeIcon').querySelector('use'), label=document.getElementById('themeLabel');
  function store(k,v){ try{ if(v===undefined) return localStorage.getItem(k); localStorage.setItem(k,v); }catch(e){ return null; } }
  function current(){ return root.getAttribute('data-theme') || 'light'; }
  function paint(){ var d=current()==='dark'; icon.setAttribute('href', d?'#i-sun':'#i-moon'); label.textContent=d?'Light':'Dark'; }
  var s=store('carhunt-theme'); if(s==='dark'||s==='light') root.setAttribute('data-theme',s);
  paint();
  btn.addEventListener('click',function(){ var n=current()==='dark'?'light':'dark'; root.setAttribute('data-theme',n); store('carhunt-theme',n); paint(); });

  var tabs=[].slice.call(document.querySelectorAll('.runs [data-run]')), active=null;
  function show(rid){
    active=rid;
    tabs.forEach(function(t){ t.setAttribute('aria-selected', t.dataset.run===rid?'true':'false'); });
    document.querySelectorAll('.run').forEach(function(p){ p.hidden = p.id!==rid; });
    try{ history.replaceState(null,'','#'+rid); }catch(e){}
  }
  tabs.forEach(function(t){ t.addEventListener('click',function(){ show(t.dataset.run); window.scrollTo(0,0); }); });
  var want=(location.hash||'').slice(1);
  var open=tabs.filter(function(t){return !t.dataset.secret;});  // a hidden tab never opens from the address bar
  show(open.some(function(t){return t.dataset.run===want;}) ? want : (document.getElementById('best') ? 'best' : open[0].dataset.run));

  // Print only the checklist: the button, or Ctrl+P while its tab is open
  var printBtn=document.getElementById('printBtn');
  function sheetOn(){ if(active==='checklist') root.classList.add('print-sheet'); }
  window.addEventListener('beforeprint', sheetOn);
  window.addEventListener('afterprint', function(){ root.classList.remove('print-sheet'); });
  if(printBtn) printBtn.addEventListener('click', function(){ root.classList.add('print-sheet'); window.print(); });

  // Ten clicks on the theme button within 5 seconds shows any hidden tabs, for this visit only
  var clicks=[];
  btn.addEventListener('click',function(){
    var now=Date.now(); clicks=clicks.filter(function(t){return now-t<5000;}); clicks.push(now);
    if(clicks.length>=10){ tabs.forEach(function(t){ if(t.dataset.secret) t.hidden=false; }); clicks=[]; }
  });

  document.querySelectorAll('nav.tabs a[data-sec]').forEach(function(a){
    a.addEventListener('click',function(ev){
      var el=document.getElementById(a.dataset.sec==='how' ? 'how' : active+'-'+a.dataset.sec);
      ev.preventDefault(); if(el) el.scrollIntoView();  // the All top picks tab has only a picks section
    });
  });

  document.querySelectorAll('section.all').forEach(function(sec){
    var body=sec.querySelector('tbody'), rows=[].slice.call(body.rows), segs=sec.querySelectorAll('.seg button');
    function filter(f){
      rows.forEach(function(r){
        r.classList.toggle('hide', (f==='clean' && r.dataset.clean!=='1') || (f==='shortlist' && r.dataset.flagged==='1'));
      });
      segs.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.f===f?'true':'false'); });
      sec.querySelector('.shown').textContent = rows.filter(function(r){return !r.classList.contains('hide');}).length;
    }
    segs.forEach(function(b){ b.addEventListener('click',function(){ filter(b.dataset.f); }); });
    sec.querySelectorAll('th[data-sort]').forEach(function(th){
      th.addEventListener('click',function(){
        var k=th.dataset.sort, asc=th.dataset.dir!=='asc'; th.dataset.dir=asc?'asc':'desc';
        rows.sort(function(a,b){ return (parseFloat(a.dataset[k])-parseFloat(b.dataset[k]))*(asc?1:-1); });
        rows.forEach(function(r){ body.appendChild(r); });
      });
    });
    filter('shortlist');
  });
})();
'''

CSS = CSS + CSS_EXTRA

RUN = '''
<div class="run" id="{rid}" role="tabpanel" hidden>
  <header class="hero">
    <div>
      <div class="eyebrow">Search {n} · Facebook Marketplace · {date}</div>
      <h1 style="margin-top:10px">{label}</h1>
      <span class="budget">Budget {budget}</span>
      <p class="lede">{search}. Every listing was narrowed to <strong>reliable economy models</strong>, then each listing
      page and seller profile was re-read for <strong>real mileage, title status, ratings and reviews</strong>.</p>
    </div>
    <div class="facts">
      <div><b class="num">{n_scraped}</b><span>listings scraped</span></div>
      <div><b class="num">{n_reliable}</b><span>reliable models checked</span></div>
      <div><b class="num">{n_clean}</b><span>no red flags</span></div>
      <div><b class="num">{n_picks}</b><span>worth a message</span></div>
    </div>
  </header>

  <section id="{rid}-picks">
    <div class="sec-head"><h2>Message these first</h2>
      <p>Ranked by value, seller trust and distance from Marietta. Tap a photo to open the listing.</p></div>
    <div class="grid">{top}</div>
  </section>
  {backups}
  {areas}
  <section id="{rid}-all" class="all">
    <div class="sec-head"><h2>All reliable models</h2>
      <div class="seg" role="group" aria-label="Filter">
        <button type="button" data-f="shortlist" aria-pressed="true">No red flags</button>
        <button type="button" data-f="clean" aria-pressed="false">Clean title</button>
        <button type="button" data-f="all" aria-pressed="false">Everything</button>
      </div></div>
    <p class="mute small" style="margin-bottom:10px">Showing <b class="shown num"></b> cars. Click Price or Miles to sort.</p>
    <div class="tbl"><table>
      <thead><tr><th></th><th>Car</th><th data-sort="price">Price ↕</th><th data-sort="miles">Miles ↕</th><th>Where</th><th>Seller</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </section>

  <section id="{rid}-rejected">
    <div class="sec-head"><h2>Rejected</h2><p>Looked good in the results, fell apart on the listing page or the seller's reviews.</p></div>
    <div class="rules">{rejects}</div>
    {multi}
  </section>
</div>
'''

PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Car Hunt</title>
<style>{css}</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="i-moon" viewBox="0 0 24 24"><path fill="currentColor" d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></symbol>
  <symbol id="i-sun" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></g></symbol>
  <symbol id="i-car" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3 15v-3l2-5a2 2 0 0 1 2-1.3h10A2 2 0 0 1 19 7l2 5v3a1 1 0 0 1-1 1h-1M5 16H4a1 1 0 0 1-1-1"/><path d="M4 12h16"/><circle cx="7.5" cy="16.5" r="2"/><circle cx="16.5" cy="16.5" r="2"/><path d="M9.5 16.5h5"/></g></symbol>
</svg>

<div class="top">
  <div class="wrap">
    <div class="brand"><svg><use href="#i-car"/></svg>Car Hunt</div>
    <nav class="tabs" aria-label="Sections">
      <a href="#picks" data-sec="picks">Picks</a><a href="#backups" data-sec="backups">Backups</a><a href="#all" data-sec="all">All cars</a><a href="#rejected" data-sec="rejected">Rejected</a><a href="#how" data-sec="how">How</a>
    </nav>
    <button class="toggle" id="themeBtn" type="button" aria-label="Toggle light and dark theme"><svg id="themeIcon"><use href="#i-moon"/></svg><span id="themeLabel">Dark</span></button>
  </div>
  <div class="wrap"><div class="runs" role="tablist" aria-label="Searches">{tabs}</div></div>
</div>

<main class="wrap">
{panels}
  <section id="how">
    <div class="sec-head"><h2>How these lists were made</h2></div>
    <ol class="how">
      <li>Searched Facebook Marketplace vehicles in narrow price slices from a logged-in browser, so no slice hit Facebook's result cap.</li>
      <li>Kept Toyota Corolla/Camry/Yaris/Prius/Matrix/Echo/RAV4, Honda Civic/Accord/Fit/CR-V, Mazda3/6/CX-5, Scion, Lexus ES and Hyundai Elantra; dropped salvage/rebuilt/not-running and buy-here-pay-here wording.</li>
      <li>Re-opened every remaining listing and read Facebook's own “About this vehicle” box and seller card.</li>
      <li>Flagged no stated clean title, sellers with several cars in the results, sold listings, over 190k miles, and impossible mileage.</li>
      <li>Opened each seller's Marketplace profile and read their star rating, live listing count and reviews. Flagged
        under 4.5★, 6+ active listings (a flipper, not an owner), and reviews that complain about mileage, emissions,
        scams or breakdowns.</li>
      <li>Left out every listing whose price is a down payment (“$2,500 down”, “pago inicial”, buy-here-pay-here); cars that are very cheap for their year are kept but flagged.</li>
      <li>Picked and ranked the finalists by hand; the reasons are on each card.</li>
    </ol>
    <div class="callout warn"><b>Not included:</b> a market-value comparison. The scraper's Edmunds lookup is switched off
      (Edmunds blocks it), so “good price” here is judgement, not a KBB number.</div>
  </section>
</main>
<footer><div class="wrap">Generated {generated} by <code>report/build_report.py</code>. One self-contained file: photos are saved copies, and listings may have sold since.</div></footer>
<script>{js}</script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', nargs=3, action='append', required=True, metavar=('SCRAPE', 'DETAILS', 'PICKS'),
                    help='one search: the scrape CSV, parse_details CSV and picks JSON; repeat per tab')
    ap.add_argument('--checks', help='JSON {listing id: [car-specific checks]} shown on each card')
    ap.add_argument('--best-order', help='JSON {"order": [{"id", "why"}]} ranking the All top picks tab')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    if a.checks:
        CHECKS.update({k: v for k, v in json.load(open(a.checks, encoding='utf-8')).items() if not k.startswith('_')})
    runs = [load(*r) for r in a.run]
    order = json.load(open(a.best_order, encoding='utf-8')) if a.best_order else None
    page = build(runs, order)
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f"Wrote {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB, {len(runs)} searches, "
          f"{sum(len(r[1]) for r in runs)} cars)")


if __name__ == "__main__":
    main()
