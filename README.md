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
python -m pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/benjaminshutman/Codepath x Anthropic Summer 2026/Codepath-x-Anthropic/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 27 items

tests/test_pawpal.py ...........................                         [100%]

============================== 27 passed in 0.01s ===============================
```

**Test coverage:**

- **Input validation** — `preferred_time` is normalized to zero-padded `"HH:MM"` (e.g. `"7:30"` → `"07:30"`) so sorting/conflict comparisons stay correct regardless of how it's typed; malformed values raise `ValueError` instead of silently corrupting results.
- **Task completion** — `mark_complete()` flips `completion_status` from `False` to `True`.
- **Task addition** — adding tasks to a `Pet` increases its task count.
- **Recurring automation** — completing a `daily`/`weekly` task creates a correctly-dated next occurrence on the same pet; completing a non-recurring task creates nothing; completing an already-completed task a second time doesn't duplicate the next occurrence.
- **Conflict detection** — tasks whose `[preferred_time, preferred_time + duration)` ranges overlap are flagged, even at different start times; back-to-back tasks that only touch, tasks with no preferred time, and an empty task list never conflict.
- **Sorting** — `sort_by_time()` orders tasks chronologically by `preferred_time`, with flexible (no-time) tasks sorted last and ties/all-flexible lists keeping their original order (stable sort).
- **Filtering** — `filter_tasks()` narrows a pooled task list by pet name, by completion status, or both at once; unmatched filters and empty input return an empty list.
- **Greedy scheduling** — `build_schedule()` schedules tasks that fit the time budget and skips the rest, including the exact-fit boundary, a zero-minute budget, an empty task list, and wrapping the clock past midnight.

**Confidence Level:** ⭐⭐⭐⭐⭐ (5/5)

All 27 tests pass, covering every algorithmic feature's happy path plus real edge cases (empty lists, ties, exact-fit boundaries, midnight wraparound, double-completion, malformed input) — and writing the edge cases actually caught a real bug (`mark_task_complete()` could double-schedule a recurring task before a guard was added). The two gaps flagged in an earlier pass — exact-time-only conflict detection and unvalidated `preferred_time` input — are now closed: `detect_conflicts()` does real interval-overlap math, and `Task.__post_init__` validates/normalizes `preferred_time` at construction time, with `app.py` catching the resulting `ValueError` gracefully. One small, deliberately-accepted limitation remains: overlap checks don't span midnight (a task at "23:50" isn't checked against next-day tasks) — see `reflection.md` §2b for why that's an acceptable tradeoff for a daily pet-care scheduler.

## 🧩 System Design

PawPal+ is built around four classes:

- **`Owner`** — the pet owner using the app. Holds their name, preferences, and the list of `Pet`s they manage. `get_all_tasks()` pools every pet's tasks into one flat list so the `Scheduler` can plan across all of an owner's pets at once.
- **`Pet`** — a single pet (name, species, age) and its list of `Task`s. `add_task()` stamps each task with the pet's name so a pooled task list can still be traced back to which pet it belongs to.
- **`Task`** — one care task: title, description, duration, priority, due date, recurrence (`"none"`/`"daily"`/`"weekly"`), an optional preferred time of day, and completion status. A task controls its own state — `mark_complete()` is the only way to flip `completion_status`, and `next_occurrence()` builds the task's next instance if it recurs.
- **`Scheduler`** — takes a pool of tasks and a daily time budget. It can sort tasks (by priority or by time), filter them (by pet or status), detect basic scheduling conflicts, mark a task complete (auto-scheduling its next occurrence if it recurs), and greedily build/explain a day's plan that fits the available time.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Priority sorting | `Scheduler.sort_tasks()`, `Task.get_priority_value()` | Orders by priority (high→low), then recurring tasks, then shorter duration as a tie-break so more tasks fit the day. |
| Sorting behavior | `Scheduler.sort_by_time()` | Orders tasks by `preferred_time` ("HH:MM"); tasks with no preferred time are flexible and sort last. |
| Filtering behavior | `Scheduler.filter_tasks()` | Filters a task list by pet name and/or completion status, independently or together. |
| Conflict detection logic | `Scheduler.detect_conflicts()` | Flags any pair of tasks whose `[preferred_time, preferred_time + duration)` ranges truly overlap, even at different start times. Compares within a single day only — see `reflection.md` section 2b for that remaining tradeoff. |
| Recurring task logic | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a `daily`/`weekly` task automatically creates and attaches its next occurrence (due one interval past today) to the same pet. Guards against double-completion creating a duplicate occurrence. |
| Greedy scheduling | `Scheduler.build_schedule()` | Packs the priority-sorted list into the day sequentially, skipping any task that doesn't fit the remaining `available_minutes`. |
| Input validation | `Task.__post_init__()` | Normalizes `preferred_time` to zero-padded `"HH:MM"` (e.g. `"7:30"` → `"07:30"`) and raises `ValueError` on malformed input, so `app.py` can catch it and show `st.error()` instead of crashing. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
