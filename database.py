"""Async wrappers around the synchronous Supabase Python SDK."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from locales import DEFAULT_LANG, normalize_lang

# Always load .env from the project directory (not from the process cwd).
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)

logger = logging.getLogger(__name__)

supabase: Client | None = None


def _format_db_error(exc: BaseException) -> str:
    """Build a human-readable description of a Supabase / HTTP error."""
    parts: list[str] = [f"{type(exc).__name__}: {exc}"]

    for attr in ("message", "code", "details", "hint"):
        value = getattr(exc, attr, None)
        if value:
            parts.append(f"{attr}={value!r}")

    text = " | ".join(parts)

    lowered = text.lower()
    if "invalid api key" in lowered or "jwt" in lowered:
        parts.append(
            "HINT: check SUPABASE_KEY in .env "
            "(use the anon or service_role key from Project Settings → API)"
        )
    elif "name or service not known" in lowered or "nodename" in lowered:
        parts.append(
            "HINT: check SUPABASE_URL in .env "
            "(expected https://<project-ref>.supabase.co)"
        )
    elif "language" in lowered and (
        "column" in lowered or "schema cache" in lowered
    ):
        parts.append(
            "HINT: column profiles.language is missing — run in SQL Editor: "
            "alter table public.profiles "
            "add column if not exists language text not null default 'ru';"
        )
    elif "row-level security" in lowered or "42501" in lowered:
        parts.append(
            "HINT: RLS blocked the query — add policies for profiles "
            "or use the service_role key on the server"
        )

    return " | ".join(parts)


def init_supabase() -> Client:
    """Create (or return) the Supabase client from environment variables."""
    global supabase

    # Re-read .env in case the process cwd differed at first import.
    load_dotenv(dotenv_path=_ENV_PATH, override=False)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not url.strip():
        msg = (
            "SUPABASE_URL is empty. "
            f"Set it in {_ENV_PATH} (e.g. https://xxxx.supabase.co)."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    if not key or not key.strip():
        msg = (
            "SUPABASE_KEY is empty. "
            f"Set the anon or service_role key in {_ENV_PATH}."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    url = url.strip()
    key = key.strip()

    if "your-project-id" in url or key.startswith("your_"):
        logger.warning(
            "SUPABASE_URL / SUPABASE_KEY still look like placeholders "
            "from .env.example — replace them with real credentials."
        )

    try:
        client = create_client(url, key)
    except Exception as exc:
        logger.error(
            "Failed to create Supabase client (url=%s): %s",
            url,
            _format_db_error(exc),
        )
        raise RuntimeError(
            f"Supabase client init failed: {_format_db_error(exc)}"
        ) from exc

    supabase = client
    logger.info("Supabase client ready (url=%s)", url)
    return client


def get_client() -> Client:
    """Return the initialized client, creating it on first use."""
    if supabase is None:
        return init_supabase()
    return supabase


# Initialize at import time so misconfiguration is visible on startup.
try:
    init_supabase()
except Exception:
    # Keep importing the module; handlers will surface a clear error later.
    logger.exception(
        "Supabase was not initialized at import time. "
        "Check SUPABASE_URL / SUPABASE_KEY in %s",
        _ENV_PATH,
    )


async def _run_sync(func: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute a blocking Supabase call in a worker thread."""
    return await asyncio.to_thread(func, *args, **kwargs)


def _ensure_language(profile: dict) -> dict:
    """Guarantee the profile dict always exposes a valid ``language`` field."""
    lang = profile.get("language") or DEFAULT_LANG
    profile["language"] = normalize_lang(str(lang))
    return profile


def _fetch_profile(telegram_id: int) -> dict | None:
    response = (
        get_client()
        .table("profiles")
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def _insert_profile(
    telegram_id: int,
    username: str | None,
    language: str,
) -> dict:
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "language": language,
    }
    response = get_client().table("profiles").insert(payload).execute()
    return response.data[0]


def _update_language(user_id: int, lang: str) -> dict:
    response = (
        get_client()
        .table("profiles")
        .update({"language": lang})
        .eq("telegram_id", user_id)
        .execute()
    )
    data = response.data or []
    if not data:
        raise RuntimeError(
            f"No profile row updated for telegram_id={user_id}. "
            "User may be missing in profiles, or UPDATE was blocked by RLS."
        )
    return data[0]


def _insert_project(user_id: int, title: str, description: str) -> dict:
    payload = {
        "user_id": user_id,
        "title": title,
        "description": description,
    }
    response = get_client().table("projects").insert(payload).execute()
    return response.data[0]


def _fetch_user_projects(user_id: int) -> list[dict]:
    response = (
        get_client()
        .table("projects")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _fetch_project_by_id(project_id: str) -> dict | None:
    response = (
        get_client()
        .table("projects")
        .select("*")
        .eq("id", project_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def _delete_project(project_id: str) -> bool:
    response = (
        get_client()
        .table("projects")
        .delete()
        .eq("id", project_id)
        .execute()
    )
    return bool(response.data)


def _insert_task(project_id: str, title: str) -> dict:
    payload = {
        "project_id": project_id,
        "title": title,
        "is_done": False,
    }
    response = get_client().table("tasks").insert(payload).execute()
    return response.data[0]


def _fetch_project_tasks(project_id: str) -> list[dict]:
    response = (
        get_client()
        .table("tasks")
        .select("*")
        .eq("project_id", project_id)
        .order("is_done", desc=False)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _fetch_task_by_id(task_id: str) -> dict | None:
    response = (
        get_client()
        .table("tasks")
        .select("*")
        .eq("id", task_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def _update_task_status(task_id: str, new_status: bool) -> bool:
    response = (
        get_client()
        .table("tasks")
        .update({"is_done": new_status})
        .eq("id", task_id)
        .execute()
    )
    if not response.data:
        raise ValueError(f"Task not found: {task_id}")
    return bool(response.data[0]["is_done"])


async def get_or_create_user(
    telegram_id: int,
    username: str | None,
    language_code: str | None = None,
) -> dict:
    """Return an existing profile or create a new one.

    Always returns a dict that includes the ``language`` field.
    New users get a language derived from Telegram ``language_code``
    (falls back to ``ru``).
    """
    try:
        profile = await _run_sync(_fetch_profile, telegram_id)
        if profile is not None:
            return _ensure_language(profile)

        language = normalize_lang(language_code)
        created = await _run_sync(
            _insert_profile,
            telegram_id,
            username,
            language,
        )
        return _ensure_language(created)
    except Exception as exc:
        logger.error(
            "Failed to get or create user telegram_id=%s | %s",
            telegram_id,
            _format_db_error(exc),
        )
        raise


async def update_user_language(
    user_id: int,
    lang: str,
    username: str | None = None,
) -> None:
    """Persist the user's preferred UI language.

    Ensures the profile row exists before updating ``language``.
    """
    language = normalize_lang(lang)
    try:
        # Make sure the row exists (middleware may have failed earlier).
        await get_or_create_user(user_id, username, language)
        await _run_sync(_update_language, user_id, language)
        logger.info(
            "Updated language for telegram_id=%s -> %s", user_id, language
        )
    except Exception as exc:
        logger.error(
            "Failed to update language for user_id=%s to %s | %s",
            user_id,
            language,
            _format_db_error(exc),
        )
        raise


async def create_project(user_id: int, title: str, description: str) -> dict:
    """Create a new project for the given user."""
    try:
        return await _run_sync(_insert_project, user_id, title, description)
    except Exception as exc:
        logger.error(
            "Failed to create project for user_id=%s | %s",
            user_id,
            _format_db_error(exc),
        )
        raise


async def get_user_projects(user_id: int) -> list[dict]:
    """Return all projects of a user, newest first."""
    try:
        return await _run_sync(_fetch_user_projects, user_id)
    except Exception as exc:
        logger.error(
            "Failed to fetch projects for user_id=%s | %s",
            user_id,
            _format_db_error(exc),
        )
        raise


async def get_project_by_id(project_id: str) -> dict | None:
    """Return project details by UUID, or None if not found."""
    try:
        return await _run_sync(_fetch_project_by_id, project_id)
    except Exception as exc:
        logger.error(
            "Failed to fetch project_id=%s | %s",
            project_id,
            _format_db_error(exc),
        )
        raise


async def delete_project(project_id: str) -> bool:
    """Delete a project by UUID. Related tasks are removed via CASCADE."""
    try:
        deleted = await _run_sync(_delete_project, project_id)
        if not deleted:
            logger.warning("No project deleted for project_id=%s", project_id)
        return deleted
    except Exception as exc:
        logger.error(
            "Failed to delete project_id=%s | %s",
            project_id,
            _format_db_error(exc),
        )
        raise


async def create_task(project_id: str, title: str) -> dict:
    """Add a new task to a project."""
    try:
        return await _run_sync(_insert_task, project_id, title)
    except Exception as exc:
        logger.error(
            "Failed to create task for project_id=%s | %s",
            project_id,
            _format_db_error(exc),
        )
        raise


async def get_project_tasks(project_id: str) -> list[dict]:
    """Return project tasks with incomplete ones listed first."""
    try:
        return await _run_sync(_fetch_project_tasks, project_id)
    except Exception as exc:
        logger.error(
            "Failed to fetch tasks for project_id=%s | %s",
            project_id,
            _format_db_error(exc),
        )
        raise


async def get_task_by_id(task_id: str) -> dict | None:
    """Return a single task by UUID, or None if not found."""
    try:
        return await _run_sync(_fetch_task_by_id, task_id)
    except Exception as exc:
        logger.error(
            "Failed to fetch task_id=%s | %s",
            task_id,
            _format_db_error(exc),
        )
        raise


async def toggle_task_status(task_id: str, current_status: bool) -> bool:
    """Flip task completion status and return the new value."""
    try:
        new_status = not current_status
        return await _run_sync(_update_task_status, task_id, new_status)
    except Exception as exc:
        logger.error(
            "Failed to toggle task_id=%s | %s",
            task_id,
            _format_db_error(exc),
        )
        raise
