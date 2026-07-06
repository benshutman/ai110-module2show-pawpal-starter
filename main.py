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
            if task.recurring:
                flags.append("recurring")
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


def main():
    # 1. Create an owner and at least two pets.
    owner = Owner(name="Jordan", preferences=["mornings", "short sessions"])

    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # 2. Add several tasks (with different durations/priorities) to those pets.
    mochi.add_task(Task("Morning walk", "Walk around the block", 30, "high", "2026-07-05", True))
    mochi.add_task(Task("Grooming", "Brush coat", 45, "low", "2026-07-05", False))
    whiskers.add_task(Task("Feeding", "Wet food", 10, "high", "2026-07-05", True))
    whiskers.add_task(Task("Litter box", "Scoop litter", 5, "medium", "2026-07-05", True))
    whiskers.add_task(Task("Playtime", "Feather toy session", 15, "medium", "2026-07-05", False))

    # 3. Pool every pet's tasks and build the day's plan (60 minutes available).
    scheduler = Scheduler(available_minutes=60, start_time="08:00")
    all_tasks = owner.get_all_tasks()
    plan = scheduler.build_schedule(all_tasks)

    # 4. Print a readable "Today's Schedule".
    print_todays_schedule(owner, plan)


if __name__ == "__main__":
    main()
