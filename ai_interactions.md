# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I wanted to limit my scope, so I am describing the implementation of the first stretch goal. The prompt I fed it was long: "Implement a third algorithmic capability beyond the core requirements — "next available slot" — for the `Scheduler` class (Challenge 1), wire it into the Streamlit UI as a "Suggest a time" button on the Add Task form, and add tests for both the backend method and the UI behavior, without breaking anything already working."

**Files modified** *(the general pattern across the whole agent session, not just this one prompt)*:

- `pawpal_system.py` — the core logic module, extended repeatedly over the session: `Scheduler.find_next_available_slot()` for this task, plus input-validation guards (`duration_minutes`, `title`, `Scheduler.available_minutes`) added later during a dedicated edge-case-testing pass.
- `app.py` — the Streamlit UI, built up incrementally: immediate add-time conflict warnings, the "Suggest a time" button and its `on_click` callback, and explicit widget `key`s added afterward so tests could target elements reliably instead of by fragile position.
- `tests/test_pawpal.py` — grew alongside every backend change (recurrence automation, conflict detection, the new slot-finder, then the edge-case validation tests), re-run in full after every edit so nothing already working silently broke.
- `tests/test_app.py` *(new file)* — added once UI behavior needed automated, repeatable verification instead of only manual browser checks.
- `README.md` — kept in sync with the code at each phase: a Features list, a rewritten Demo Walkthrough with freshly captured screenshots, an updated Scheduling/Testing table, and refreshed test-count and sample-output blocks.
- `reflection.md` and `ai_interactions.md` — filled in as each phase/stretch feature landed, documenting design tradeoffs and this agent-workflow log itself.
- `diagrams/` and `screenshots/` — regenerated whenever the underlying UML or UI actually changed, rather than left stale next to newer code.

**What did the agent do?**

- Proposed a design before writing any code: reuse `Scheduler`'s existing `start_time`/`available_minutes` window (the same one `build_schedule()` already uses) instead of inventing a separately hardcoded time range, return a plain `"HH:MM"` string consistent with `preferred_time` elsewhere, and return `None` on no fit — mirroring how `mark_task_complete()` and the documented single-day scope of `detect_conflicts()` already behave.
- Implemented `Scheduler.find_next_available_slot(duration_minutes, tasks)` in `pawpal_system.py` — walks the sorted busy intervals from timed tasks and returns the earliest gap that fits.
- Added 6 pytest cases for the method alone (no tasks, a mid-day gap, a too-small gap, flexible tasks correctly ignored, a fully-booked day, the exact-fit boundary) and ran the full suite plus `main.py` after every change.
- Wired a "Suggest a time" button into `app.py`, next to "Add task."
- Drove the actual running Streamlit app with a headless browser (Playwright) to verify the button visually, rather than trusting the code alone — and caught a real design flaw doing it: the first version searched from midnight and suggested an impractical `00:00` slot, so the window was corrected to start from the scheduler's normal `08:00`.
- Hit a real runtime bug live: `StreamlitAPIException: st.session_state.preferred_time_input cannot be modified after the widget ... is instantiated`, from setting a widget's `session_state` after that widget had already rendered in the same script run. Fixed it by moving the logic into a proper `on_click` callback (which Streamlit runs before widgets re-render) and re-verified both the successful-suggestion path and the fully-booked "no slot" path live in the browser.
- Added explicit `key=` parameters to the relevant buttons/inputs and wrote `tests/test_app.py` using Streamlit's own `AppTest` harness to automate both of those same scenarios end-to-end, instead of only testing the backend method in isolation.

**What did you have to verify or fix manually?**

I reviewed and approved each design decision before the agent implemented it — the search-window boundary, the return format, and the None-on-no-fit behavior — rather than letting the agent choose unilaterally. I didn't have to hand-fix any code myself: the agent caught both of its own bugs (the impractical midnight suggestion and the session_state exception) through live browser verification before handing the feature back, so my manual role was directing scope and reviewing behavior rather than patching code.

---

## Advanced Edge-Case Testing

> Document the prompt(s) used to generate edge-case tests and the rationale behind each case.

**Prompt:** "could you help ensure that my code meets the requirements in the screenshot?" (the rubric row: at least three pytest cases targeting complex edge cases such as non-numeric strings, negative numbers, or empty inputs). Rather than writing three arbitrary/contrived tests to satisfy the letter of the rubric, the agent first audited `pawpal_system.py` for fields that genuinely had *no* validation yet, so each test would catch a real gap instead of a made-up one.

**Cases chosen and why:**

- **`duration_minutes` rejects a non-numeric string** (e.g. `"twenty"`) — before this, a bad value from a form or a typo'd test wouldn't fail where it was introduced; it would silently sit in the `Task` and crash later, deep inside a `sort_tasks()`/`build_schedule()` arithmetic comparison, far from the actual mistake.
- **`duration_minutes` rejects negative or zero values** — a negative duration is physically meaningless for a care task and would otherwise silently corrupt scheduling math (e.g. a negative duration "frees up" time in `build_schedule()`'s running total instead of costing any).
- **`title` rejects empty or whitespace-only strings** — an empty title would otherwise silently create an unidentifiable task that shows up blank in every table and generated plan the UI renders, with no way to tell it apart from another blank task.
- **`Scheduler(available_minutes=...)` rejects negative budgets** — a negative time budget is nonsensical and would otherwise silently behave exactly like a zero budget (every task quietly skipped) instead of surfacing that the input itself was bad. Zero was deliberately left valid, since it's already a tested, legitimate "no time today" case (`test_build_schedule_with_zero_minutes_skips_everything`).

All four follow the same shape as the project's existing validation (`priority`, `recurring`, `preferred_time`): fail loudly with `ValueError` at construction time instead of letting a bad value degrade silently into a wrong-but-plausible result somewhere downstream.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
