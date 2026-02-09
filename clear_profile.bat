@echo off
echo Clearing Facebook Scraper temporary profile...
rmdir /s /q "%USERPROFILE%\.facebook_scraper_profile"
echo Done! The profile has been cleared.
echo Next time you run the scraper, you'll get a fresh login prompt.
pause
