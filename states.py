"""FSM state groups for DevTracker dialogs."""

from aiogram.fsm.state import State, StatesGroup


class ProjectCreation(StatesGroup):
    """Multi-step flow for creating a new project."""

    waiting_for_title = State()
    waiting_for_description = State()


class TaskCreation(StatesGroup):
    """Flow for adding a task to an existing project.

    Store ``project_id`` in FSM context data while waiting for the title.
    """

    waiting_for_task_title = State()
