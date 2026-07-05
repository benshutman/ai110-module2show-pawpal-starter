from dataclasses import dataclass, field


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
        pass

    def describe(self):
        pass

    def mark_complete(self):
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list = field(default_factory=list)

    def add_task(self, task):
        pass

    def get_tasks(self):
        pass


@dataclass
class Owner:
    name: str
    preferences: list = field(default_factory=list)
    pets: list = field(default_factory=list)

    def add_pet(self, pet):
        pass

    def get_pets(self):
        pass


class Scheduler:
    def __init__(self, available_minutes: int):
        self.available_minutes = available_minutes

    def sort_tasks(self, tasks):
        pass

    def build_schedule(self, tasks):
        pass

    def explain_plan(self, plan):
        pass
