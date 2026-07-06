import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# Streamlit reruns this whole script on every interaction, so a plain `Owner(...)`
# would be recreated (and wiped) every time. Store it in session_state — the session
# "vault" — and only create it once, on the first run. Later runs reuse the same object.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)
else:
    # Keep the persisted Owner's name in sync with the input box.
    st.session_state.owner.name = owner_name

owner = st.session_state.owner

st.divider()

# --- Pets: "Add a Pet" wired to Owner.add_pet() ---
st.subheader("Pets")
pcol1, pcol2, pcol3 = st.columns(3)
with pcol1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with pcol3:
    pet_age = st.number_input("Age", min_value=0, max_value=40, value=3)

if st.button("Add pet"):
    owner.add_pet(Pet(name=pet_name, species=species, age=int(pet_age)))
    st.success(f"Added {pet_name} the {species}.")

pets = owner.get_pets()
if pets:
    st.write("Current pets:")
    st.table(
        [
            {"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.get_tasks())}
            for p in pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks: "Add a Task" wired to Pet.add_task() ---
st.subheader("Tasks")
if not pets:
    st.info("Add a pet first — tasks are attached to a pet.")
else:
    target_index = st.selectbox(
        "Attach task to pet",
        range(len(pets)),
        format_func=lambda i: f"{pets[i].name} ({pets[i].species})",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        due_date = st.date_input("Due date")
    with col5:
        recurring = st.checkbox("Recurring (daily essential)", value=False)

    task_description = st.text_input("Description (optional)", value="")

    if st.button("Add task"):
        pet = pets[target_index]
        pet.add_task(
            Task(
                title=task_title,
                description=task_description,
                duration_minutes=int(duration),
                priority=priority,
                due_date=str(due_date),
                recurring=recurring,
            )
        )
        st.success(f"Added '{task_title}' to {pet.name}.")

    # Show each pet's tasks so the change is visible immediately after adding.
    any_tasks = False
    for pet in pets:
        pet_tasks = pet.get_tasks()
        if pet_tasks:
            any_tasks = True
            st.write(f"**{pet.name}**'s tasks:")
            st.table(
                [
                    {
                        "title": t.title,
                        "duration_minutes": t.duration_minutes,
                        "priority": t.priority,
                        "recurring": t.recurring,
                        "done": t.completion_status,
                    }
                    for t in pet_tasks
                ]
            )
    if not any_tasks:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Build Schedule: wired to the Scheduler across all of the owner's pets ---
st.subheader("Build Schedule")
available_minutes = st.number_input(
    "Minutes available today", min_value=1, max_value=1440, value=60
)

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.info("No tasks to schedule yet. Add some above.")
    else:
        scheduler = Scheduler(available_minutes=int(available_minutes))
        plan = scheduler.build_schedule(all_tasks)
        st.text(scheduler.explain_plan(plan))
