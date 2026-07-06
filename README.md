# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running the demo script exercises the logic layer end to end and prints a daily plan
built across all of the owner's pets:

```bash
python main.py
```

```
====================================================
      🐾 PawPal+ — Today's Schedule for Jordan       
====================================================
Pets: Mochi (dog), Whiskers (cat)
----------------------------------------------------
  08:00  Feeding           10 min  [high]  (recurring)
  08:10  Morning walk      30 min  [high]  (recurring)
  08:40  Litter box         5 min  [medium]  (recurring)
  08:45  Playtime          15 min  [medium]
----------------------------------------------------
Skipped (not enough time today):
  • Grooming          45 min  [low]
----------------------------------------------------
Summary: 4 task(s) scheduled, 60/60 minutes used.
====================================================
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.1.1, pluggy-1.6.0
rootdir: .../ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 2 items

tests/test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.01s ===============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Task.get_priority_value()` | Orders by priority (high→low), then recurring essentials, then shorter duration as a tie-break. |
| Filtering | `Scheduler.build_schedule()` | Greedy time budget — skips any task whose duration exceeds the remaining `available_minutes`. |
| Conflict handling | `Scheduler.build_schedule()` | Overlaps are avoided by construction: each task's start time is the previous task's end, so no two slots collide. |
| Recurring tasks | `Scheduler.sort_tasks()`, `Task.describe()` | `Task.recurring` flag boosts recurring tasks in the sort tie-break so daily essentials aren't dropped ahead of one-offs; `describe()` labels them `(recurring)`. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
