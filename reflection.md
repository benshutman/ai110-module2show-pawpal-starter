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
    - I included four classes: Owner, Pet, Task, and Scheduler. The Owner class is the User, who manages the owner's information and the pets (multiple) that they might own. The Pet class stores each pet's information like name and species and age and the tasks connected to that pet. The Task class represents individual tasks, including duration, priority, and whether the task repeats. The Scheduler class sorts tasks and builds a plan based on the available time.

**b. Design changes**

- Did your design change during implementation?
    -My design was constantly changing during implementation. I kept interrogating the AI to help me design a better overall flow for the program logic. The base 4 classes are pretty "simple" but the process of designing a UML and asking for potential logical bottlenecks revealed some things. 
- If yes, describe at least one change and why you made it.
    -In my task class I didn't have a method to change the state and mark a task as completed, I was controlling it using a bool class attribute. I didn't have a way for Task to control it's own state. Claude suggested that I use a method to control Task state, which is better OOP design. Yeah, I forget my getters and setters! I happened to take a look at the gradiung rubric, which clearly says that we need a class method to control the state.  
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    - Three constraints drive the schedule: the owner's available time budget (`available_minutes`), each task's `priority` (high/medium/low), and each task's `preferred_time` (used for sorting and conflict detection, not for hard time-slot booking). Recurrence (`daily`/`weekly`) acts as a soft constraint too — `sort_tasks()` favors recurring tasks over one-off tasks of the same priority so a daily essential like feeding isn't crowded out by a one-time task of equal priority.
- How did you decide which constraints mattered most?
    - Priority mattered most, because a busy pet owner cares more about "did the urgent things happen today" than about hitting an exact time of day — so `build_schedule()` sorts on priority first, before anything else. Preferred time deliberately doesn't override that: it drives display ordering (`sort_by_time`) and conflict detection (`detect_conflicts`), but a low-priority task's preferred time never bumps a high-priority task out of the schedule.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    - The one tradeoff that's still real and accepted: this only compares ranges *within a single day*. A task whose range would run past midnight (e.g., "23:50" for 30 minutes) is not checked against the next day's early tasks. I decided that's acceptable because a daily pet-care task realistically scheduled to span midnight is vanishingly rare, and handling it would mean splitting ranges across day boundaries for a case I couldn't actually construct a realistic scenario for.
- Why is that tradeoff reasonable for this scenario?
    - I decided that's acceptable because a daily pet-care task realistically scheduled to span midnight is vanishingly rare, and handling it would mean splitting ranges across day boundaries for a case I couldn't actually construct a realistic scenario for.

**c. Presenting conflicts in the UI**

- If your Scheduler flags a task conflict, how should that warning be presented in the Streamlit UI to be most helpful to a pet owner?
    - I made the decision to present the warning to the user so they can modify the conflict there and then. The conflict warning is pops up and makes the user address it only when the owner later happens to open "Browse Tasks" is too late to be actionable; they've moved on and may never look. So `app.py` now calls `detect_conflicts()` again immediately after `Add task` and shows an `st.warning()` to the user right at the moment of creation, while the form (and the ability to just change the preferred time) is still in front of them. The warning is specific: the warning names both tasks, the pet, and the exact overlapping time, e.g. `⚠ 'Vet checkup' overlaps with 'Morning walk' (Mochi, 07:30). Consider picking a different time.` — everything needed to resolve it is presented to the user without leaving the page. I kept the existing Browse Tasks conflict list too, since it still catches conflicts created indirectly (e.g., a recurring task's auto-scheduled next occurrence landing on an already-taken slot) that an add-time check can't see.
    - I verified this live with a headless-browser screenshot: adding "Morning walk" (07:30) then "Vet checkup" at an overlapping 07:40 shows the yellow `st.warning` immediately below the green `st.success`, distinct enough to notice, with no console errors.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    - I worked through this project step by step with Claude after developing the classes and UML. I shared each phase's checklist (sorting/filtering, recurring tasks, evaluate-and-refine, document-and-merge) and asked it to implement the described logic directly in my existing classes rather than starting over. I also used it to review my own code — asking it to critique one of my methods for readability/performance before I decided whether to actually keep the suggestion.
- What kinds of prompts or questions were most helpful?
    - Narrow, specific, concrete prompts worked much better than vague ones. "Share one of your completed algorithmic methods and ask how it could be simplified" produced a focused before/after comparison on one function, instead of a scattershot list of unrelated suggestions a generic "review my code" would have produced. This time I asked it to test and verify after each step- asking it to actually run `main.py` and `pytest` after every change — instead of just describing what the code should do — also caught things I wouldn't have noticed from reading a diff alone.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - When I asked Claude to simplify `Scheduler.filter_tasks()`, it collapsed two sequential list-comprehension passes into one comprehension with a combined `(x is None or ...) and (y is None or ...)` condition. That version is more "Pythonic" and technically does one less pass over the list, but I decided it was harder to read at a glance than the original step-by-step version. The app only ever filters a handful of tasks at a time, so the performance win wasn't worth the readability cost. I rejected it and kept the original two-pass version.
- How did you evaluate or verify what the AI suggested?
    - I compared both versions side by side. Then I ran the full pytest suite after each change to make sure behavior didn't change. Once I verified that it didn't, same tests passing both times, I re-ran `main.py` to confirm the "Filtered — Whiskers' tasks" / "Filtered — completed tasks" demo output was identical before and after.

**c. AI strategy**

- Which AI coding assistant features were most effective for building your scheduler?
    - I really made use of the "agent" mode. Being able to actually *run* the app in browser, not just read the code, was the biggest win. Claude ran `pytest` after every change to catch regressions immediately, and once the Streamlit UI needed verifying, it drove the real running app with a headless browser to actually check the behavior. The ability to click through "add a pet → add an overlapping task → confirm the conflict warning fires" and captured screenshots — instead of just describing what the UI *should* do significantly changes how I test. The fact that I could check browser behavior caught things a code read alone wouldn't have, like confirming the add-time conflict warning actually renders with the right task names and pet, not just that the underlying function returns the right pairs.
- How did using separate chat sessions for different phases help you stay organized?
    - I separated chat sessions by phases. Working phase by phase (sorting/filtering, then recurring automation, then evaluate-and-refine, then docs/UML/README) kept each session focused on one checklist instead of trying to hold the whole project in view at once. Each new phase also started from an already-tested baseline, so a session only had to reason about the one feature it was adding rather than re-verifying everything that came before. I tested and verified at each step, so it kept everything as clean as possible.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - I believe I was pretty thorough. I tested every algorithmic feature the project is built around, not just the original four: priority sorting (`sort_tasks`), time-based sorting (`sort_by_time`), filtering (`filter_tasks`), overlap-aware conflict detection (`detect_conflicts`), recurrence automation (`Task.next_occurrence`/`mark_task_complete`), greedy time-budget scheduling (`build_schedule`), and the next-available-slot finder (`find_next_available_slot`) added later as a stretch feature. On top of the happy-path behaviors, I added advanced edge-case tests for fields that had no validation at all until I went looking for gaps: non-numeric and negative/zero `duration_minutes`, an empty/whitespace `title`, and a negative `Scheduler.available_minutes`. I also added UI-level tests with Streamlit's `AppTest` harness that drive the actual "Suggest a time" button end to end, instead of only testing `find_next_available_slot()` in isolation.
- Why were these tests important?
    - The algorithmic features are the core behaviors the app is supposed to demonstrate, and they're easy to get subtly wrong. For example, an off-by-one in the `timedelta` math for "next occurrence," or a filter that silently returns everything instead of nothing when a field doesn't match. The demo script (`main.py`) only walks through one hand-built scenario, so it wouldn't catch a bug in a case that scenario doesn't happen to hit the way a dedicated test does. The edge-case tests mattered because they weren't hypothetical — `duration_minutes` and `title` genuinely had zero validation before I wrote them, so a typo'd or blank value would have silently corrupted scheduling math or produced an unidentifiable task. The UI tests mattered because a passing backend test doesn't prove the Streamlit wiring calls it correctly — that's exactly how I caught a real `StreamlitAPIException` while building "Suggest a time" that no backend test could have seen.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - I am confident on the paths I exercised — all 42 pytest tests pass (40 backend/logic tests plus 2 `AppTest`-driven UI tests). I didn't stop at unit tests: I drove the real Streamlit app end-to-end with `AppTest` (and, separately, a headless browser for visual verification) to confirm the UI wiring itself works — not just that the underlying functions return the right values.
- What edge cases would you test next if you had more time?
    - Weekly recurrence crossing a month or year boundary, and conflict detection spanning midnight (the deliberately-accepted limitation from section 2b) — both are real gaps I know about but haven't closed, unlike the ones above that I already went back and fixed.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    - I was really impressed with how the conflict-detection feature was developed. It went from a naive exact-time-match check, to a true overlap-aware range check, to finally surfacing the warning directly to the user the moment a task is added instead of only in a separate browse view. Every step of that evolution is backed by a passing test and, for the UI piece, an actual screenshot of it firing correctly.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - I would really like to add persistence features! That seems like the most reasonable path to improvement. Along the way, I'd extend conflict detection to span midnight (the known gap documented in section 2b), and I'd let a user edit or delete an existing task instead of only adding new ones — right now a typo in a task can only be worked around by adding a corrected duplicate.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    - My role is different than "normal" programming. Being the "lead architect" meant staying responsible for every design decision even when the AI proposed the code — accepting a suggestion because it worked wasn't good enough; I had to be able to explain why it was the right call for *this* app. For example, rejecting the more "Pythonic" one-line `filter_tasks()` because readability mattered more than a marginal performance win on a handful of tasks. The AI was fastest at generating options and verifying behavior; the judgment about which option actually fit the scenario had to stay mine. I liken this to the way humans walk- each step is not deterministic, rather we place our feet in approximately where we want them to go and basically fall forward, then catch our balance. It is like working with the AI- I have to "drive" but I'm really just giving an approximation and catching my balance when things go screwey. 
