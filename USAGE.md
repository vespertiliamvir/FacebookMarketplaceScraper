# Usage Guide - Facebook Marketplace Car Scraper

Detailed guide for using the scraper effectively.

---

## Table of Contents

1. [First Time Setup](#first-time-setup)
2. [Running the Scraper](#running-the-scraper)
3. [Configuring Search Parameters](#configuring-search-parameters)
4. [Understanding the Output](#understanding-the-output)
5. [Advanced Tips](#advanced-tips)
6. [Common Workflows](#common-workflows)

---

## First Time Setup

### Step 1: Install Dependencies

```bash
cd "path/to/repo"
pip install -r requirements.txt
```

This installs:
- Selenium (browser automation)
- BeautifulSoup (HTML parsing)
- Pandas (CSV handling)
- WebDriver Manager (automatic driver updates)
- Colorama & tqdm (UI enhancements)

### Step 2: Verify Installation

```bash
python test_validation.py
```

You should see: `✓ ALL VALIDATION TESTS PASSED`

---

## Running the Scraper

### Basic Run

```bash
python main.py
```

### What Happens:

**Step 1: Configure Preferences**
- First run: Interactive setup wizard
- Subsequent runs: Use saved settings or modify

**Step 2: Scrape Facebook**
- Browser opens (visible)
- Navigates to Facebook Marketplace
- Scrolls to load listings
- Extracts data from each listing

**Step 3: Fetch Prices**
- Looks up fair market values on Edmunds
- Shows progress bar
- Caches results for future runs

**Step 4: Process Data**
- Calculates deal ratios
- Sorts by best deals first
- Filters invalid listings

**Step 5: Export CSV**
- Creates timestamped CSV file
- Shows summary of results

---

## Configuring Search Parameters

### Location Settings

**Location:** City name or zip code
- Examples: "Atlanta", "90210", "New York"
- Used to build Facebook Marketplace URL

**Search Radius:** Miles from location
- Default: 50 miles
- Range: 1-500 miles
- Larger radius = more listings but less local

### Price Range

**Minimum Price:** Lowest acceptable price
- Default: $250
- Set to 0 for no minimum
- Filters out very cheap/scam listings

**Maximum Price:** Highest acceptable price
- Default: $55,000
- Adjust based on your budget
- Higher = more luxury vehicles included

### Mileage Range

**Minimum Mileage:** Lowest acceptable mileage
- Default: 0
- Usually leave at 0 unless you want high-mileage only

**Maximum Mileage:** Highest acceptable mileage
- Default: 200,000
- Lower for newer cars (e.g., 50,000)
- Higher for older/budget cars

### Year Range

**Minimum Year:** Oldest acceptable year
- Default: 1995
- Adjust based on preferences
- Older = more budget options

**Maximum Year:** Newest acceptable year
- Default: 2026 (current year)
- Set to specific year for used-only search

### Vehicle Filters (Optional)

**Make:** Specific manufacturer
- Examples: "Honda", "Toyota", "Ford"
- Leave blank for all makes
- Case-insensitive

**Model:** Specific model
- Examples: "Civic", "Camry", "F-150"
- Leave blank for all models
- Requires make to be set

### Scraping Settings

**Max Listings:** Stop after N listings
- Default: 500
- Lower for faster testing (e.g., 100)
- Higher for comprehensive search (e.g., 1000)
- More listings = longer runtime

---

## Understanding the Output

### CSV File Structure

**Filename:** `facebook_marketplace_scrape_YYYYMMDD_HHMMSS.csv`

**Columns:**

1. **Deal_Ratio** - Fair price / Asking price
   - Higher = better deal
   - "N/A" = no price data available

2. **Price** - Asking price
   - Format: "$12,500.00"

3. **Title** - Listing title
   - Usually: "YYYY Make Model Trim"

4. **Description** - Seller's description
   - "N/A" if not provided

5. **Mileage** - Odometer reading
   - Format: "50,000"
   - "999,999" = not listed

6. **Image_URLs** - All image URLs
   - Pipe-separated: "url1|url2|url3"
   - "N/A" if no images

7. **Listing_URL** - Facebook link
   - Click to view full listing

8. **Fair_Market_Price** - Edmunds value
   - Format: "$14,200.00"
   - "N/A" if lookup failed

9. **Year** - Vehicle year
   - Parsed from title

10. **Make** - Vehicle manufacturer
    - Parsed from title

11. **Model** - Vehicle model
    - Parsed from title

### Interpreting Deal Ratios

**Excellent Deals (1.2+)**
- 20%+ below market value
- Investigate thoroughly
- May be motivated seller or needs work

**Good Deals (1.1-1.2)**
- 10-20% below market
- Worth pursuing
- Likely fair pricing

**Fair Price (0.9-1.1)**
- Near market value
- Standard pricing
- Negotiate for better deal

**Overpriced (<0.9)**
- Above market value
- Avoid unless special circumstances
- Seller may not be realistic

**No Ratio (N/A)**
- Price lookup failed
- Title couldn't be parsed
- Manual research needed

---

## Advanced Tips

### Optimizing Search Parameters

**For Best Deals:**
- Set wide price range
- Set wide mileage range
- Include older years
- Don't filter by make/model
- High max_listings (500+)

**For Specific Car:**
- Set make and model
- Narrow year range
- Adjust price to expected range
- Lower max_listings (100-200)

**For Quick Test:**
- Set max_listings to 50
- Use saved preferences
- Check one location

### Using Cached Data

**Price cache** (`price_cache.pkl`) stores Edmunds lookups.

**Benefits:**
- Faster re-runs
- Avoids rate limiting
- Consistent pricing

**When to clear cache:**
- Prices seem outdated (>1 month old)
- Testing changes
- Delete file: `price_cache.pkl`

### Modifying Preferences

**Option 1: Interactive**
- Run `python main.py`
- Choose "Modify settings"
- Change specific values

**Option 2: Edit File**
- Open `scraper_preferences.json`
- Edit values directly
- Save file

**Option 3: Delete & Restart**
- Delete `scraper_preferences.json`
- Run scraper
- Set up from scratch

### Analyzing Results

**In Excel/Google Sheets:**
1. Open CSV file
2. Sort by Deal_Ratio (descending)
3. Filter by price range
4. Filter by mileage
5. Review top 10-20 listings

**In Python/Pandas:**
```python
import pandas as pd
df = pd.read_csv('facebook_marketplace_scrape_20260202_120000.csv')
df = df[df['Deal_Ratio'] != 'N/A']
df['Deal_Ratio'] = df['Deal_Ratio'].astype(float)
top_deals = df.nlargest(10, 'Deal_Ratio')
print(top_deals[['Title', 'Price', 'Deal_Ratio']])
```

---

## Common Workflows

### Workflow 1: Daily Deal Hunting

1. Run scraper with saved settings
2. Sort CSV by Deal_Ratio
3. Check top 5-10 deals
4. Visit Facebook listings
5. Contact sellers for best deals

**Frequency:** Daily or every few days

### Workflow 2: Specific Car Search

1. Set make and model filters
2. Set realistic price range
3. Set max_listings to 200
4. Run scraper
5. Review all results
6. Compare with other sources

**Frequency:** When ready to buy

### Workflow 3: Market Research

1. Set wide parameters
2. Set high max_listings (500+)
3. Run scraper
4. Analyze price trends
5. Identify undervalued segments

**Frequency:** Monthly or quarterly

### Workflow 4: Multi-Location Search

1. Run scraper for Location A
2. Save CSV as "location_a.csv"
3. Change location to Location B
4. Run scraper again
5. Save CSV as "location_b.csv"
6. Compare results

**Frequency:** When willing to travel

---

## Troubleshooting

### Scraper Stops Early

**Possible causes:**
- Reached max_listings
- No more listings available
- Facebook changed UI

**Solutions:**
- Check terminal output for errors
- Try different search parameters
- Check `scraper.log` for details

### Missing Price Data

**Possible causes:**
- Edmunds doesn't have data for that car
- Title parsing failed
- Rate limiting

**Solutions:**
- Check if title is formatted correctly
- Reduce max_listings
- Wait and try again later

### Slow Performance

**Expected behavior:**
- 2-3 seconds per price lookup
- 5-15 minutes for 500 listings

**To speed up:**
- Reduce max_listings
- Use cached data (re-run)
- Disable price comparison (modify code)

---

## Best Practices

1. **Start broad, filter later** - Easier to filter CSV than re-scrape
2. **Run regularly** - New deals appear daily
3. **Verify listings** - Always check Facebook before contacting
4. **Research thoroughly** - Deal ratio is just one factor
5. **Be patient** - Good deals take time to find
6. **Act fast** - Best deals go quickly
7. **Negotiate** - Even good deals can be better
8. **Get inspection** - Never skip pre-purchase inspection

---

## FAQ

**Q: How often should I run the scraper?**
A: Daily if actively searching, weekly for casual browsing.

**Q: Can I scrape multiple locations?**
A: Yes, run separately for each location and save different CSV files.

**Q: Why do some listings show 999,999 mileage?**
A: Seller didn't list mileage. Check Facebook listing for details.

**Q: Can I filter by transmission or other features?**
A: Not currently. Filter the CSV manually or check descriptions.

**Q: Is this legal?**
A: For personal use, yes. Don't use for commercial purposes.

**Q: Can I run this on a schedule?**
A: Yes, use Task Scheduler (Windows) or cron (Linux/Mac).

**Q: What if Facebook changes their website?**
A: The scraper uses multiple fallback selectors for longevity, but may need updates eventually.

---

**Need more help? Check `TESTING_GUIDE.md` or `README.md`**
