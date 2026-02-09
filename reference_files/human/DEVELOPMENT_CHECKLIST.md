# 📋 Development Checklist - Facebook Marketplace Scraper 2026
*Linked with AI Checklist: `repo/reference_files/ai/DEVELOPMENT_CHECKLIST.md`*

## 🧠 Phase 1: Algorithmic Scoring System (Pre-Processing)
**Goal:** Sort listings by "Deal Quality" before AI analysis.
- [x] **Define Scoring Rules**
  - [x] Create dictionary of "Green Flag" keywords (e.g., "garage kept", "service records")
  - [x] Create dictionary of "Red Flag" keywords (e.g., "rebuilt", "part out")
  - [x] Define point values for Price, Seller Type, and Keywords
- [x] **Enhance Seller Profiling**
  - [x] Add dealer keyword detection (e.g., "LLC", "financing", website URLs)
  - [x] Add phone number pattern detection
- [x] **Implement Scoring Engine**
  - [x] Create `ScoringEngine` class
  - [x] Implement `calculate_score(listing)` method
  - [x] Update `CSVExporter` to include `Score` and sort by it

## 🚀 Phase 2: Multi-Browser Scalability
**Goal:** Increase scraping speed by 4x.
- [x] **Architecture Design**
  - [x] Design `ParallelScraperManager` class
  - [x] Determine best method: `multiprocessing` vs `concurrent.futures`
- [x] **Profile Management**
  - [x] Create system to generate/manage multiple Chrome profiles
  - [x] Ensure unique sessions for each browser
- [x] **Integration**
  - [x] Update main loop to dispatch jobs to workers
  - [x] Implement result aggregation (merge results from all browsers)

## 🔍 Phase 3: Advanced Search Fixes
**Goal:** Fix "Toyota" search and Radius issues.
- [x] **Fix Make/Model Search**
  - [x] Investigate new Facebook URL structure for filters
  - [x] Update `FacebookUrlBuilder` to support new format
- [x] **Fix Search Radius**
  - [x] Verify `radius` parameter behavior
  - [ ] Implement "Grid Search" (hopping locations) if radius is broken

## 🧪 Phase 4: Testing & Validation
- [x] Unit tests for Scoring Engine
- [x] Stress test Multi-Browser (2 workers)
- [x] Suppress Google Login/Welcome Popups in Chrome Drivers
- [x] Verify CSV output contains all new columns and sorted data
- [x] Fix Parallel Window Grid & Race Conditions (Staggered Launch)
- [x] Implement "Master Profile" Login Strategy (Solves Login Loops)
- [x] Fix UnicodeEncodeError (Remove Emojis for Windows Compatibility)
