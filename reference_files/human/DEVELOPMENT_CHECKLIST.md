# Human Development Checklist - Facebook Marketplace Scraper 2026

**Your Role:** Project owner, requirements clarifier, tester, and reviewer.

**Workflow:** You guide the AI through investigation → confidence check → implementation → testing → review cycles.

**Note:** AI will track progress, decisions, and issues in their checklist as we work. A comprehensive development report will be generated at the end (Phase 5).

---

## Phase 1: Requirements & Investigation

### ☐ 1.1 Review Requirements
- [ ] Read `REQUIREMENTS.md` - Confirm all requirements are clear
- [ ] Read `ARCHITECTURE.md` - Understand the technical approach
- [ ] Check old script (`Facebook Car Scraper.py`) - Understand what worked/didn't work

### ☐ 1.2 Initiate AI Investigation
**→ Tell AI:** "Please start Phase 1 of the AI checklist - Requirements Investigation"

- [ ] Wait for AI to complete investigation
- [ ] Review AI's findings and questions
- [ ] Answer any clarification questions AI has

### ☐ 1.3 Clarify Requirements (If Needed)
**Questions to consider:**
- [ ] Which price comparison source? (Edmunds, KBB, or both?)
- [ ] How many listings to scrape? (100? 500? 1000?)
- [ ] Headless mode or visible browser?
- [ ] How to handle missing data? (Skip listing or include with N/A?)
- [ ] Image URLs: All images or just first one?

**→ Tell AI:** "Here are the clarifications: [your answers]"

---

## Phase 2: Confidence Assessment

### ☐ 2.1 Request Confidence Check
**→ Tell AI:** "Please complete Phase 2 - Confidence Assessment"

### ☐ 2.2 Review AI's Confidence Report
AI should provide:
- [ ] Confidence level (0-100%) for each component
- [ ] Known risks and uncertainties
- [ ] Areas needing more research

### ☐ 2.3 Decision Point
**If AI confidence < 80% on critical components:**
- [ ] **→ Tell AI:** "Please reinvestigate [specific area] before proceeding"
- [ ] Review additional findings
- [ ] Repeat until confidence ≥ 80%

**If AI confidence ≥ 80%:**
- [ ] **→ Tell AI:** "Confidence approved. Proceed to Phase 3 - Implementation"

---

## Phase 3: Implementation

### ☐ 3.1 Monitor Implementation Progress
**→ Tell AI:** "Begin implementation following your checklist"

AI will implement in stages:
- [ ] Stage 1: Project structure & dependencies
- [ ] Stage 2: Configuration system
- [ ] Stage 3: Facebook scraper (core)
- [ ] Stage 4: Price comparator
- [ ] Stage 5: Data processor & CSV exporter
- [ ] Stage 6: Main entry point

### ☐ 3.2 Review Each Stage
After each stage:
- [ ] Review code changes AI made
- [ ] Check for any obvious issues
- [ ] **→ Tell AI:** "Stage [N] looks good, continue" OR "I have concerns about [X]"

---

## Phase 4: Testing

### ☐ 4.1 Request AI Testing
**→ Tell AI:** "Please complete Phase 4 - Testing & Validation"

### ☐ 4.2 Manual Testing
**Test 1: Basic Functionality**
- [ ] Run the scraper with default settings
- [ ] Verify it completes without crashing
- [ ] Check CSV output exists

**Test 2: Data Quality**
- [ ] Open CSV file
- [ ] Verify all columns present: `Deal_Ratio, Price, Title, Description, Mileage, Image_URLs, Listing_URL`
- [ ] Check data looks reasonable (no obvious errors)
- [ ] Verify sorting (best deals first)

**Test 3: Edge Cases**
- [ ] Try with different search parameters (different price ranges, locations)
- [ ] Check how it handles listings with missing mileage
- [ ] Check how it handles listings with weird prices (e.g., "$1,234")

**Test 4: Longevity Check**
- [ ] Review the selectors used in `facebook_scraper.py`
- [ ] Confirm multiple fallback strategies are in place
- [ ] Check logs for any selector failures

### ☐ 4.3 Report Issues
**If issues found:**
- [ ] Document specific issues clearly
- [ ] **→ Tell AI:** "Testing revealed these issues: [list issues]"
- [ ] **→ Tell AI:** "Please fix these issues and return to Phase 4"

**If no issues:**
- [ ] **→ Tell AI:** "All tests passed! Proceed to Phase 5 - Documentation"

---

## Phase 5: Documentation & Finalization

### ☐ 5.1 Request Final Documentation
**→ Tell AI:** "Please complete Phase 5 - Documentation"

### ☐ 5.2 Review Documentation
- [ ] Read updated `README.md` - Clear setup instructions?
- [ ] Check `USAGE.md` - Easy to understand?
- [ ] Review `DEVELOPMENT_REPORT.md` - Complete project history?
- [ ] Review code comments - Adequate explanations?

### ☐ 5.3 Final Checks
- [ ] All files committed to git branch `revamp-2026`
- [ ] No sensitive data in code (API keys, passwords, etc.)
- [ ] `requirements.txt` is complete
- [ ] Old script preserved on `main` branch

### ☐ 5.4 Project Complete
- [ ] **→ Tell AI:** "Project approved! Thank you!"
- [ ] Merge `revamp-2026` branch to `main` (if desired)
- [ ] Archive old script for historical reference

---

## Quick Reference

**Start AI Phase:**
- Phase 1: "Please start Phase 1 of the AI checklist - Requirements Investigation"
- Phase 2: "Please complete Phase 2 - Confidence Assessment"
- Phase 3: "Confidence approved. Proceed to Phase 3 - Implementation"
- Phase 4: "Please complete Phase 4 - Testing & Validation"
- Phase 5: "Please complete Phase 5 - Documentation"

**Common Commands:**
- "Continue to next stage"
- "I have concerns about [X]"
- "Please reinvestigate [specific area]"
- "Testing revealed these issues: [list]"
- "All tests passed!"

---

## Notes Section
Use this space to track decisions, issues, or observations:

```
[Date] - [Note]
Example:
2026-02-02 - Decided to use Edmunds only (KBB too unreliable)
2026-02-02 - Max listings set to 500 for performance
```
