# Facebook Marketplace Scraper - Phase 2 Requirements Board

## 🚀 Epic 1: Multi-Browser Scalability
**Goal:** Increase scraping throughput from ~300/hr to ~1200/hr by running parallel browser instances.

### 🎫 TICKET-001: Parallel Driver Manager
- **Description:** Implement a manager that spins up N Chrome instances using Python `multiprocessing` or `concurrent.futures`.
- **Requirements:**
  - Configurable number of browsers (default: 4).
  - Each browser has a unique profile/session to avoid conflicts (if possible, or incognito).
  - Robust error handling: if one browser crashes, others continue.
  - Aggregated progress reporting (e.g., "Total: 150/4000").

### 🎫 TICKET-002: Location Grid Search
- **Description:** Instead of one fixed location, the scraper should handle a list of locations or "hop" around a grid.
- **Requirements:**
  - Input: List of Zip Codes or Lat/Long coordinates.
  - Logic: Assign different locations to different browsers.
  - Deduplication: Ensure the same listing isn't scraped twice (track Listing IDs globally).

---

## 🔍 Epic 2: Advanced Search & Filtering Fixes
**Goal:** Restore functionality of Make/Model filters and correct search radius.

### 🎫 TICKET-003: Fix URL Builder (Make/Model)
- **Problem:** "Toyota" search returns 0 results.
- **Task:** Reverse engineer the current FB Marketplace URL structure for Make/Model filtering.
- **Hypothesis:** FB might have changed from query params (`?make=toyota`) to path-based (`/marketplace/toyota-camry`) or filter IDs.

### 🎫 TICKET-004: Fix Search Radius
- **Problem:** Radius locked to 35 miles or incorrect.
- **Task:** Verify `radius` parameter in URL. Ensure accurate "pick-up" of listings within range.

---

## 🧠 Epic 3: Algorithmic Scoring System (Pre-Processing)
**Goal:** Sort listings by "Deal Quality" *before* AI analysis to save costs and prioritize best cars.

### 🎫 TICKET-005: Scoring Logic Engine
- **Description:** A post-scraping analysis step that assigns a `Score` (0-100) to each listing.
- **Scoring Rules (Draft):**
  - **Base Score:** 50
  - **Price/Value:** +10 if >20% below market (Deal Ratio).
  - **Seller:** 
    - +5 for "Likely Private" (Account >5 years, <3 listings).
    - -10 for "Dealer/Business".
    - -5 for "Possible Flipper".
  - **Description Keywords (Green Flags +3 each):**
    - "garage kept", "service records", "one owner", "clean title", "maintenance", "elderly", "highway miles".
  - **Description Keywords (Red Flags -10 each):**
    - "rebuilt", "salvage", "mechanic special", "parts only", "no title", "bill of sale only", "misfire", "leak".

### 🎫 TICKET-006: Enhanced Seller Profiling
- **Task:** Improve flipper detection.
- **Additions:**
  - Detect dealer keywords in description ("financing", "down payment", "www.", "LLC").
  - Detect phone number patterns (often used by dealers).

---

## 📂 Epic 4: Data Pipeline & Storage
### 🎫 TICKET-007: Consolidated CSV Export
- **Description:** Ensure all parallel workers merge data into a single, clean CSV.
- **Requirements:** 
  - Columns: Added `Score`, `Seller_Type`, `Green_Flags`, `Red_Flags`.
  - Auto-sort by `Score` descending.
