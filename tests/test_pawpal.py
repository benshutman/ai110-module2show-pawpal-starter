"""Quick tests for the PawPal+ logic layer."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def make_task(title="Morning walk", duration=20, priority="high", recurring="none"):
    """Build a Task with sensible defaults so each test only sets what it cares about."""
    return Task(
        title=title,
        description="test task",
        duration_minutes=duration,
        priority=priority,
        due_date="2026-07-05",
        recurring=recurring,
    )


def test_mark_complete_changes_status():
    """Task Completion: calling mark_complete() flips completion_status to True."""
    task = make_task()
    assert task.completion_status is False

    task.mark_complete()

    assert task.completion_status is True


def test_adding_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet increases that pet's task count."""
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task())
    assert len(pet.get_tasks()) == 1

    pet.add_task(make_task(title="Feeding"))
    assert len(pet.get_tasks()) == 2


def test_marking_daily_task_complete_creates_next_occurrence():
    """Recurring Automation: completing a daily task schedules its next occurrence
    one day past today on the same pet."""
    pet = Pet(name="Mochi", species="dog", age=3)
    task = make_task(recurring="daily")
    pet.add_task(task)
    scheduler = Scheduler(available_minutes=60)
    owner = Owner(name="Jordan", pets=[pet])

    next_task = scheduler.mark_task_complete(owner, task)

    assert task.completion_status is True
    assert len(pet.get_tasks()) == 2
    assert next_task.completion_status is False
    assert next_task.due_date == (date.today() + timedelta(days=1)).isoformat()
    assert next_task.pet_name == "Mochi"


def test_marking_non_recurring_task_complete_does_not_create_next_occurrence():
    """Recurring Automation: completing a one-off task does not schedule anything new."""
    pet = Pet(name="Mochi", species="dog", age=3)
    task = make_task(recurring="none")
    pet.add_task(task)
    scheduler = Scheduler(available_minutes=60)

    next_task = scheduler.mark_task_complete(Owner(name="Jordan", pets=[pet]), task)

    assert next_task is None
    assert len(pet.get_tasks()) == 1
