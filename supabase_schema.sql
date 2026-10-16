-- Desafio MQS: execute este script uma única vez no SQL Editor do Supabase.
create table if not exists public.mqs_settings (
  id integer primary key check (id = 1),
  title text not null default 'DESAFIO MQS',
  campaign_open boolean not null default false,
  start_date date,
  end_date date,
  questions_per_game integer not null default 10 check (questions_per_game between 1 and 100)
);

create table if not exists public.mqs_questions (
  id text primary key,
  category text not null default 'Geral',
  prompt text not null,
  question_type text not null default 'MCQ',
  a text not null default '',
  b text not null default '',
  c text not null default '',
  d text not null default '',
  correct text not null default '',
  explanation text not null default '',
  active boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.mqs_attempts (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  name text not null,
  sector text not null,
  participant_key text not null unique,
  score integer not null default 0,
  correct integer not null default 0,
  total integer not null default 0,
  percent numeric(5,1) not null default 0,
  answers jsonb not null default '[]'::jsonb
);

-- A aplicação usa a chave de servidor apenas no backend Python (Streamlit Secrets).
-- Não exponha SUPABASE_SERVICE_ROLE_KEY no navegador nem em repositório público.
alter table public.mqs_settings enable row level security;
alter table public.mqs_questions enable row level security;
alter table public.mqs_attempts enable row level security;

insert into public.mqs_settings (id, title, campaign_open, questions_per_game)
values (1, 'DESAFIO MQS', false, 10)
on conflict (id) do nothing;
