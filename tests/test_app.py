"""End-to-end tests for the "Suggest a time" button in app.py, using Streamlit's
own AppTest harness to drive the real script (not just the underlying Scheduler
method in isolation)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def _add_pet(at):
    """Add the default pet (Mochi/dog/3) via the UI."""
    at.button(key="add_pet_button").click().run()


def _add_task(at, title, duration, preferred_time):
    """Fill in and submit the Add Task form via the UI."""
    at.text_input(key="task_title_input").input(title).run()
    at.number_input(key="task_duration_input").set_value(duration).run()
    at.text_input(key="preferred_time_input").input(preferred_time).run()
    at.button(key="add_task_button").click().run()


def test_suggest_a_time_fills_the_earliest_open_slot():
    """Suggest a Time: clicking the button fills preferred_time with the earliest
    gap after an existing task, matching Scheduler.find_next_available_slot()."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    _add_pet(at)
    _add_task(at, title="Morning walk", duration=20, preferred_time="08:00")  # occupies 08:00-08:20

    at.text_input(key="task_title_input").input("Vet checkup").run()
    at.number_input(key="task_duration_input").set_value(15).run()
    at.button(key="suggest_time_button").click().run()

    assert not at.exception
    assert at.text_input(key="preferred_time_input").value == "08:20"
    assert at.session_state["suggestion_message"] is None


def test_suggest_a_time_warns_when_the_day_is_fully_booked():
    """Suggest a Time (edge case): when no gap of the requested length exists
    before the end of the day, the button surfaces a warning instead of a time."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    _add_pet(at)
    # Fill the entire 08:00-24:00 search window with four back-to-back 240-minute
    # blocks (240 is the form's max duration), leaving no gap anywhere.
    for start in ["08:00", "12:00", "16:00", "20:00"]:
        _add_task(at, title=f"Block {start}", duration=240, preferred_time=start)

    at.text_input(key="task_title_input").input("Vet checkup").run()
    at.number_input(key="task_duration_input").set_value(10).run()
    at.button(key="suggest_time_button").click().run()

    assert not at.exception
    assert at.session_state["suggestion_message"] == "No open slot found for that duration today."
    assert any("No open slot found" in w.value for w in at.warning)
