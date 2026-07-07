from dataclasses import dataclass, field
from datetime import date, timedelta


# Maps human-readable priority labels to a sortable numeric weight.
PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}

# Maps a recurrence frequency to how far past today its next occurrence falls.
RECURRENCE_INTERVALS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def _add_minutes(time_str, minutes):
    """Add ``minutes`` to an ``"HH:MM"`` clock string and return the new ``"HH:MM"``."""
    hours, mins = (int(part) for part in time_str.split(":"))
    total = hours * 60 + mins + minutes
    total %= 24 * 60  # wrap around midnight so the clock stays valid
    return f"{total // 60:02d}:{total % 60:02d}"


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

    def get_priority_value(self):
        """Return a sortable weight for this task's priority (higher = more urgent)."""
        return PRIORITY_VALUES.get(self.priority.lower(), 0)

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
        """Create a scheduler with a daily time budget and a plan start time."""
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
        """Find tasks scheduled at the exact same time of day.

        Args:
            tasks (list[Task]): Tasks to check; not mutated.

        Returns:
            list[tuple[Task, Task]]: Every pair of tasks that share a non-empty
                ``preferred_time``. Tasks without a preferred time are flexible
                and never conflict. This only catches exact "HH:MM" matches —
                see reflection.md section 2b for the tradeoff against true
                overlapping-duration detection.

        Algorithmic feature #4: basic conflict detection.
        """
        by_time = {}
        for task in tasks:
            if task.preferred_time:
                by_time.setdefault(task.preferred_time, []).append(task)

        conflicts = []
        for tasks_at_time in by_time.values():
            for i in range(len(tasks_at_time)):
                for j in range(i + 1, len(tasks_at_time)):
                    conflicts.append((tasks_at_time[i], tasks_at_time[j]))
        return conflicts

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
