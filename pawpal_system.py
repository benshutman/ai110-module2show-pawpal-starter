from dataclasses import dataclass, field
from datetime import date, timedelta


# Maps human-readable priority labels to a sortable numeric weight.
PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}

# Maps a recurrence frequency to how far past today its next occurrence falls.
RECURRENCE_INTERVALS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}

VALID_RECURRENCE_VALUES = {"none", *RECURRENCE_INTERVALS}


def _add_minutes(time_str, minutes):
    """Add ``minutes`` to an ``"HH:MM"`` clock string and return the new ``"HH:MM"``."""
    hours, mins = (int(part) for part in time_str.split(":"))
    total = hours * 60 + mins + minutes
    total %= 24 * 60  # wrap around midnight so the clock stays valid
    return f"{total // 60:02d}:{total % 60:02d}"


def _time_to_minutes(time_str):
    """Convert an ``"HH:MM"`` clock string to minutes since midnight."""
    hours, mins = (int(part) for part in time_str.split(":"))
    return hours * 60 + mins


def _normalize_time(time_str):
    """Validate a clock string and zero-pad it to a canonical ``"HH:MM"``.

    Accepts any ``"H:MM"``/``"HH:MM"`` 24-hour string (e.g. ``"7:30"``) so a
    user typing without a leading zero still sorts and compares correctly
    downstream, where ``"HH:MM"`` strings are compared as plain text.

    Raises:
        ValueError: If ``time_str`` isn't a valid 24-hour clock string.
    """
    try:
        hours_str, minutes_str = time_str.split(":")
        hours, minutes = int(hours_str), int(minutes_str)
    except (ValueError, AttributeError):
        raise ValueError(f'preferred_time must be an "HH:MM" string, got {time_str!r}')

    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f'preferred_time must be a valid 24-hour time, got {time_str!r}')

    return f"{hours:02d}:{minutes:02d}"


def _normalize_choice(value, valid_values, field_name):
    """Validate ``value`` case-insensitively against ``valid_values``.

    A typo here (e.g. "Daily" or "hgih") would otherwise degrade silently —
    ``dict.get(..., default)`` lookups elsewhere just fall back to a default
    weight/behavior instead of surfacing the mistake.

    Raises:
        ValueError: If ``value`` (lowercased) isn't one of ``valid_values``.
    """
    normalized = value.lower() if isinstance(value, str) else value
    if normalized not in valid_values:
        raise ValueError(f"{field_name} must be one of {sorted(valid_values)}, got {value!r}")
    return normalized


@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    priority: str
    due_date: str
    recurring: str = "none"  # "none", "daily", or "weekly"
    completion_status: bool = False
    preferred_time: str = ""
    pet_name: str = ""

    def __post_init__(self):
        """Validate/normalize fields so a typo fails loudly instead of degrading
        silently into a wrong-but-plausible weight or behavior."""
        if not isinstance(self.duration_minutes, int) or isinstance(self.duration_minutes, bool):
            raise ValueError(f"duration_minutes must be an int, got {self.duration_minutes!r}")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes!r}")
        if not self.title or not self.title.strip():
            raise ValueError("title must not be empty")
        self.priority = _normalize_choice(self.priority, PRIORITY_VALUES, "priority")
        self.recurring = _normalize_choice(self.recurring, VALID_RECURRENCE_VALUES, "recurring")
        if self.preferred_time:
            self.preferred_time = _normalize_time(self.preferred_time)

    def get_priority_value(self):
        """Return a sortable weight for this task's priority (higher = more urgent)."""
        return PRIORITY_VALUES[self.priority]

    def describe(self):
        """Return a human-readable one-line summary of the task."""
        summary = f"{self.title} ({self.duration_minutes} min) [priority: {self.priority}]"
        if self.recurring != "none":
            summary += f" (recurring {self.recurring})"
        if self.completion_status:
            summary += " ✓"
        return summary

    def mark_complete(self):
        """Mark the task as done. State is changed through this method, not directly."""
        self.completion_status = True

    def next_occurrence(self):
        """Build the next scheduled instance of a recurring task.

        Returns:
            Task: A new, incomplete Task with the same title/description/duration/
                priority/preferred_time, due one interval (1 day for "daily", 7
                days for "weekly") past today.
            None: If ``self.recurring`` is "none" (or any value not in
                RECURRENCE_INTERVALS).
        """
        interval = RECURRENCE_INTERVALS.get(self.recurring)
        if interval is None:
            return None

        next_due = date.today() + interval
        return Task(
            title=self.title,
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            due_date=next_due.isoformat(),
            recurring=self.recurring,
            preferred_time=self.preferred_time,
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list = field(default_factory=list)

    def add_task(self, task):
        """Attach a care task to this pet, stamping it with this pet's name so
        pooled tasks (e.g. from Owner.get_all_tasks()) stay traceable to their pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self):
        """Return this pet's list of tasks."""
        return self.tasks


@dataclass
class Owner:
    name: str
    preferences: list = field(default_factory=list)
    pets: list = field(default_factory=list)

    def add_pet(self, pet):
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_pets(self):
        """Return this owner's list of pets."""
        return self.pets

    def get_all_tasks(self):
        """Pool and return a flat list of tasks across all of this owner's pets.

        This is how the Scheduler retrieves work across multiple pets rather than
        being limited to a single pet.
        """
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


class Scheduler:
    def __init__(self, available_minutes: int, start_time: str = "08:00"):
        """Create a scheduler with a daily time budget and a plan start time.

        Raises:
            ValueError: If available_minutes is negative or not an int. Zero is
                allowed (a legitimately empty day, see build_schedule() tests) —
                only a nonsensical negative budget is rejected.
        """
        if not isinstance(available_minutes, int) or isinstance(available_minutes, bool):
            raise ValueError(f"available_minutes must be an int, got {available_minutes!r}")
        if available_minutes < 0:
            raise ValueError(f"available_minutes must not be negative, got {available_minutes!r}")
        self.available_minutes = available_minutes
        self.start_time = start_time

    def sort_tasks(self, tasks):
        """Return a new list ordered by priority (high first), then recurring tasks,
        then shorter duration as a tie-break so more tasks fit the day.

        Algorithmic feature #1: sorting.
        """
        return sorted(
            tasks,
            key=lambda task: (
                -task.get_priority_value(),
                task.recurring == "none",
                task.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks):
        """Order tasks by their preferred time of day.

        Args:
            tasks (list[Task]): Tasks to sort; not mutated.

        Returns:
            list[Task]: A new list ordered by ``preferred_time`` ("HH:MM").
                Tasks without a preferred time are flexible and sort after every
                task that has one. Zero-padded "HH:MM" strings compare correctly
                with plain string ordering, so no parsing into minutes is needed.

        Algorithmic feature #2: sorting by time.
        """
        return sorted(
            tasks,
            key=lambda task: (not task.preferred_time, task.preferred_time),
        )

    def filter_tasks(self, tasks, pet_name=None, completion_status=None):
        """Filter tasks by pet name and/or completion status.

        Args:
            tasks (list[Task]): Tasks to filter; not mutated.
            pet_name (str, optional): Keep only tasks whose ``pet_name`` matches.
                Skipped when ``None``.
            completion_status (bool, optional): Keep only tasks whose
                ``completion_status`` matches. Skipped when ``None``.

        Returns:
            list[Task]: Tasks matching every filter that was given. Applied as
                two sequential passes (rather than one combined-condition
                comprehension) because that reads as plainly as the feature
                works: filter by pet, then by status — the task lists here are
                small enough that the extra pass costs nothing.

        Algorithmic feature #3: filtering.
        """
        filtered = tasks
        if pet_name is not None:
            filtered = [t for t in filtered if t.pet_name == pet_name]
        if completion_status is not None:
            filtered = [t for t in filtered if t.completion_status == completion_status]
        return filtered

    def detect_conflicts(self, tasks):
        """Find tasks whose [preferred_time, preferred_time + duration) ranges overlap.

        Args:
            tasks (list[Task]): Tasks to check; not mutated.

        Returns:
            list[tuple[Task, Task]]: Every pair of tasks with a non-empty
                ``preferred_time`` whose scheduled ranges overlap — including
                tasks that start at different times but still collide (e.g. a
                20-minute task at "07:30" overlaps one starting at "07:45").
                Tasks without a preferred time are flexible and never conflict.
                Ranges are compared within a single day; a task whose range
                would run past midnight is not checked against next-day tasks
                (see reflection.md section 2b).

        Algorithmic feature #4: overlap-aware conflict detection.
        """
        timed_tasks = [t for t in tasks if t.preferred_time]

        conflicts = []
        for i in range(len(timed_tasks)):
            start_a = _time_to_minutes(timed_tasks[i].preferred_time)
            end_a = start_a + timed_tasks[i].duration_minutes
            for j in range(i + 1, len(timed_tasks)):
                start_b = _time_to_minutes(timed_tasks[j].preferred_time)
                end_b = start_b + timed_tasks[j].duration_minutes
                if start_a < end_b and start_b < end_a:
                    conflicts.append((timed_tasks[i], timed_tasks[j]))
        return conflicts

    def find_next_available_slot(self, duration_minutes, tasks):
        """Find the earliest "HH:MM" start time, within ``[start_time, start_time +
        available_minutes)``, where a task of ``duration_minutes`` wouldn't overlap
        any existing timed task.

        Args:
            duration_minutes (int): Length of the slot to fit.
            tasks (list[Task]): Existing tasks to avoid colliding with; not mutated.
                Tasks without a ``preferred_time`` are flexible and never block a slot.

        Returns:
            str: ``"HH:MM"`` of the earliest open slot.
            None: If no slot of that length fits before the day's time budget runs out.

        Algorithmic feature #8: earliest-fit gap search across the day's busy intervals,
        scoped to the same ``start_time``/``available_minutes`` window ``build_schedule()``
        uses, rather than a separately hardcoded day boundary.
        """
        window_start = _time_to_minutes(self.start_time)
        window_end = window_start + self.available_minutes

        busy = sorted(
            (_time_to_minutes(t.preferred_time), _time_to_minutes(t.preferred_time) + t.duration_minutes)
            for t in tasks
            if t.preferred_time
        )

        candidate = window_start
        for busy_start, busy_end in busy:
            if busy_start >= candidate + duration_minutes:
                break
            candidate = max(candidate, busy_end)

        if candidate + duration_minutes <= window_end:
            return f"{candidate // 60:02d}:{candidate % 60:02d}"
        return None

    def mark_task_complete(self, owner, task):
        """Complete a task and auto-schedule its next occurrence if it recurs.

        Args:
            owner (Owner): Owner whose pets are searched (by ``task.pet_name``)
                for where to attach the next occurrence.
            task (Task): The task to mark complete.

        Returns:
            Task: The newly scheduled next occurrence, if ``task`` recurs
                daily/weekly and its pet was found.
            None: If the task doesn't recur, or was already complete (so
                completing it twice can't schedule two next occurrences).

        Algorithmic feature #5: recurrence automation via Task.next_occurrence().
        """
        if task.completion_status:
            return None

        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            for pet in owner.get_pets():
                if pet.name == task.pet_name:
                    pet.add_task(next_task)
                    break
        return next_task

    def build_schedule(self, tasks):
        """Build a time-stamped daily plan that fits within ``available_minutes``.

        Algorithmic feature #6: greedy time-budget filtering — tasks that don't fit
        the remaining time are skipped rather than scheduled.
        Algorithmic feature #7: recurring tasks are favored (via sort_tasks) so daily
        essentials aren't dropped ahead of one-off tasks of equal priority.
        """
        ordered = self.sort_tasks(tasks)
        scheduled = []
        skipped = []
        minutes_used = 0
        current_time = self.start_time

        for task in ordered:
            if minutes_used + task.duration_minutes <= self.available_minutes:
                scheduled.append({"time": current_time, "task": task})
                current_time = _add_minutes(current_time, task.duration_minutes)
                minutes_used += task.duration_minutes
            else:
                skipped.append(task)

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "minutes_used": minutes_used,
            "minutes_available": self.available_minutes,
        }

    def explain_plan(self, plan):
        """Render a plan (from build_schedule) as a human-readable, explained string."""
        lines = [
            f"Daily plan ({plan['minutes_used']}/{plan['minutes_available']} min used):"
        ]

        if plan["scheduled"]:
            for entry in plan["scheduled"]:
                lines.append(f"  {entry['time']} — {entry['task'].describe()}")
        else:
            lines.append("  (nothing fit in the available time)")

        if plan["skipped"]:
            lines.append("Skipped (not enough time):")
            for task in plan["skipped"]:
                lines.append(f"  {task.describe()}")

        lines.append(
            "Reasoning: tasks ordered by priority (high first), recurring essentials "
            "favored, then shorter tasks; scheduled greedily until time ran out."
        )
        return "\n".join(lines)
