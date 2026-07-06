from dataclasses import dataclass, field


# Maps human-readable priority labels to a sortable numeric weight.
PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}


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
    recurring: bool
    completion_status: bool = False

    def get_priority_value(self):
        """Return a sortable weight for this task's priority (higher = more urgent)."""
        return PRIORITY_VALUES.get(self.priority.lower(), 0)

    def describe(self):
        """Return a human-readable one-line summary of the task."""
        summary = f"{self.title} ({self.duration_minutes} min) [priority: {self.priority}]"
        if self.recurring:
            summary += " (recurring)"
        if self.completion_status:
            summary += " ✓"
        return summary

    def mark_complete(self):
        """Mark the task as done. State is changed through this method, not directly."""
        self.completion_status = True


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list = field(default_factory=list)

    def add_task(self, task):
        """Attach a care task to this pet."""
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
                not task.recurring,
                task.duration_minutes,
            ),
        )

    def build_schedule(self, tasks):
        """Build a time-stamped daily plan that fits within ``available_minutes``.

        Algorithmic feature #2: greedy time-budget filtering — tasks that don't fit
        the remaining time are skipped rather than scheduled.
        Algorithmic feature #3: recurring tasks are favored (via sort_tasks) so daily
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
