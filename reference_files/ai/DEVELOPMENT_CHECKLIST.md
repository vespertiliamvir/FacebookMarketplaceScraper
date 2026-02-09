# 🤖 AI Development Checklist - Facebook Marketplace Scraper 2026
*Linked with Human Checklist: `repo/reference_files/human/DEVELOPMENT_CHECKLIST.md`*

## 🧠 Phase 1: Algorithmic Scoring System
- [ ] `src/scoring/rules.py`: Define `GREEN_FLAGS`, `RED_FLAGS`, and weights
- [ ] `src/scoring/engine.py`: Implement `ScoringEngine` class
- [ ] `src/scraper/utils.py`: Add regex patterns for dealer detection
- [ ] `src/scraper/csv_exporter.py`: Add `Score` column and sorting logic

## 🚀 Phase 2: Parallel Execution
- [ ] `src/scraper/manager.py`: Create `ScraperManager` to handle process pool
- [ ] `src/scraper/worker.py`: Define worker entry point for individual browser
- [ ] `src/main.py`: Update CLI to accept `--workers` argument

## 🔍 Phase 3: URL & Filter Engineering
- [ ] `src/scraper/url_builder.py`: Reverse engineer new FB filter IDs
- [ ] `src/scraper/url_builder.py`: Implement robust make/model path generation

## 🧪 Phase 4: Integration
- [ ] Run `pytest` suite for scoring logic
- [ ] Manual verification of "Grid Search" coverage
