"""Quick tests for the PawPal+ logic layer."""

from pawpal_system import Pet, Task


def make_task(title="Morning walk", duration=20, priority="high"):
    """Build a Task with sensible defaults so each test only sets what it cares about."""
    return Task(
        title=title,
        description="test task",
        duration_minutes=duration,
        priority=priority,
        due_date="2026-07-05",
        recurring=False,
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
