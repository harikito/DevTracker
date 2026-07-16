# DevTracker — Multilingual Pet-Project Tracker Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blueviolet?logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

> 🇬🇧 **English** · 🇷🇺 [Русская версия](#-devtracker--multilingual-pet-project-tracker-bot-russian)

---

# 🇬🇧 DevTracker — Multilingual Pet-Project Tracker Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blueviolet?logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)

An **asynchronous Telegram bot** that helps developers track their **pet projects** and related **tasks**.

DevTracker stores data in **Supabase (PostgreSQL)** and ships with built-in **multilingual UI support (RU / EN)**.

---

## 🛠 Tech Stack

| Technology | Role |
|---|---|
| **Python 3.10+** | Core language |
| **Aiogram 3** | Async Telegram Bot framework |
| **Supabase / PostgreSQL** | Cloud database & API |
| **python-dotenv** | Environment variable loading |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/DevTracker.git
cd DevTracker
```

### 2. Install dependencies

On macOS, use `pip3`:

```bash
pip3 install -r requirements.txt
```

Optional — create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

### 3. Configure `.env`

```bash
cp .env.example .env
```

Fill in your values:

```env
BOT_TOKEN=your_telegram_bot_token_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_public_key_here
```

| Variable | Where to get it |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `SUPABASE_URL` | Supabase → **Project Settings → API → Project URL** |
| `SUPABASE_KEY` | Supabase → **Project Settings → API → `anon` / `service_role` key** |

> For a server-side bot, prefer the **`service_role`** key. Never expose it in client apps.

### 4. Run the bot

```bash
python3 main.py
```

Then open Telegram and send `/start` to your bot.

---

## 🗄 Supabase Database Setup

1. Open your project in [Supabase](https://supabase.com/).
2. Go to **SQL Editor → New query**.
3. Paste the SQL below (from `schema.sql`) and click **Run**.

```sql
-- DevTracker schema for Supabase (PostgreSQL)
-- Run this in the Supabase SQL Editor before starting the bot.

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    telegram_id bigint primary key,
    username text,
    language text not null default 'ru',
    created_at timestamptz not null default now(),
    constraint profiles_language_check check (language in ('ru', 'en'))
);

-- Existing deployments: add the column if the table already exists.
alter table public.profiles
    add column if not exists language text not null default 'ru';

create table if not exists public.projects (
    id uuid primary key default gen_random_uuid(),
    user_id bigint not null references public.profiles (telegram_id) on delete cascade,
    title text not null,
    description text not null default '',
    created_at timestamptz not null default now()
);

create index if not exists projects_user_id_created_at_idx
    on public.projects (user_id, created_at desc);

create table if not exists public.tasks (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects (id) on delete cascade,
    title text not null,
    is_done boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists tasks_project_id_status_idx
    on public.tasks (project_id, is_done, created_at desc);

-- For a private bot with the service/anon key on the server,
-- permissive policies are acceptable. Tighten for public clients.
alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.tasks enable row level security;

create policy "profiles_all" on public.profiles
    for all using (true) with check (true);

create policy "projects_all" on public.projects
    for all using (true) with check (true);

create policy "tasks_all" on public.tasks
    for all using (true) with check (true);
```

### Tables overview

| Table | Purpose |
|---|---|
| `profiles` | Telegram users (`telegram_id`, `username`, `language`) |
| `projects` | Pet projects (`user_id` → `profiles.telegram_id`) |
| `tasks` | Project tasks (`is_done`, linked via `project_id`) |

---

<p align="center">
  <a href="#-devtracker--multilingual-pet-project-tracker-bot-russian">⬇️ Switch to Russian</a>
</p>

---
---

# 🇷🇺 DevTracker — Multilingual Pet-Project Tracker Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blueviolet?logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)

> 🇷🇺 **Русский** · 🇬🇧 [English version](#-devtracker--multilingual-pet-project-tracker-bot)

**Асинхронный Telegram-бот** для разработчиков, который помогает трекать **пет-проекты** и связанные с ними **задачи**.

DevTracker хранит данные в **Supabase (PostgreSQL)** и поддерживает **мультиязычный интерфейс (RU / EN)**.

---

## 🛠 Стек технологий

| Технология | Назначение |
|---|---|
| **Python 3.10+** | Основной язык |
| **Aiogram 3** | Асинхронный фреймворк для Telegram Bot API |
| **Supabase / PostgreSQL** | Облачная база данных и API |
| **python-dotenv** | Загрузка переменных окружения из `.env` |

---

## 🚀 Быстрый запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/<your-username>/DevTracker.git
cd DevTracker
```

### 2. Установите зависимости

На macOS используйте `pip3`:

```bash
pip3 install -r requirements.txt
```

Опционально — виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

### 3. Настройте `.env`

```bash
cp .env.example .env
```

Заполните значения:

```env
BOT_TOKEN=your_telegram_bot_token_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_public_key_here
```

| Переменная | Где взять |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `SUPABASE_URL` | Supabase → **Project Settings → API → Project URL** |
| `SUPABASE_KEY` | Supabase → **Project Settings → API → ключ `anon` / `service_role`** |

> Для серверного бота лучше использовать ключ **`service_role`**. Не публикуйте его в клиентских приложениях.

### 4. Запустите бота

```bash
python3 main.py
```

После запуска откройте Telegram и отправьте боту команду `/start`.

---

## 🗄 Настройка базы данных в Supabase

1. Откройте проект в [Supabase](https://supabase.com/).
2. Перейдите в **SQL Editor → New query**.
3. Вставьте SQL ниже (из `schema.sql`) и нажмите **Run**.

```sql
-- DevTracker schema for Supabase (PostgreSQL)
-- Run this in the Supabase SQL Editor before starting the bot.

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    telegram_id bigint primary key,
    username text,
    language text not null default 'ru',
    created_at timestamptz not null default now(),
    constraint profiles_language_check check (language in ('ru', 'en'))
);

-- Existing deployments: add the column if the table already exists.
alter table public.profiles
    add column if not exists language text not null default 'ru';

create table if not exists public.projects (
    id uuid primary key default gen_random_uuid(),
    user_id bigint not null references public.profiles (telegram_id) on delete cascade,
    title text not null,
    description text not null default '',
    created_at timestamptz not null default now()
);

create index if not exists projects_user_id_created_at_idx
    on public.projects (user_id, created_at desc);

create table if not exists public.tasks (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects (id) on delete cascade,
    title text not null,
    is_done boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists tasks_project_id_status_idx
    on public.tasks (project_id, is_done, created_at desc);

-- For a private bot with the service/anon key on the server,
-- permissive policies are acceptable. Tighten for public clients.
alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.tasks enable row level security;

create policy "profiles_all" on public.profiles
    for all using (true) with check (true);

create policy "projects_all" on public.projects
    for all using (true) with check (true);

create policy "tasks_all" on public.tasks
    for all using (true) with check (true);
```

### Обзор таблиц

| Таблица | Назначение |
|---|---|
| `profiles` | Пользователи Telegram (`telegram_id`, `username`, `language`) |
| `projects` | Пет-проекты (`user_id` → `profiles.telegram_id`) |
| `tasks` | Задачи проекта (`is_done`, связь через `project_id`) |

---

<p align="center">
  Made for developers who ship side projects 🚀
</p>
