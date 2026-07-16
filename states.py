"""FSM state groups for DevTracker dialogs."""

from aiogram.fsm.state import State, StatesGroup


class ProjectStates(StatesGroup):
    """Multi-step flow for creating a new project."""

    waiting_for_title = State()
    waiting_for_description = State()


# Backward-compatible alias used by older imports.
ProjectCreation = ProjectStates


class TaskCreation(StatesGroup):
    """Flow for adding a task to an existing project.

    Store ``project_id`` in FSM context data while waiting for the title.
    """

    waiting_for_task_title = State()
