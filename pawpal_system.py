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
        """Return a fresh Task for this task's next occurrence, due one interval
        past today, or ``None`` if this task doesn't recur.
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
        """Return a new list ordered by each task's preferred time of day ("HH:MM").

        Tasks without a preferred time are flexible and sort after every task
        that has one. Zero-padded "HH:MM" strings compare correctly with plain
        string ordering, so no parsing into minutes is needed.

        Algorithmic feature #2: sorting by time.
        """
        return sorted(
            tasks,
            key=lambda task: (not task.preferred_time, task.preferred_time),
        )

    def filter_tasks(self, tasks, pet_name=None, completion_status=None):
        """Return tasks matching the given pet name and/or completion status.

        Either filter can be left as ``None`` to skip it, so callers can filter
        by just one field or both at once.

        Algorithmic feature #3: filtering.
        """
        filtered = tasks
        if pet_name is not None:
            filtered = [t for t in filtered if t.pet_name == pet_name]
        if completion_status is not None:
            filtered = [t for t in filtered if t.completion_status == completion_status]
        return filtered

    def mark_task_complete(self, owner, task):
        """Mark a task complete and, if it recurs daily/weekly, automatically
        create and attach its next occurrence to the same pet.

        Algorithmic feature #4: recurrence automation via Task.next_occurrence().
        """
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

        Algorithmic feature #5: greedy time-budget filtering — tasks that don't fit
        the remaining time are skipped rather than scheduled.
        Algorithmic feature #6: recurring tasks are favored (via sort_tasks) so daily
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
