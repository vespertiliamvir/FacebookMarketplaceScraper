# Reference Files - Development Workflow

This folder contains synchronized checklists for collaborative human-AI development.

## Structure

```
reference_files/
├── human/
│   └── DEVELOPMENT_CHECKLIST.md    # Your checklist (project owner)
├── ai/
│   └── DEVELOPMENT_CHECKLIST.md    # AI's checklist (implementation)
└── README.md                        # This file
```

## How to Use

### For Humans (You)
1. Open `human/DEVELOPMENT_CHECKLIST.md`
2. Follow the phases sequentially
3. Each phase tells you when to prompt the AI
4. Review AI's work at each checkpoint
5. Provide feedback and approvals

### For AI (Assistant)
1. Wait for human to initiate each phase
2. Follow `ai/DEVELOPMENT_CHECKLIST.md`
3. Report progress after each stage
4. Wait for human approval before proceeding
5. Document decisions in notes section

## Workflow Overview

**Phase 1: Requirements & Investigation**
- AI investigates requirements and asks clarifying questions
- Human provides clarifications

**Phase 2: Confidence Assessment**
- AI assesses confidence in each component (must be ≥80%)
- Human approves or requests more investigation

**Phase 3: Implementation**
- AI implements in 6 stages (structure → config → scraper → comparator → processor → integration)
- Human reviews each stage

**Phase 4: Testing & Validation**
- AI prepares tests
- Human runs manual tests and reports results
- AI fixes issues if found

**Phase 5: Documentation & Finalization**
- AI creates comprehensive documentation
- Human reviews and approves final deliverable

## Quick Start

**Human:** Open `human/DEVELOPMENT_CHECKLIST.md` and start at Phase 1.1

**AI:** Wait for human to say: *"Please start Phase 1 of the AI checklist - Requirements Investigation"*

## Communication Protocol

The checklists reference each other with clear handoff points:
- Human checklist tells you when to prompt AI
- AI checklist tells AI when to report back to you
- Both checklists have "→ Tell [Human/AI]:" prompts for synchronization

## Notes

- Both checklists have a notes section at the bottom for tracking decisions
- Use these to document important choices, issues, or observations
- This creates a development log for future reference
