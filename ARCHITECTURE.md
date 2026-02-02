# Architecture Design - Facebook Marketplace Scraper 2026

## Problems with Old Script
1. **Brittle CSS Selectors:** Uses specific div classes like `'kbiprv82'` that break with every FB update
2. **Hardcoded Paths:** ChromeDriver path hardcoded
3. **Poor Error Handling:** Many try/except blocks that silently fail
4. **Inefficient:** Multiple browser instances, slow scrolling
5. **Limited Flexibility:** Hard to modify search parameters

## New Architecture Approach

### 1. **Robust Scraping Strategy**
Instead of relying on specific CSS classes, use:
- **Semantic HTML elements** (h2, h3, span with aria-labels)
- **Data attributes** (data-testid, aria-label)
- **Text pattern matching** (regex for prices, mileage)
- **Structural relationships** (parent-child DOM navigation)
- **Multiple fallback selectors** (try 3-4 different methods)

### 2. **Modern Tech Stack**
- **Selenium 4** with WebDriver Manager (auto-updates drivers)
- **BeautifulSoup4** for parsing (more flexible than direct Selenium selectors)
- **Requests** for Edmunds API calls (if available) or scraping
- **Pandas** for CSV output and data manipulation
- **Python 3.10+** with type hints

### 3. **Modular Design**
```
scraper/
├── __init__.py
├── config.py              # Settings, URLs, search params
├── facebook_scraper.py    # FB Marketplace scraping logic
├── price_comparator.py    # Edmunds/KBB price fetching
├── data_processor.py      # Clean, sort, calculate ratios
├── csv_exporter.py        # Output to CSV
└── utils.py               # Helper functions

main.py                    # Entry point
requirements.txt
README.md
```

### 4. **Key Features**

#### A. Facebook Scraper (`facebook_scraper.py`)
- Use multiple selector strategies with fallbacks
- Scroll intelligently (detect when no new content loads)
- Extract: Title, Price, Description, Mileage, Images, URL
- Handle pagination/infinite scroll
- Rate limiting to avoid detection

#### B. Price Comparator (`price_comparator.py`)
- Parse car details (year, make, model) from title
- Query Edmunds/KBB for fair market value
- Handle API rate limits
- Cache results to avoid redundant requests
- Multiple fallback strategies if one source fails

#### C. Data Processor (`data_processor.py`)
- Clean mileage data (handle "50k", "50,000", "50000 miles")
- Calculate deal ratio: `asking_price / fair_market_value`
- Sort by deal ratio (best deals first)
- Filter out invalid entries

#### D. CSV Exporter (`csv_exporter.py`)
- Output columns: `Deal_Ratio, Price, Title, Description, Mileage, Image_URLs, Listing_URL`
- Timestamp filename
- Handle special characters in descriptions

### 5. **Longevity Features**
- **Selector Hierarchy:** Try 5+ different ways to find each element
- **Graceful Degradation:** If images fail, continue with other data
- **Logging:** Detailed logs for debugging when selectors break
- **Config-Driven:** Easy to update selectors without code changes
- **Headless Mode:** Option to run without GUI for automation

### 6. **Configuration (`config.py`)**
```python
SEARCH_PARAMS = {
    'location': 'atlanta',
    'min_price': 250,
    'max_price': 55000,
    'min_mileage': 0,
    'max_mileage': 200000,
    'min_year': 1995,
    'max_year': 2025,
    'max_listings': 500  # Stop after N listings
}

SELECTORS = {
    'listing_container': [
        'div[data-testid="marketplace-listing"]',
        'div.x9f619',
        'div[role="article"]'
    ],
    'price': [
        'span[data-testid="listing-price"]',
        'span.x193iq5w',
        'span:contains("$")'
    ]
    # ... multiple fallbacks for each field
}
```

## Implementation Plan
1. Set up project structure
2. Implement robust Facebook scraper with fallback selectors
3. Implement Edmunds price comparison
4. Implement data processing and sorting
5. Implement CSV export
6. Add comprehensive error handling and logging
7. Test with various search parameters

## Success Criteria
- ✅ Scrapes 100+ listings without breaking
- ✅ Survives minor FB UI updates (test with different URLs)
- ✅ Outputs clean CSV with all required fields
- ✅ Sorts by deal ratio correctly
- ✅ Handles edge cases (missing mileage, weird prices)
