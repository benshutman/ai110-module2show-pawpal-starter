# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
##- 3 core actions a user should perform:   
    -Add/change pet/owner info (basic info re:owner and pet)
    -Add tasks (feeding, pet sitting, walks, playtime, grooming, medication)
    -Generate Daily Plan (Organizes tasks by time, priority, conflicts, etc)
- Briefly describe your initial UML design.
    -My UML describes 4 classes: Owner, Pet, Task, and Scheduler. For each class, the UML lists methods and attributes, and shows the relationship between the classes. 
- What classes did you include, and what responsibilities did you assign to each?
    - I included four classes: Owner, Pet, Task, and Scheduler. The Owner class manages the owner's information and the pets (multiple) that they might own. The Pet class stores each pet's information like name and species and age and the tasks connected to that pet. The Task class represents individual tasks, including duration, priority, and whether the task repeats. The Scheduler class sorts tasks and builds a plan based on the available time.

**b. Design changes**

- Did your design change during implementation?
    -My design was constantly changing during implementation. I kept interrogating the AI to help me design a better overall flow for the program logic. The base 4 classes are pretty "simple" but the process of designing a UML and asking for potential logical bottlenecks revealed some things. 
- If yes, describe at least one change and why you made it.
    -In my task class I didn't have a method to change the state and mark a task as completed, I was controlling it using a bool class attribute. I didn't have a way for Task to control it's own state. Claude suggested that I use a method to control Task state, which is better OOP design. Yeah, I forget my getters and setters! I happened to take a look at the gradiung rubric, which clearly says that we need a class method to control the state.  
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    - **Update:** I originally shipped `Scheduler.detect_conflicts()` checking only for *exact-same* `preferred_time` strings, and accepted that as a known limitation (see the original reasoning below). Once I had more time, I went back and closed that gap: `detect_conflicts()` now converts each task's `preferred_time` + `duration_minutes` into a `[start, end)` minute-of-day range and flags any pair whose ranges truly overlap — so a 20-minute walk at "07:30" now correctly conflicts with a task starting at "07:45", not just one also starting at "07:30". Back-to-back tasks that only touch (one ends exactly when the next starts) are correctly treated as non-overlapping. The one tradeoff that's still real: this only compares ranges *within a single day* — a task whose range would run past midnight (e.g., "23:50" for 30 minutes) is not checked against the next day's early tasks. I decided that's acceptable because a daily pet-care task realistically scheduled to span midnight is vanishingly rare, and handling it would mean splitting ranges across day boundaries for a case I couldn't actually construct a realistic scenario for.
    - *(Original reasoning, kept for context on how the decision evolved):* True overlap detection means converting every task's start time and duration into a minute-of-day interval, then comparing every pair of intervals for overlap — more code, more edge cases (midnight wraparound, back-to-back tasks that just touch but don't overlap), for a feature this app only needs a "basic" version of. For a single owner tracking a handful of daily pet-care tasks, exact-time collisions are the common case worth catching, and I'd rather ship a simple, correct check than a more complete one I'm less confident is bug-free.
- Why is that tradeoff reasonable for this scenario?
    - I verified the upgrade didn't regress the original behavior: every existing exact-time-match test still passes (same start time always trivially overlaps), and I added new tests for the cases the old version would have missed — different start times with overlapping durations (now correctly flagged) and back-to-back tasks that only touch (correctly *not* flagged). I also confirmed this live in `main.py`: completing the daily "Morning walk" still auto-schedules its next occurrence at the same 07:30 slot as the just-completed original, and `detect_conflicts()` still catches that pair under the new overlap-based logic.

**c. Presenting conflicts in the UI**

- If your Scheduler flags a task conflict, how should that warning be presented in the Streamlit UI to be most helpful to a pet owner?
    - Two things make a conflict warning actually useful: timing and specificity. Timing — flagging it only when the owner later happens to open "Browse Tasks" is too late to be actionable; they've moved on and may never look. So `app.py` now calls `detect_conflicts()` again immediately after `Add task` and shows an `st.warning()` right at the moment of creation, while the form (and the ability to just change the preferred time) is still in front of them. Specificity — a generic "you have a conflict somewhere" forces the owner to go hunt for it, so the warning names both tasks, the pet, and the exact overlapping time, e.g. `⚠ 'Vet checkup' overlaps with 'Morning walk' (Mochi, 07:30). Consider picking a different time.` — everything needed to resolve it without leaving the page. I kept the existing Browse Tasks conflict list too, since it still catches conflicts created indirectly (e.g., a recurring task's auto-scheduled next occurrence landing on an already-taken slot) that an add-time check can't see.
    - I verified this live with a headless-browser screenshot: adding "Morning walk" (07:30) then "Vet checkup" at an overlapping 07:40 shows the yellow `st.warning` immediately below the green `st.success`, distinct enough to notice, with no console errors.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    - I worked through this project step by step with Claude, sharing each phase's checklist (sorting/filtering, recurring tasks, evaluate-and-refine, document-and-merge) and asking it to implement the described logic directly in my existing classes rather than starting over. I also used it to review my own code — asking it to critique one of my methods for readability/performance before I decided whether to actually keep the suggestion.
- What kinds of prompts or questions were most helpful?
    - Narrow, concrete prompts worked much better than vague ones. "Share one of your completed algorithmic methods and ask how it could be simplified" produced a focused before/after comparison on one function, instead of a scattershot list of unrelated suggestions a generic "review my code" would have produced. Asking it to actually run `main.py` and `pytest` after every change — instead of just describing what the code should do — also caught things I wouldn't have noticed from reading a diff alone.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - When I asked Claude to simplify `Scheduler.filter_tasks()`, it collapsed two sequential list-comprehension passes into one comprehension with a combined `(x is None or ...) and (y is None or ...)` condition. That version is more "Pythonic" and technically does one less pass over the list, but I decided it was harder to read at a glance than the original step-by-step version — especially since the app only ever filters a handful of tasks at a time, so the performance win wasn't worth the readability cost. I rejected it and kept the original two-pass version.
- How did you evaluate or verify what the AI suggested?
    - I compared both versions side by side, ran the full pytest suite after each change to make sure behavior didn't change (it didn't — same tests passing both times), and re-ran `main.py` to confirm the "Filtered — Whiskers' tasks" / "Filtered — completed tasks" demo output was identical before and after.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - I tested the four algorithmic features this project is built around: sorting (`sort_by_time` orders tasks chronologically, with flexible tasks sorted last), filtering (`filter_tasks` narrows a pooled list by pet name and by completion status), recurring automation (completing a `daily`/`weekly` task creates a correctly-dated next occurrence, and a non-recurring task doesn't create anything), and conflict detection (tasks at the exact same preferred time are flagged, flexible tasks never are). I also kept the task-completion and task-addition tests from earlier phases.
- Why were these tests important?
    - These are the core behaviors the whole app is supposed to demonstrate, and they're easy to get subtly wrong — an off-by-one in the `timedelta` math for "next occurrence," or a filter that silently returns everything instead of nothing when a field doesn't match. The demo script (`main.py`) only walks through one hand-built scenario, so it wouldn't catch a bug in a case that scenario doesn't happen to hit the way a dedicated test does.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - Fairly confident on the paths I actually exercised — all 8 pytest tests pass. I didn't stop at unit tests either: I used Streamlit's `AppTest` API to drive the real Streamlit app end-to-end (adding pets/tasks, marking tasks complete, switching between the sort/filter views) to confirm the UI wiring itself works, not just the underlying functions in isolation.
- What edge cases would you test next if you had more time?
    - True overlapping-duration conflict detection instead of exact-time matching (the known tradeoff documented in section 2b), malformed `preferred_time` input (nothing currently validates "07:30" vs. "7:30" vs. plain text), and weekly recurrence crossing a month or year boundary.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
