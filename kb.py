"""Inline and reply keyboards for DevTracker (builder pattern)."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_kb(i18n: dict[str, str]) -> InlineKeyboardMarkup:
    """Root navigation: projects, creation, and language switch."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n["main_menu_btn"],
            callback_data="proj_list",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n["create_project_btn"],
            callback_data="proj_create",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n["change_lang_btn"],
            callback_data="change_lang",
        )
    )
    return builder.as_markup()


def projects_list_kb(
    projects: list[dict],
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """Dynamic list of user projects with a back button."""
    builder = InlineKeyboardBuilder()
    untitled = i18n.get("untitled", "—")
    for project in projects:
        title = project.get("title") or untitled
        project_id = project["id"]
        builder.row(
            InlineKeyboardButton(
                text=f"📁 {title}",
                callback_data=f"proj_view:{project_id}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=i18n["back"],
            callback_data="menu_main",
        )
    )
    return builder.as_markup()


def project_detail_kb(
    project_id: str,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """Actions available on a single project screen."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n["view_tasks"],
            callback_data=f"task_list:{project_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n["add_task"],
            callback_data=f"task_add:{project_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n["back"],
            callback_data="proj_list",
        )
    )
    return builder.as_markup()


def tasks_list_kb(
    tasks: list[dict],
    project_id: str,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """Task list with toggle buttons and navigation."""
    builder = InlineKeyboardBuilder()
    untitled = i18n.get("untitled", "—")
    for task in tasks:
        title = task.get("title") or untitled
        is_done = bool(task.get("is_done"))
        prefix = "✅" if is_done else "❌"
        task_id = task["id"]
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix} {title}",
                callback_data=f"task_toggle:{task_id}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=i18n["add_task"],
            callback_data=f"task_add:{project_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n["back"],
            callback_data=f"proj_view:{project_id}",
        )
    )
    return builder.as_markup()


def language_selection_kb() -> InlineKeyboardMarkup:
    """Inline buttons for choosing the UI language."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🇷🇺 Русский",
            callback_data="set_lang:ru",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🇺🇸 English",
            callback_data="set_lang:en",
        )
    )
    return builder.as_markup()


def cancel_kb(i18n: dict[str, str]) -> ReplyKeyboardMarkup:
    """Reply keyboard to abort an active FSM dialog."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=i18n["cancel"]))
    return builder.as_markup(resize_keyboard=True)
