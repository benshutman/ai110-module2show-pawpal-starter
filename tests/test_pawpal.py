"""Quick tests for the PawPal+ logic layer."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def make_task(title="Morning walk", duration=20, priority="high", recurring="none", preferred_time=""):
    """Build a Task with sensible defaults so each test only sets what it cares about."""
    return Task(
        title=title,
        description="test task",
        duration_minutes=duration,
        priority=priority,
        due_date="2026-07-05",
        recurring=recurring,
        preferred_time=preferred_time,
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


def test_detect_conflicts_flags_tasks_at_the_same_preferred_time():
    """Conflict Detection: two tasks at the exact same preferred time are flagged."""
    scheduler = Scheduler(available_minutes=60)
    walk = make_task(title="Morning walk", preferred_time="07:30")
    vet_call = make_task(title="Vet call", preferred_time="07:30")
    grooming = make_task(title="Grooming", preferred_time="14:00")

    conflicts = scheduler.detect_conflicts([walk, vet_call, grooming])

    assert conflicts == [(walk, vet_call)]


def test_detect_conflicts_ignores_flexible_tasks():
    """Conflict Detection: tasks with no preferred time never conflict."""
    scheduler = Scheduler(available_minutes=60)
    flexible_one = make_task(title="Playtime")
    flexible_two = make_task(title="Brushing")

    conflicts = scheduler.detect_conflicts([flexible_one, flexible_two])

    assert conflicts == []


def test_sort_by_time_orders_tasks_chronologically():
    """Sorting: sort_by_time() orders tasks by preferred_time; flexible tasks sort last."""
    scheduler = Scheduler(available_minutes=60)
    afternoon = make_task(title="Grooming", preferred_time="14:00")
    morning = make_task(title="Morning walk", preferred_time="07:30")
    flexible = make_task(title="Playtime")

    ordered = scheduler.sort_by_time([afternoon, flexible, morning])

    assert [t.title for t in ordered] == ["Morning walk", "Grooming", "Playtime"]


def test_filter_tasks_filters_by_pet_and_status():
    """Filtering: filter_tasks() narrows a pooled task list by pet name and by status."""
    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)
    walk = make_task(title="Morning walk")
    feeding = make_task(title="Feeding")
    feeding.mark_complete()
    mochi.add_task(walk)
    whiskers.add_task(feeding)
    owner = Owner(name="Jordan", pets=[mochi, whiskers])
    scheduler = Scheduler(available_minutes=60)
    all_tasks = owner.get_all_tasks()

    by_pet = scheduler.filter_tasks(all_tasks, pet_name="Whiskers")
    by_status = scheduler.filter_tasks(all_tasks, completion_status=True)

    assert [t.title for t in by_pet] == ["Feeding"]
    assert [t.title for t in by_status] == ["Feeding"]
