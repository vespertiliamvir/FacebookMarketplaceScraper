# Testing Guide - Facebook Marketplace Scraper

**Phase 4: Testing & Validation**

This guide will walk you through testing the scraper to ensure everything works correctly.

---

## Prerequisites

### 1. Install Dependencies

Open a terminal in the `repo/` directory and run:

```bash
pip install -r requirements.txt
```

**Expected output:** All packages install successfully without errors.

**If you get errors:**
- Make sure you have Python 3.10+ installed
- Try: `python -m pip install --upgrade pip`
- Then retry the install command

---

## Test 1: Basic Functionality (Required)

**Goal:** Verify the scraper runs end-to-end without crashing.

### Steps:

1. Open terminal in `repo/` directory
2. Run: `python main.py`
3. Follow the interactive prompts:
   - **First run:** Set up your preferences (or press Enter to use defaults)
   - **Subsequent runs:** Choose option 1 to use saved settings
4. Let it run completely (may take 5-15 minutes)

### What to Check:

✅ **Browser opens** - Chrome/Edge browser window appears  
✅ **Facebook loads** - You see Facebook Marketplace  
✅ **Scrolling works** - Page scrolls automatically  
✅ **Progress updates** - Terminal shows "Found X listings"  
✅ **Price lookups** - Progress bar shows price comparisons  
✅ **CSV created** - File appears with timestamp name  
✅ **No crashes** - Program completes without errors  

### Expected Result:

```
======================================================================
✓ SCRAPING COMPLETE!
======================================================================

Next Steps:
  1. Open the CSV file: facebook_marketplace_scrape_YYYYMMDD_HHMMSS.csv
  ...
```

**If it crashes:** Note the error message and report it.

---

## Test 2: CSV Data Quality (Required)

**Goal:** Verify the CSV output has correct data.

### Steps:

1. Open the generated CSV file (Excel, Google Sheets, or text editor)
2. Check the columns

### What to Check:

✅ **All columns present:**
- Deal_Ratio
- Price
- Title
- Description
- Mileage
- Image_URLs
- Listing_URL
- Fair_Market_Price
- Year
- Make
- Model

✅ **Data looks reasonable:**
- Prices are formatted: "$12,500.00"
- Deal ratios are numbers: "1.234" or "N/A"
- Titles have car info: "2015 Honda Civic"
- Mileage shows numbers or "999,999" (missing)
- URLs start with "https://www.facebook.com"

✅ **Sorting is correct:**
- First rows have highest Deal_Ratio values
- Listings without ratios are at the end

### Expected Result:

CSV has 50-500 rows (depending on your max_listings setting) with valid car data.

**If data looks wrong:** Note specific issues (e.g., "all prices show N/A").

---

## Test 3: Different Search Parameters (Optional)

**Goal:** Verify the scraper works with different settings.

### Steps:

1. Run: `python main.py`
2. Choose option 2 (Modify settings)
3. Try different values:
   - Different location (e.g., "Los Angeles" or "90210")
   - Different price range (e.g., $5,000-$20,000)
   - Different mileage range (e.g., 0-50,000)
4. Run the scraper

### What to Check:

✅ **Settings are saved** - Next run shows your new settings  
✅ **Results match filters** - Prices/mileage within your ranges  
✅ **Location works** - Listings from correct area  

---

## Test 4: Edge Cases (Optional)

**Goal:** Test how the scraper handles unusual situations.

### Test 4a: Very Restrictive Filters

Set filters that might return few results:
- Price: $1,000-$2,000
- Mileage: 0-10,000
- Year: 2023-2026

**Expected:** Scraper finds fewer listings but doesn't crash.

### Test 4b: Missing Data

Check how missing data is handled:
- Look for listings with "999,999" mileage
- Look for "N/A" in description or images

**Expected:** Missing data shows placeholders, not errors.

### Test 4c: Keyboard Interrupt

While scraper is running, press `Ctrl+C`

**Expected:** Program stops gracefully with message "Scraping cancelled by user"

---

## Common Issues & Solutions

### Issue 1: "No module named 'selenium'"

**Solution:** Run `pip install -r requirements.txt`

### Issue 2: Browser doesn't open

**Solution:** 
- Check if Chrome or Edge is installed
- Try running as administrator
- Check antivirus isn't blocking

### Issue 3: "No listings found"

**Solution:**
- Check your search parameters aren't too restrictive
- Try a different location
- Verify Facebook Marketplace is accessible in your region

### Issue 4: All prices show "N/A"

**Solution:**
- Edmunds might be blocking requests
- Check internet connection
- Try running again later (rate limiting)

### Issue 5: Scraper is very slow

**Solution:**
- This is normal! Price lookups take time
- Reduce max_listings to 100 for faster testing
- Each price lookup takes ~2-3 seconds

---

## Reporting Issues

If you encounter problems, please provide:

1. **Error message** (copy full text from terminal)
2. **What you were doing** (which test, what settings)
3. **CSV output** (if generated, check if data looks correct)
4. **Screenshots** (if helpful)

**Report format:**
```
Test: [Test name]
Issue: [Brief description]
Error: [Error message if any]
Settings: [Your search parameters]
```

---

## Success Criteria

**Minimum for success:**
- ✅ Test 1 passes (basic functionality works)
- ✅ Test 2 passes (CSV has valid data)
- ✅ At least 50 listings scraped
- ✅ At least 50% of listings have price data

**Ideal success:**
- ✅ All tests pass
- ✅ 200+ listings scraped
- ✅ 80%+ listings have price data
- ✅ No crashes or errors

---

## Next Steps After Testing

Once testing is complete:

1. **If all tests pass:** Report "All tests passed!" and we'll move to Phase 5 (Documentation)
2. **If issues found:** Report the issues and I'll fix them
3. **If partially working:** Report what works and what doesn't

---

**Ready to test? Run `python main.py` and let me know how it goes!** 🚀
