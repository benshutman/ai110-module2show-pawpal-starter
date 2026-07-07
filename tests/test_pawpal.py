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


def test_marking_weekly_task_complete_creates_next_occurrence_in_a_week():
    """Recurring Automation: completing a weekly task schedules its next occurrence
    seven days past today on the same pet."""
    pet = Pet(name="Whiskers", species="cat", age=5)
    task = make_task(recurring="weekly")
    pet.add_task(task)
    scheduler = Scheduler(available_minutes=60)
    owner = Owner(name="Jordan", pets=[pet])

    next_task = scheduler.mark_task_complete(owner, task)

    assert next_task.recurring == "weekly"
    assert next_task.due_date == (date.today() + timedelta(weeks=1)).isoformat()


def test_marking_already_complete_task_complete_again_does_not_duplicate_next_occurrence():
    """Recurring Automation (edge case): completing an already-completed daily task
    a second time does not schedule a second next occurrence."""
    pet = Pet(name="Mochi", species="dog", age=3)
    task = make_task(recurring="daily")
    pet.add_task(task)
    scheduler = Scheduler(available_minutes=60)
    owner = Owner(name="Jordan", pets=[pet])

    scheduler.mark_task_complete(owner, task)
    second_result = scheduler.mark_task_complete(owner, task)

    assert second_result is None
    assert len(pet.get_tasks()) == 2  # the original (now done) plus exactly one next occurrence


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


def test_detect_conflicts_flags_every_pair_when_three_tasks_share_a_time():
    """Conflict Detection (edge case): three tasks at the same time produce all
    three pairwise conflicts, not just one."""
    scheduler = Scheduler(available_minutes=60)
    walk = make_task(title="Walk", preferred_time="07:30")
    vet_call = make_task(title="Vet call", preferred_time="07:30")
    grooming = make_task(title="Grooming", preferred_time="07:30")

    conflicts = scheduler.detect_conflicts([walk, vet_call, grooming])

    assert conflicts == [(walk, vet_call), (walk, grooming), (vet_call, grooming)]


def test_detect_conflicts_returns_empty_list_for_no_tasks():
    """Conflict Detection (edge case): an empty task list has no conflicts."""
    scheduler = Scheduler(available_minutes=60)

    assert scheduler.detect_conflicts([]) == []


def test_sort_by_time_orders_tasks_chronologically():
    """Sorting: sort_by_time() orders tasks by preferred_time; flexible tasks sort last."""
    scheduler = Scheduler(available_minutes=60)
    afternoon = make_task(title="Grooming", preferred_time="14:00")
    morning = make_task(title="Morning walk", preferred_time="07:30")
    flexible = make_task(title="Playtime")

    ordered = scheduler.sort_by_time([afternoon, flexible, morning])

    assert [t.title for t in ordered] == ["Morning walk", "Grooming", "Playtime"]


def test_sort_by_time_returns_empty_list_for_no_tasks():
    """Sorting (edge case): sort_by_time() on an empty list returns an empty list."""
    scheduler = Scheduler(available_minutes=60)

    assert scheduler.sort_by_time([]) == []


def test_sort_by_time_preserves_original_order_for_ties():
    """Sorting (edge case): tasks with the same preferred_time (or all flexible)
    keep their original relative order, since sort_by_time is a stable sort."""
    scheduler = Scheduler(available_minutes=60)
    tied_first = make_task(title="Feeding", preferred_time="08:00")
    tied_second = make_task(title="Meds", preferred_time="08:00")
    flexible_first = make_task(title="Playtime")
    flexible_second = make_task(title="Brushing")

    ordered = scheduler.sort_by_time([tied_first, tied_second, flexible_first, flexible_second])

    assert [t.title for t in ordered] == ["Feeding", "Meds", "Playtime", "Brushing"]


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


def test_filter_tasks_with_both_filters_keeps_only_tasks_matching_both():
    """Filtering (edge case): combining pet_name and completion_status only keeps
    tasks that satisfy both conditions at once, not either one alone."""
    mochi = Pet(name="Mochi", species="dog", age=3)
    walk = make_task(title="Morning walk")  # Mochi, not done
    grooming = make_task(title="Grooming")
    grooming.mark_complete()  # Mochi, done
    mochi.add_task(walk)
    mochi.add_task(grooming)
    scheduler = Scheduler(available_minutes=60)

    done_mochi_tasks = scheduler.filter_tasks(mochi.get_tasks(), pet_name="Mochi", completion_status=True)
    pending_mochi_tasks = scheduler.filter_tasks(mochi.get_tasks(), pet_name="Mochi", completion_status=False)

    assert [t.title for t in done_mochi_tasks] == ["Grooming"]
    assert [t.title for t in pending_mochi_tasks] == ["Morning walk"]


def test_filter_tasks_with_unknown_pet_name_returns_empty_list():
    """Filtering (edge case): a pet name that matches no task returns an empty list."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(make_task())
    scheduler = Scheduler(available_minutes=60)

    assert scheduler.filter_tasks(pet.get_tasks(), pet_name="Whiskers") == []


def test_filter_tasks_with_no_tasks_returns_empty_list():
    """Filtering (edge case): filtering an empty task list returns an empty list,
    even with filters set."""
    scheduler = Scheduler(available_minutes=60)

    assert scheduler.filter_tasks([], pet_name="Mochi", completion_status=True) == []


def test_build_schedule_schedules_tasks_that_fit_and_skips_the_rest():
    """Greedy Scheduling: build_schedule() schedules tasks that fit the time budget,
    in sequential start-time order, and skips whatever doesn't fit."""
    scheduler = Scheduler(available_minutes=30, start_time="08:00")
    walk = make_task(title="Morning walk", duration=20, priority="high")
    grooming = make_task(title="Grooming", duration=45, priority="low")

    plan = scheduler.build_schedule([walk, grooming])

    assert [entry["task"].title for entry in plan["scheduled"]] == ["Morning walk"]
    assert plan["scheduled"][0]["time"] == "08:00"
    assert [t.title for t in plan["skipped"]] == ["Grooming"]
    assert plan["minutes_used"] == 20
    assert plan["minutes_available"] == 30


def test_build_schedule_with_zero_minutes_skips_everything():
    """Greedy Scheduling (edge case): available_minutes=0 means nothing gets scheduled."""
    scheduler = Scheduler(available_minutes=0, start_time="08:00")
    task = make_task(duration=5)

    plan = scheduler.build_schedule([task])

    assert plan["scheduled"] == []
    assert plan["skipped"] == [task]
    assert plan["minutes_used"] == 0


def test_build_schedule_schedules_task_that_exactly_fills_the_budget():
    """Greedy Scheduling (edge case): a task whose duration exactly equals the
    remaining budget is still scheduled — the fit check is inclusive (<=)."""
    scheduler = Scheduler(available_minutes=20, start_time="08:00")
    task = make_task(duration=20)

    plan = scheduler.build_schedule([task])

    assert plan["scheduled"] == [{"time": "08:00", "task": task}]
    assert plan["minutes_used"] == 20


def test_build_schedule_wraps_start_time_past_midnight():
    """Greedy Scheduling (edge case): a plan starting late in the day wraps its
    clock past midnight instead of overflowing into a 25th hour."""
    scheduler = Scheduler(available_minutes=60, start_time="23:50")
    first = make_task(title="Late walk", duration=20, priority="high")
    second = make_task(title="Late feeding", duration=20, priority="high")

    plan = scheduler.build_schedule([first, second])

    assert [entry["time"] for entry in plan["scheduled"]] == ["23:50", "00:10"]


def test_build_schedule_with_no_tasks_returns_empty_plan():
    """Greedy Scheduling (edge case): build_schedule() on an empty task list
    returns an empty plan without error."""
    scheduler = Scheduler(available_minutes=60)

    plan = scheduler.build_schedule([])

    assert plan == {
        "scheduled": [],
        "skipped": [],
        "minutes_used": 0,
        "minutes_available": 60,
    }
