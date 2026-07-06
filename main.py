"""PawPal+ demo script.

A small "testing ground" that exercises the logic layer in pawpal_system.py end to end:
it builds an owner with a couple of pets, gives them care tasks, then asks the Scheduler
to build and print a readable daily plan across all the pets.

Run it with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_todays_schedule(owner, plan):
    """Print a nicely formatted 'Today's Schedule' for the terminal."""
    width = 52
    print("=" * width)
    print(f"🐾 PawPal+ — Today's Schedule for {owner.name}".center(width))
    print("=" * width)

    pet_summary = ", ".join(
        f"{pet.name} ({pet.species})" for pet in owner.get_pets()
    )
    print(f"Pets: {pet_summary}")
    print("-" * width)

    if plan["scheduled"]:
        for entry in plan["scheduled"]:
            task = entry["task"]
            flags = []
            if task.recurring != "none":
                flags.append(task.recurring)
            if task.completion_status:
                flags.append("done")
            flag_str = f"  ({', '.join(flags)})" if flags else ""
            print(
                f"  {entry['time']}  {task.title:<16} "
                f"{task.duration_minutes:>3} min  [{task.priority}]{flag_str}"
            )
    else:
        print("  (nothing fit in the available time)")

    if plan["skipped"]:
        print("-" * width)
        print("Skipped (not enough time today):")
        for task in plan["skipped"]:
            print(
                f"  • {task.title:<16} {task.duration_minutes:>3} min  [{task.priority}]"
            )

    print("-" * width)
    print(
        f"Summary: {len(plan['scheduled'])} task(s) scheduled, "
        f"{plan['minutes_used']}/{plan['minutes_available']} minutes used."
    )
    print("=" * width)


def print_sorted_by_time(tasks):
    """Print tasks ordered by their preferred time of day."""
    print("-" * 52)
    print("All tasks sorted by preferred time:")
    for task in tasks:
        time_label = task.preferred_time or "flexible"
        print(f"  {time_label:<8} {task.title:<16} [{task.pet_name}]")


def print_filtered_tasks(label, tasks):
    """Print a filtered subset of tasks under a descriptive label."""
    print("-" * 52)
    print(f"Filtered — {label}:")
    if tasks:
        for task in tasks:
            status = "done" if task.completion_status else "not done"
            print(f"  {task.title:<16} [{task.pet_name}] ({status})")
    else:
        print("  (no matching tasks)")


def main():
    # 1. Create an owner and at least two pets.
    owner = Owner(name="Jordan", preferences=["mornings", "short sessions"])

    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # 2. Add several tasks (with different durations/priorities/preferred times)
    #    to those pets. They're added out of chronological order on purpose, so
    #    sort_by_time() below has to do real work rather than just echoing
    #    insertion order.
    grooming = Task("Grooming", "Brush coat", 45, "low", "2026-07-05", "none", preferred_time="14:00")
    playtime = Task("Playtime", "Feather toy session", 15, "medium", "2026-07-05", "none", preferred_time="17:30")
    morning_walk = Task("Morning walk", "Walk around the block", 30, "high", "2026-07-05", "daily", preferred_time="07:30")
    litter_box = Task("Litter box", "Scoop litter", 5, "medium", "2026-07-05", "daily", preferred_time="08:15")
    feeding = Task("Feeding", "Wet food", 10, "high", "2026-07-05", "daily", preferred_time="08:00")

    # A couple of tasks are already done today, so filtering by status has
    # something to show.
    feeding.mark_complete()
    litter_box.mark_complete()

    mochi.add_task(grooming)
    mochi.add_task(morning_walk)
    whiskers.add_task(playtime)
    whiskers.add_task(litter_box)
    whiskers.add_task(feeding)

    # 3. Pool every pet's tasks, then exercise the new sorting/filtering
    #    algorithms on the pooled list before building the day's plan.
    scheduler = Scheduler(available_minutes=60, start_time="08:00")
    all_tasks = owner.get_all_tasks()

    print_sorted_by_time(scheduler.sort_by_time(all_tasks))
    print_filtered_tasks("Whiskers' tasks", scheduler.filter_tasks(all_tasks, pet_name="Whiskers"))
    print_filtered_tasks("completed tasks", scheduler.filter_tasks(all_tasks, completion_status=True))

    # 4. Build the day's plan (60 minutes available) and print it.
    plan = scheduler.build_schedule(all_tasks)
    print_todays_schedule(owner, plan)

    # 5. Demonstrate recurrence automation: completing a daily task automatically
    #    schedules its next occurrence on the same pet.
    print("-" * 52)
    print("Recurrence automation:")
    before_count = len(mochi.get_tasks())
    next_walk = scheduler.mark_task_complete(owner, morning_walk)
    after_count = len(mochi.get_tasks())
    print(f"  Completed '{morning_walk.title}' — Mochi now has {after_count} task(s) (was {before_count}).")
    if next_walk:
        print(f"  Next occurrence scheduled: '{next_walk.title}' due {next_walk.due_date}.")


if __name__ == "__main__":
    main()
