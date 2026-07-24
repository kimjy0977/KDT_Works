-- ORIGIN v2 — 스키마 + 보안(RLS)
-- Supabase SQL Editor에 그대로 붙여 실행. (v1보다 확장됨: EN 컬럼·profiles·essays)

-- ── 사조 ────────────────────────────────────────────────
create table if not exists movements (
  id         serial primary key,
  slug       text unique not null,
  name_ko    text not null,
  name_en    text not null,
  era_start  int  not null,
  era_end    int  not null,
  blurb      text not null,       -- 한국어
  blurb_en   text not null default '',
  sort       int  not null default 0
);

-- ── 원류 작품 ────────────────────────────────────────────
create table if not exists works (
  id             serial primary key,
  movement_id    int  not null references movements(id) on delete cascade,
  title          text not null,
  title_en       text not null default '',
  creator        text not null,
  year           text not null,
  image_url      text not null,
  source_url     text not null,
  description    text not null,   -- 한국어
  description_en text not null default '',
  lineage_note   text not null,   -- 한국어
  lineage_en     text not null default ''
);

-- ── 유저 프로필 (온보딩 맞춤) ────────────────────────────
create table if not exists profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  interests    text[] not null default '{}',   -- 관심 사조 slug 배열
  role         text,                            -- 직군
  onboarded_at timestamptz
);

-- ── 칼럼(에세이) ─────────────────────────────────────────
create table if not exists essays (
  id           serial primary key,
  slug         text unique not null,
  title_ko     text not null,
  title_en     text not null,
  dek_ko       text not null,     -- 한 줄 소개
  dek_en       text not null,
  body_ko      text not null,     -- 본문 (문단 \n\n 구분, [[work:ID]] 토큰 임베드)
  body_en      text not null,
  hero_url     text not null,
  movement_slug text,             -- 관련 사조
  featured     boolean not null default false,
  sort         int not null default 0
);

-- ── 무드보드(유저별 컬렉션) ──────────────────────────────
create table if not exists board_items (
  id         serial primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  work_id    int  not null references works(id) on delete cascade,
  note       text,
  is_public  boolean not null default false,
  created_at timestamptz not null default now(),
  unique (user_id, work_id)
);

-- ── 행 수준 보안 (RLS) ───────────────────────────────────
alter table movements   enable row level security;
alter table works       enable row level security;
alter table essays      enable row level security;
alter table profiles    enable row level security;
alter table board_items enable row level security;

-- 콘텐츠(사조·작품·칼럼)는 누구나 읽기만
drop policy if exists "movements read" on movements;
create policy "movements read" on movements for select using (true);
drop policy if exists "works read" on works;
create policy "works read" on works for select using (true);
drop policy if exists "essays read" on essays;
create policy "essays read" on essays for select using (true);

-- 프로필: 본인 것만
drop policy if exists "profile select own" on profiles;
create policy "profile select own" on profiles for select using (auth.uid() = id);
drop policy if exists "profile upsert own" on profiles;
create policy "profile upsert own" on profiles for insert with check (auth.uid() = id);
drop policy if exists "profile update own" on profiles;
create policy "profile update own" on profiles for update using (auth.uid() = id) with check (auth.uid() = id);

-- 무드보드: 본인 것 전체 접근 + 공개(is_public) 항목은 누구나 읽기
drop policy if exists "board select own" on board_items;
create policy "board select own" on board_items
  for select using (auth.uid() = user_id or is_public = true);
drop policy if exists "board insert own" on board_items;
create policy "board insert own" on board_items
  for insert with check (auth.uid() = user_id);
drop policy if exists "board update own" on board_items;
create policy "board update own" on board_items
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists "board delete own" on board_items;
create policy "board delete own" on board_items
  for delete using (auth.uid() = user_id);
