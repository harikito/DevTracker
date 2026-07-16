"""DevTracker — async Telegram bot for pet-project tracking."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env BEFORE importing database (client reads env on init).
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)

from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, TelegramObject

import database as db
from kb import (
    cancel_kb,
    confirm_delete_kb,
    language_selection_kb,
    main_menu_kb,
    project_detail_kb,
    projects_list_kb,
    tasks_list_kb,
)
from locales import LOCALES, SUPPORTED_LANGS, get_i18n, normalize_lang
from states import ProjectStates, TaskCreation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

router = Router(name="main")

CANCEL_TEXTS = {
    "❌ Отмена",
    "❌ Cancel",
    "Отмена",
    "Cancel",
    "/cancel",
}


class LocalizationMiddleware(BaseMiddleware):
    """Inject per-user ``i18n`` dictionary and ``lang_code`` into handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            data["i18n"] = LOCALES["ru"]
            data["lang_code"] = "ru"
            return await handler(event, data)

        try:
            db_user = await db.get_or_create_user(
                user.id,
                user.username,
                user.language_code,
            )
            user_lang = normalize_lang(db_user.get("language", "ru"))
        except Exception:
            logger.exception(
                "LocalizationMiddleware: failed to resolve user %s",
                getattr(user, "id", None),
            )
            user_lang = normalize_lang(getattr(user, "language_code", None))

        data["i18n"] = get_i18n(user_lang)
        data["lang_code"] = user_lang
        return await handler(event, data)


def _escape_html(text: str) -> str:
    """Escape characters that break Telegram HTML parse mode."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _display_name(user) -> str:
    """Best-effort display name for welcome messages."""
    if user is None:
        return "User"
    if user.full_name:
        return user.full_name
    if user.username:
        return user.username
    return str(user.id)


def _welcome_text(i18n: dict[str, str], user) -> str:
    return i18n["welcome"].format(name=_escape_html(_display_name(user)))


async def _safe_edit_text(
    message: Message,
    text: str,
    reply_markup=None,
) -> None:
    """Edit message text; ignore 'message is not modified' errors."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except Exception as exc:
        if "message is not modified" in str(exc).lower():
            return
        raise


async def _show_main_menu(
    target: Message,
    i18n: dict[str, str],
    user,
) -> None:
    """Render the welcome/main menu screen in place."""
    await _safe_edit_text(
        target,
        _welcome_text(i18n, user),
        reply_markup=main_menu_kb(i18n),
    )


async def _show_projects_list(
    target: Message,
    user_id: int,
    i18n: dict[str, str],
) -> None:
    """Render the user's project list into an existing message."""
    projects = await db.get_user_projects(user_id)
    if not projects:
        text = f"{i18n['projects_header']}\n\n{i18n['no_projects']}"
        await _safe_edit_text(
            target,
            text,
            reply_markup=projects_list_kb([], i18n),
        )
        return

    untitled = i18n.get("untitled", "—")
    lines = [i18n["projects_header"], ""]
    for index, project in enumerate(projects, start=1):
        title = _escape_html(project.get("title") or untitled)
        lines.append(f"{index}. {title}")

    await _safe_edit_text(
        target,
        "\n".join(lines),
        reply_markup=projects_list_kb(projects, i18n),
    )


async def _show_project_detail(
    target: Message,
    project_id: str,
    i18n: dict[str, str],
) -> None:
    """Render project details into an existing message."""
    project = await db.get_project_by_id(project_id)
    if project is None:
        await _safe_edit_text(
            target,
            i18n["project_not_found"],
            reply_markup=projects_list_kb([], i18n),
        )
        return

    untitled = i18n.get("untitled", "—")
    title = _escape_html(project.get("title") or untitled)
    description = _escape_html(
        project.get("description") or i18n.get("no_description", "")
    )
    text = i18n["project_detail"].format(title=title, description=description)
    await _safe_edit_text(
        target,
        text,
        reply_markup=project_detail_kb(project_id, i18n),
    )


async def _show_tasks_list(
    target: Message,
    project_id: str,
    i18n: dict[str, str],
) -> None:
    """Render the task list for a project into an existing message."""
    project = await db.get_project_by_id(project_id)
    if project is None:
        await _safe_edit_text(
            target,
            i18n["project_not_found"],
            reply_markup=main_menu_kb(i18n),
        )
        return

    tasks = await db.get_project_tasks(project_id)
    untitled = i18n.get("untitled", "—")
    title = _escape_html(project.get("title") or untitled)
    description = _escape_html(
        project.get("description") or i18n.get("no_description", "")
    )
    header = i18n["tasks_header"].format(title=title, description=description)

    if not tasks:
        text = f"{header}\n\n{i18n['no_tasks']}"
    else:
        text = header

    await _safe_edit_text(
        target,
        text,
        reply_markup=tasks_list_kb(tasks, project_id, i18n),
    )


async def _cancel_fsm(
    message: Message,
    state: FSMContext,
    i18n: dict[str, str],
) -> None:
    """Clear FSM state and return the user to the main menu."""
    await state.clear()
    await message.answer(
        i18n["canceled"],
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        _welcome_text(i18n, message.from_user),
        reply_markup=main_menu_kb(i18n),
    )


def _is_cancel_text(text: str | None, i18n: dict[str, str]) -> bool:
    if text is None:
        return False
    stripped = text.strip()
    return stripped in CANCEL_TEXTS or stripped == i18n.get("cancel")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Reset FSM and show the localized welcome screen with action buttons."""
    await state.clear()
    user = message.from_user
    if user is None:
        return

    welcome = _welcome_text(i18n, user)
    menu = main_menu_kb(i18n)

    # Inline menu must be passed directly in answer().
    # Do NOT send ReplyKeyboardRemove first and then edit_text with the same
    # body — Telegram often returns "message is not modified" and the buttons
    # never appear.
    await message.answer(welcome, reply_markup=menu)


@router.message(Command("cancel"))
@router.message(F.text.in_(CANCEL_TEXTS))
async def cmd_cancel(
    message: Message,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Abort any active FSM dialog and return to the main menu."""
    current = await state.get_state()
    if current is None:
        await message.answer(
            f"{i18n['no_active_action']}\n\n{_welcome_text(i18n, message.from_user)}",
            reply_markup=main_menu_kb(i18n),
        )
        return
    await _cancel_fsm(message, state, i18n)


# ---------------------------------------------------------------------------
# Language switch
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Show the language selection menu."""
    await state.clear()
    await callback.answer()
    if callback.message is None:
        return
    await _safe_edit_text(
        callback.message,
        i18n["select_lang"],
        reply_markup=language_selection_kb(),
    )


@router.callback_query(F.data.startswith("set_lang:"))
async def cb_set_lang(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Persist language preference and refresh the main menu in place."""
    await state.clear()
    if callback.message is None or callback.data is None or callback.from_user is None:
        await callback.answer()
        return

    lang_code = callback.data.split(":", maxsplit=1)[1]
    if lang_code not in SUPPORTED_LANGS:
        await callback.answer()
        return

    try:
        await db.update_user_language(
            callback.from_user.id,
            lang_code,
            username=callback.from_user.username,
        )
    except Exception as exc:
        logger.error(
            "set_lang failed for user=%s lang=%s | %s",
            callback.from_user.id,
            lang_code,
            exc,
        )
        await callback.answer(i18n.get("error_db", "Error"), show_alert=True)
        return

    new_i18n = get_i18n(lang_code)
    await callback.answer(new_i18n["lang_changed"])
    text = (
        f"{new_i18n['lang_changed']}\n\n"
        f"{_welcome_text(new_i18n, callback.from_user)}"
    )
    await _safe_edit_text(
        callback.message,
        text,
        reply_markup=main_menu_kb(new_i18n),
    )


# ---------------------------------------------------------------------------
# Main menu & navigation callbacks
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "menu_main")
async def cb_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Return to the root menu."""
    await state.clear()
    await callback.answer()
    if callback.message is None:
        return
    await _show_main_menu(callback.message, i18n, callback.from_user)


@router.callback_query(F.data == "proj_list")
async def cb_projects_list(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Show the list of the user's projects."""
    await state.clear()
    await callback.answer()
    if callback.message is None or callback.from_user is None:
        return

    try:
        await _show_projects_list(
            callback.message,
            callback.from_user.id,
            i18n,
        )
    except Exception:
        logger.exception("Failed to show projects list")
        await _safe_edit_text(
            callback.message,
            i18n["error_load_projects"],
            reply_markup=main_menu_kb(i18n),
        )


@router.callback_query(F.data.startswith("proj_view:"))
async def cb_project_view(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Open a project detail screen."""
    await state.clear()
    await callback.answer()
    if callback.message is None or callback.data is None:
        return

    project_id = callback.data.split(":", maxsplit=1)[1]
    try:
        await _show_project_detail(callback.message, project_id, i18n)
    except Exception:
        logger.exception("Failed to open project_id=%s", project_id)
        await _safe_edit_text(
            callback.message,
            i18n["error_load_project"],
            reply_markup=main_menu_kb(i18n),
        )


@router.callback_query(F.data.startswith("proj_delete_yes:"))
async def cb_project_delete_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Delete the project after explicit confirmation."""
    await state.clear()
    if callback.message is None or callback.data is None or callback.from_user is None:
        await callback.answer()
        return

    project_id = callback.data.split(":", maxsplit=1)[1]
    try:
        deleted = await db.delete_project(project_id)
        if not deleted:
            await callback.answer(i18n["project_not_found"], show_alert=True)
            await _show_projects_list(
                callback.message,
                callback.from_user.id,
                i18n,
            )
            return

        await callback.answer(i18n["project_deleted"])
        await _show_projects_list(
            callback.message,
            callback.from_user.id,
            i18n,
        )
    except Exception:
        logger.exception("Failed to delete project_id=%s", project_id)
        await callback.answer(i18n["error_delete_project"], show_alert=True)


@router.callback_query(F.data.startswith("proj_delete_no:"))
async def cb_project_delete_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Cancel deletion and return to the project detail screen."""
    await state.clear()
    await callback.answer()
    if callback.message is None or callback.data is None:
        return

    project_id = callback.data.split(":", maxsplit=1)[1]
    try:
        await _show_project_detail(callback.message, project_id, i18n)
    except Exception:
        logger.exception(
            "Failed to reopen project after delete cancel: %s", project_id
        )
        await _safe_edit_text(
            callback.message,
            i18n["error_load_project"],
            reply_markup=main_menu_kb(i18n),
        )


@router.callback_query(F.data.startswith("proj_delete:"))
async def cb_project_delete_ask(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Ask for delete confirmation before removing a project."""
    await state.clear()
    await callback.answer()
    if callback.message is None or callback.data is None:
        return

    project_id = callback.data.split(":", maxsplit=1)[1]
    try:
        project = await db.get_project_by_id(project_id)
        if project is None:
            await _safe_edit_text(
                callback.message,
                i18n["project_not_found"],
                reply_markup=main_menu_kb(i18n),
            )
            return

        untitled = i18n.get("untitled", "—")
        title = _escape_html(project.get("title") or untitled)
        await _safe_edit_text(
            callback.message,
            i18n["confirm_delete"].format(title=title),
            reply_markup=confirm_delete_kb(project_id, i18n),
        )
    except Exception:
        logger.exception("Failed to open delete confirm for %s", project_id)
        await callback.answer(i18n["error_delete_project"], show_alert=True)


@router.callback_query(F.data.startswith("task_list:"))
async def cb_tasks_list(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Show tasks for the selected project."""
    await state.clear()
    await callback.answer()
    if callback.message is None or callback.data is None:
        return

    project_id = callback.data.split(":", maxsplit=1)[1]
    try:
        await _show_tasks_list(callback.message, project_id, i18n)
    except Exception:
        logger.exception("Failed to load tasks for project_id=%s", project_id)
        await _safe_edit_text(
            callback.message,
            i18n["error_load_tasks"],
            reply_markup=main_menu_kb(i18n),
        )


@router.callback_query(F.data.startswith("task_toggle:"))
async def cb_task_toggle(callback: CallbackQuery, i18n: dict) -> None:
    """Toggle task completion and refresh the task list in place."""
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    task_id = callback.data.split(":", maxsplit=1)[1]

    try:
        task_row = await db.get_task_by_id(task_id)
        if task_row is None:
            await callback.answer(i18n["task_not_found"], show_alert=True)
            return

        current_status = bool(task_row.get("is_done"))
        project_id = str(task_row["project_id"])
        new_status = await db.toggle_task_status(task_id, current_status)

        toast = i18n["task_done"] if new_status else i18n["task_undone"]
        await callback.answer(toast)
        await _show_tasks_list(callback.message, project_id, i18n)
    except Exception:
        logger.exception("task_toggle failed for task_id=%s", task_id)
        await callback.answer(i18n["error_toggle"], show_alert=True)


# ---------------------------------------------------------------------------
# Project creation FSM
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "proj_create")
async def cb_project_create(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Start the project creation dialog."""
    await callback.answer()
    if callback.message is None:
        return

    await state.set_state(ProjectStates.waiting_for_title)
    await callback.message.answer(
        i18n["project_title_prompt"],
        reply_markup=cancel_kb(i18n),
    )


@router.message(ProjectStates.waiting_for_title, F.text)
async def process_project_title(
    message: Message,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Receive project title and ask for description."""
    if message.text is None:
        return
    if _is_cancel_text(message.text, i18n):
        await _cancel_fsm(message, state, i18n)
        return

    title = message.text.strip()
    if not title:
        await message.answer(i18n["empty_title"])
        return
    if len(title) > 120:
        await message.answer(i18n["title_too_long"].format(max=120))
        return

    await state.update_data(title=title)
    await state.set_state(ProjectStates.waiting_for_description)
    await message.answer(i18n["project_desc_prompt"])


@router.message(ProjectStates.waiting_for_description, F.text)
async def process_project_description(
    message: Message,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Receive description, persist the project, and show its detail screen."""
    if message.text is None or message.from_user is None:
        return
    if _is_cancel_text(message.text, i18n):
        await _cancel_fsm(message, state, i18n)
        return

    description = message.text.strip()
    if description in {"—", "-", "нет", "Нет", "no", "No", "none", "None"}:
        description = ""
    if len(description) > 2000:
        await message.answer(i18n["desc_too_long"].format(max=2000))
        return

    data = await state.get_data()
    title = data.get("title") or i18n.get("untitled", "—")
    user_id = message.from_user.id

    try:
        project = await db.create_project(user_id, title, description)
    except Exception:
        logger.exception("Failed to create project for user_id=%s", user_id)
        await state.clear()
        await message.answer(
            i18n["error_create_project"],
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            _welcome_text(i18n, message.from_user),
            reply_markup=main_menu_kb(i18n),
        )
        return

    await state.clear()
    project_id = str(project["id"])
    safe_title = _escape_html(title)

    await message.answer(
        i18n["project_created"].format(title=safe_title),
        reply_markup=ReplyKeyboardRemove(),
    )
    detail_message = await message.answer("…")
    await _show_project_detail(detail_message, project_id, i18n)


# ---------------------------------------------------------------------------
# Task creation FSM
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("task_add:"))
async def cb_task_add(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Start the task creation dialog for a project."""
    await callback.answer()
    if callback.message is None or callback.data is None:
        return

    project_id = callback.data.split(":", maxsplit=1)[1]
    await state.set_state(TaskCreation.waiting_for_task_title)
    await state.update_data(project_id=project_id)

    await callback.message.answer(
        i18n["task_title_prompt"],
        reply_markup=cancel_kb(i18n),
    )


@router.message(TaskCreation.waiting_for_task_title, F.text)
async def process_task_title(
    message: Message,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Persist a new task and return to the project's task list."""
    if message.text is None:
        return
    if _is_cancel_text(message.text, i18n):
        await _cancel_fsm(message, state, i18n)
        return

    title = message.text.strip()
    if not title:
        await message.answer(i18n["empty_title"])
        return
    if len(title) > 200:
        await message.answer(i18n["title_too_long"].format(max=200))
        return

    data = await state.get_data()
    project_id = data.get("project_id")
    if not project_id:
        await state.clear()
        await message.answer(
            i18n["context_lost"],
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            _welcome_text(i18n, message.from_user),
            reply_markup=main_menu_kb(i18n),
        )
        return

    try:
        await db.create_task(str(project_id), title)
    except Exception:
        logger.exception("Failed to create task for project_id=%s", project_id)
        await state.clear()
        await message.answer(
            i18n["error_create_task"],
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            _welcome_text(i18n, message.from_user),
            reply_markup=main_menu_kb(i18n),
        )
        return

    await state.clear()
    await message.answer(
        i18n["task_created"],
        reply_markup=ReplyKeyboardRemove(),
    )
    list_message = await message.answer("…")
    await _show_tasks_list(list_message, str(project_id), i18n)


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


@router.message()
async def fallback_message(
    message: Message,
    state: FSMContext,
    i18n: dict,
) -> None:
    """Guide the user when the message does not match any active flow."""
    current = await state.get_state()
    if current is not None:
        await message.answer(i18n["fallback_fsm"])
        return

    await message.answer(
        i18n["fallback_menu"],
        reply_markup=main_menu_kb(i18n),
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def main() -> None:
    """Initialize bot, dispatcher, middleware, and start long polling."""
    load_dotenv(dotenv_path=_ENV_PATH, override=False)

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error(
            "BOT_TOKEN is not set. Create %s from .env.example.",
            _ENV_PATH,
        )
        sys.exit(1)

    try:
        db.init_supabase()
    except Exception as exc:
        logger.error("Cannot start without Supabase: %s", exc)
        sys.exit(1)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.middleware(LocalizationMiddleware())
    dp.include_router(router)

    logger.info("DevTracker bot is starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
