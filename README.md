# Facebook Marketplace Car Scraper - 2026 Edition

**Find the best car deals with AI-powered price comparison**

A robust, user-friendly scraper that finds undervalued cars on Facebook Marketplace by comparing asking prices with fair market values from Edmunds.com.

---

## ✨ Features

- **🔍 Smart Scraping** - Multiple fallback selectors survive Facebook UI changes
- **💰 Price Comparison** - Automatic fair market value lookups from Edmunds
- **📊 Deal Ranking** - Sorts listings by deal ratio (best deals first)
- **💾 Caching** - Saves price lookups to avoid redundant requests
- **🎨 User-Friendly** - Colorful terminal UI with progress indicators
- **⚙️ Configurable** - Save search preferences for quick re-runs
- **📁 CSV Export** - Clean, structured data ready for analysis

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Chrome or Edge browser installed
- Internet connection

### Installation

1. **Clone or download this repository**

2. **Navigate to the repo directory:**
   ```bash
   cd "path/to/Facebook Marketplace Web Scraper Revamp 2026/repo"
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

**Run the scraper:**
```bash
python main.py
```

**Follow the interactive prompts:**
- First run: Configure your search preferences
- Subsequent runs: Use saved settings or modify them

**Wait for completion** (5-15 minutes depending on settings)

**Open the CSV file** to see your results!

---

## 📋 What Gets Scraped

**From Facebook Marketplace:**
- Title (year, make, model)
- Asking price
- Description
- Mileage
- Images (all URLs)
- Listing URL

**From Edmunds.com:**
- Fair market value
- Deal ratio calculation

**Output CSV Columns:**
- Deal_Ratio (higher = better deal)
- Price
- Title
- Description
- Mileage (999,999 = not listed)
- Image_URLs (pipe-separated)
- Listing_URL
- Fair_Market_Price
- Year, Make, Model

---

## ⚙️ Configuration

### Search Parameters

Configure via interactive prompts:
- **Location** - City name or zip code
- **Search Radius** - Miles from location
- **Price Range** - Min/max asking price
- **Mileage Range** - Min/max mileage
- **Year Range** - Min/max year
- **Make/Model** - Optional filters
- **Max Listings** - Stop after N listings (default: 500)

### Preferences File

Settings are saved to `scraper_preferences.json` and automatically loaded on subsequent runs.

---

## 📊 Understanding Deal Ratios

**Deal Ratio = Fair Market Price / Asking Price**

- **> 1.2** - Excellent deal (20%+ below market)
- **1.1 - 1.2** - Good deal (10-20% below market)
- **0.9 - 1.1** - Fair price (near market value)
- **< 0.9** - Overpriced (above market value)

**Example:**
- Car asking $10,000
- Fair market value $12,000
- Deal ratio = 1.2 (20% below market - great deal!)

---

## 🛠️ Troubleshooting

### "No module named 'selenium'"
**Solution:** Run `pip install -r requirements.txt`

### Browser doesn't open
**Solution:** 
- Ensure Chrome or Edge is installed
- Try running as administrator
- Check antivirus settings

### "No listings found"
**Solution:**
- Check search parameters aren't too restrictive
- Try different location
- Verify Facebook Marketplace is accessible

### All prices show "N/A"
**Solution:**
- Edmunds may be rate limiting
- Check internet connection
- Try again later or reduce max_listings

### Scraper is slow
**Solution:**
- This is normal! Each price lookup takes 2-3 seconds
- Reduce max_listings for faster testing
- Use cached results on re-runs

---

## 📁 Project Structure

```
repo/
├── scraper/
│   ├── config.py              # Settings and selectors
│   ├── utils.py               # Helper functions
│   ├── preferences.py         # Preference management
│   ├── facebook_scraper.py    # FB Marketplace scraper
│   ├── price_comparator.py    # Edmunds price lookup
│   ├── data_processor.py      # Data cleaning and sorting
│   └── csv_exporter.py        # CSV export
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── TESTING_GUIDE.md          # Testing instructions
├── USAGE.md                  # Detailed usage guide
└── ARCHITECTURE.md           # Technical documentation
```

---

## 🔧 Advanced Usage

### Custom Configuration

Edit `scraper/config.py` to customize:
- Scroll behavior
- Rate limiting delays
- Selector strategies
- Output format

### Caching

Price lookups are cached in `price_cache.pkl`. Delete this file to force fresh lookups.

### Logging

Logs are saved to `scraper.log` for debugging.

---

## 📝 Tips for Best Results

1. **Start with broad filters** - You can always filter the CSV later
2. **Use realistic price ranges** - Too narrow = fewer results
3. **Check multiple locations** - Deals vary by region
4. **Run regularly** - New listings appear daily
5. **Sort by Deal_Ratio** - Focus on best deals first
6. **Verify listings** - Always check the actual Facebook listing before purchasing

---

## 🤝 Contributing

This is a personal project, but feel free to fork and modify for your own use!

---

## ⚠️ Disclaimer

This tool is for personal use only. Please respect Facebook's Terms of Service and use responsibly. The author is not responsible for any misuse of this tool.

Price data from Edmunds is for reference only. Always do your own research before purchasing a vehicle.

---

## 📄 License

This project is provided as-is for personal use.

---

## 🎯 Version

**2.0.0** - 2026 Revamp Edition

Built with longevity in mind - designed to survive Facebook UI changes.

---

**Happy car hunting! 🚗💨**
