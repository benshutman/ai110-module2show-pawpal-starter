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
----------------------------------------------------
All tasks sorted by preferred time:
  07:30    Morning walk     [Mochi]
  08:00    Feeding          [Whiskers]
  08:15    Litter box       [Whiskers]
  14:00    Grooming         [Mochi]
  17:30    Playtime         [Whiskers]
----------------------------------------------------
Filtered — Whiskers' tasks:
  Playtime         [Whiskers] (not done)
  Litter box       [Whiskers] (done)
  Feeding          [Whiskers] (done)
----------------------------------------------------
Filtered — completed tasks:
  Litter box       [Whiskers] (done)
  Feeding          [Whiskers] (done)
====================================================
      🐾 PawPal+ — Today's Schedule for Jordan       
====================================================
Pets: Mochi (dog), Whiskers (cat)
----------------------------------------------------
  08:00  Feeding           10 min  [high]  (daily, done)
  08:10  Morning walk      30 min  [high]  (daily)
  08:40  Litter box         5 min  [medium]  (daily, done)
  08:45  Playtime          15 min  [medium]
----------------------------------------------------
Skipped (not enough time today):
  • Grooming          45 min  [low]
----------------------------------------------------
Summary: 4 task(s) scheduled, 60/60 minutes used.
====================================================
----------------------------------------------------
Recurrence automation:
  Completed 'Morning walk' — Mochi now has 3 task(s) (was 2).
  Next occurrence scheduled: 'Morning walk' due 2026-07-07.
----------------------------------------------------
Conflict check:
  ⚠ 'Morning walk' and 'Morning walk' both want 07:30.
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
collected 6 items

tests/test_pawpal.py ......                                              [100%]

============================== 6 passed in 0.01s ===============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Priority sorting | `Scheduler.sort_tasks()`, `Task.get_priority_value()` | Orders by priority (high→low), then recurring tasks, then shorter duration as a tie-break so more tasks fit the day. |
| Sorting behavior | `Scheduler.sort_by_time()` | Orders tasks by `preferred_time` ("HH:MM"); tasks with no preferred time are flexible and sort last. |
| Filtering behavior | `Scheduler.filter_tasks()` | Filters a task list by pet name and/or completion status, independently or together. |
| Conflict detection logic | `Scheduler.detect_conflicts()` | Flags any pair of tasks that share the exact same `preferred_time`. Exact-match only, not true overlapping-duration detection — see `reflection.md` section 2b for that tradeoff. |
| Recurring task logic | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a `daily`/`weekly` task automatically creates and attaches its next occurrence (due one interval past today) to the same pet. |
| Greedy scheduling | `Scheduler.build_schedule()` | Packs the priority-sorted list into the day sequentially, skipping any task that doesn't fit the remaining `available_minutes`. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
