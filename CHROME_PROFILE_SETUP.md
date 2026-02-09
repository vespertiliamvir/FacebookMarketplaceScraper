# Chrome Profile Setup Guide

## Why Use Your Chrome Profile?

Using your existing Chrome profile allows the scraper to:
- ✅ **Bypass Facebook login** - You're already logged in
- ✅ **Avoid 2FA issues** - No notification problems
- ✅ **Reduce bot detection** - Uses your real browser data
- ✅ **Save time** - No manual login needed

---

## Important: Close Chrome Before Running

**⚠️ CRITICAL: You MUST close ALL Chrome windows before running the scraper!**

The script will automatically check and warn you if Chrome is running.

---

## Finding Your Chrome Profile Path

### Method 1: Automatic (Default)
The scraper uses the default Windows Chrome profile location:
```
C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data
```

This works for 99% of users. **Try running the scraper first - it should just work!**

### Method 2: Manual Check (If Default Doesn't Work)

1. **Open Chrome** (your regular Chrome, not the scraper)
2. **Go to:** `chrome://version`
3. **Look for "Profile Path"** - it will show something like:
   ```
   C:\Users\david\AppData\Local\Google\Chrome\User Data\Default
   ```
4. **Note the profile name** at the end (usually "Default", but could be "Profile 1", "Profile 2", etc.)

### Method 3: If You Use Multiple Chrome Profiles

If you have multiple Chrome profiles (work, personal, etc.):

1. Make sure you're logged into Facebook in the profile you want to use
2. Check `chrome://version` in that profile to see which one it is
3. If it's not "Default", you'll need to modify the scraper

**To change the profile in the scraper:**
- Open: `scraper/facebook_scraper.py`
- Find line: `options.add_argument("--profile-directory=Default")`
- Change `Default` to your profile name (e.g., `Profile 1`)

---

## How to Run

1. **Close ALL Chrome windows**
2. **Run the scraper:**
   ```bash
   python main.py
   ```
   or double-click `Run_Scraper.bat`

3. **The browser will open using your profile**
4. **You should be automatically logged into Facebook**
5. **Scraping begins!**

---

## Troubleshooting

### "Chrome is running" Error
- Close ALL Chrome windows (check system tray too!)
- Make sure Chrome isn't running in the background
- Check Task Manager if needed

### Still Asking for Login
- Your Chrome profile might not be logged into Facebook
- Log in manually in your regular Chrome first
- Make sure you're using the correct profile (see Method 3 above)

### Profile Path Not Found
- Check if Chrome is installed in a custom location
- Verify the path exists: `C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data`
- If using Chrome Beta/Canary, the path will be different

---

## Advanced: Using a Different Browser

If you use Edge instead of Chrome:
- Edge profile path: `C:\Users\YOUR_USERNAME\AppData\Local\Microsoft\Edge\User Data`
- You'll need to modify the scraper to use Edge WebDriver instead

---

## Security Note

The scraper only **reads** your Chrome profile to access your Facebook session. It does not:
- ❌ Store your passwords
- ❌ Send data anywhere
- ❌ Modify your profile
- ❌ Access other websites

It simply uses your existing Facebook login to scrape Marketplace listings.
