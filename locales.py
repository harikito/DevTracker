"""Localization dictionaries for DevTracker (ru / en)."""

from __future__ import annotations

LOCALES: dict[str, dict[str, str]] = {
    "ru": {
        "welcome": (
            "👋 <b>Привет, {name}!</b>\n\n"
            "Добро пожаловать в <b>DevTracker</b> — твой личный ассистент "
            "для контроля пет-проектов и задач.\n\n"
            "Выбери действие ниже:"
        ),
        "main_menu_btn": "📁 Мои проекты",
        "create_project_btn": "➕ Создать проект",
        "change_lang_btn": "🌐 Сменить язык / Change Language",
        "no_projects": "У тебя пока нет созданных проектов.",
        "project_title_prompt": (
            "Введите название нового проекта:\n"
            "(или нажмите /cancel для отмены)"
        ),
        "project_desc_prompt": (
            "Введите описание проекта:\n"
            "(или нажмите /cancel)"
        ),
        "project_created": "✅ Проект <b>{title}</b> успешно создан!",
        "cancel": "❌ Отмена",
        "canceled": "Действие отменено.",
        "back": "⬅️ Назад",
        "add_task": "➕ Добавить задачу",
        "task_title_prompt": (
            "Введите текст задачи:\n"
            "(или нажмите /cancel)"
        ),
        "task_created": "✅ Задача создана!",
        "projects_header": "📁 <b>Твои проекты:</b>",
        "tasks_header": "📋 <b>Задачи по проекту {title}:</b>\n\n{description}",
        "select_lang": "Выберите язык / Select your language:",
        "lang_changed": "✅ Язык успешно изменен!",
        # Operational strings (errors / edge cases)
        "view_tasks": "📋 Список задач",
        "untitled": "Без названия",
        "no_description": "Описание не указано.",
        "project_not_found": "Проект не найден. Возможно, он был удалён.",
        "task_not_found": "Задача не найдена.",
        "task_done": "Задача выполнена.",
        "task_undone": "Задача снова активна.",
        "no_tasks": "В этом проекте пока нет задач.",
        "no_active_action": "Сейчас нет активного действия.",
        "empty_title": "Название не может быть пустым. Попробуйте снова:",
        "title_too_long": (
            "Название слишком длинное (макс. {max} символов). "
            "Введите более короткое:"
        ),
        "desc_too_long": (
            "Описание слишком длинное (макс. {max} символов). "
            "Сократите текст и отправьте снова:"
        ),
        "error_db": (
            "Не удалось подключиться к базе данных. "
            "Попробуйте позже."
        ),
        "error_load_projects": "Не удалось загрузить проекты. Попробуйте позже.",
        "error_load_project": "Не удалось открыть проект. Попробуйте позже.",
        "error_load_tasks": "Не удалось загрузить задачи. Попробуйте позже.",
        "error_toggle": "Не удалось обновить статус задачи.",
        "error_create_project": "Не удалось создать проект. Попробуйте позже.",
        "error_create_task": "Не удалось создать задачу. Попробуйте позже.",
        "context_lost": (
            "Контекст проекта потерян. "
            "Вернитесь в меню и попробуйте снова."
        ),
        "fallback_fsm": (
            "Ожидаю текстовый ответ по текущему шагу.\n"
            "Или нажмите «❌ Отмена» / отправьте /cancel."
        ),
        "fallback_menu": "Используйте меню ниже или команду /start.",
    },
    "en": {
        "welcome": (
            "👋 <b>Hello, {name}!</b>\n\n"
            "Welcome to <b>DevTracker</b> — your personal assistant "
            "for tracking pet projects and tasks.\n\n"
            "Choose an action below:"
        ),
        "main_menu_btn": "📁 My Projects",
        "create_project_btn": "➕ Create Project",
        "change_lang_btn": "🌐 Change Language / Сменить язык",
        "no_projects": "You don't have any projects yet.",
        "project_title_prompt": (
            "Enter new project title:\n"
            "(or type /cancel to abort)"
        ),
        "project_desc_prompt": (
            "Enter project description:\n"
            "(or type /cancel)"
        ),
        "project_created": "✅ Project <b>{title}</b> created successfully!",
        "cancel": "❌ Cancel",
        "canceled": "Action canceled.",
        "back": "⬅️ Back",
        "add_task": "➕ Add Task",
        "task_title_prompt": (
            "Enter task title:\n"
            "(or type /cancel)"
        ),
        "task_created": "✅ Task created!",
        "projects_header": "📁 <b>Your Projects:</b>",
        "tasks_header": "📋 <b>Tasks for {title}:</b>\n\n{description}",
        "select_lang": "Select your language / Выберите язык:",
        "lang_changed": "✅ Language updated successfully!",
        # Operational strings (errors / edge cases)
        "view_tasks": "📋 Task list",
        "untitled": "Untitled",
        "no_description": "No description provided.",
        "project_not_found": "Project not found. It may have been deleted.",
        "task_not_found": "Task not found.",
        "task_done": "Task marked as done.",
        "task_undone": "Task marked as active.",
        "no_tasks": "This project has no tasks yet.",
        "no_active_action": "There is no active action right now.",
        "empty_title": "Title cannot be empty. Please try again:",
        "title_too_long": (
            "Title is too long (max {max} characters). "
            "Please enter a shorter one:"
        ),
        "desc_too_long": (
            "Description is too long (max {max} characters). "
            "Please shorten it and try again:"
        ),
        "error_db": (
            "Could not connect to the database. "
            "Please try again later."
        ),
        "error_load_projects": "Could not load projects. Please try again later.",
        "error_load_project": "Could not open the project. Please try again later.",
        "error_load_tasks": "Could not load tasks. Please try again later.",
        "error_toggle": "Could not update task status.",
        "error_create_project": "Could not create the project. Please try again later.",
        "error_create_task": "Could not create the task. Please try again later.",
        "context_lost": (
            "Project context was lost. "
            "Return to the menu and try again."
        ),
        "fallback_fsm": (
            "Waiting for a text reply for the current step.\n"
            "Or press «❌ Cancel» / send /cancel."
        ),
        "fallback_menu": "Use the menu below or the /start command.",
    },
}

SUPPORTED_LANGS = frozenset(LOCALES.keys())
DEFAULT_LANG = "ru"


def normalize_lang(language_code: str | None) -> str:
    """Map a Telegram language_code to a supported locale key."""
    if not language_code:
        return DEFAULT_LANG
    code = language_code.lower().replace("_", "-")
    short = code.split("-", maxsplit=1)[0]
    if short in SUPPORTED_LANGS:
        return short
    if code.startswith("en"):
        return "en"
    return DEFAULT_LANG


def get_i18n(lang: str | None) -> dict[str, str]:
    """Return localization dict for the given language code."""
    if lang in LOCALES:
        return LOCALES[lang]
    return LOCALES[DEFAULT_LANG]
