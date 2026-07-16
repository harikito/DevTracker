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
