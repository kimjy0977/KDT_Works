-- ⚠️ 2026-07-24: 이 테이블들은 이후 접두사로 개명됨(a_mq_origin_* / c_lab_todo_* / d_hw_atlas_*).
-- 아래는 초기 세팅 SQL(옛 이름 기록). 현재 스키마 정본 = 라이브 DB(kdt_works). 재실행 시 개명 반영 필요.

-- ============================================================
-- 세계 국가 도감 v2 · 백엔드 설정 (댓글 · 가봤어요/가고싶어요 · 즐겨찾기)
-- 사용자 구분 = Supabase 익명 로그인(anonymous). 본인 것만 수정 가능(RLS).
-- Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 Run
-- ============================================================

-- ① 반응: 나라별 '가봤어요/가고싶어요' (사용자별 1개씩 토글)
create table if not exists public.country_marks (
  user_id    uuid not null references auth.users(id) on delete cascade,
  code       text not null,
  kind       text not null check (kind in ('visited','wish')),
  created_at timestamptz default now(),
  primary key (user_id, code, kind)
);
alter table public.country_marks enable row level security;
drop policy if exists "marks read all"  on public.country_marks;
drop policy if exists "marks insert own" on public.country_marks;
drop policy if exists "marks delete own" on public.country_marks;
create policy "marks read all"   on public.country_marks for select using (true);
create policy "marks insert own"  on public.country_marks for insert with check (auth.uid() = user_id);
create policy "marks delete own"  on public.country_marks for delete using (auth.uid() = user_id);

-- ② 즐겨찾기: 사용자별 (본인만 읽고 쓰기)
create table if not exists public.favorites (
  user_id    uuid not null references auth.users(id) on delete cascade,
  code       text not null,
  created_at timestamptz default now(),
  primary key (user_id, code)
);
alter table public.favorites enable row level security;
drop policy if exists "fav read own"   on public.favorites;
drop policy if exists "fav insert own" on public.favorites;
drop policy if exists "fav delete own" on public.favorites;
create policy "fav read own"   on public.favorites for select using (auth.uid() = user_id);
create policy "fav insert own" on public.favorites for insert with check (auth.uid() = user_id);
create policy "fav delete own" on public.favorites for delete using (auth.uid() = user_id);

-- ③ 댓글: 나라별 (누구나 읽기, 로그인 사용자가 작성, 본인 것만 삭제)
create table if not exists public.comments (
  id         bigint generated always as identity primary key,
  code       text not null,
  user_id    uuid not null references auth.users(id) on delete cascade,
  nickname   text not null check (char_length(nickname) between 1 and 20),
  body       text not null check (char_length(body) between 1 and 300),
  created_at timestamptz default now()
);
alter table public.comments enable row level security;
drop policy if exists "cmt read all"   on public.comments;
drop policy if exists "cmt insert own" on public.comments;
drop policy if exists "cmt delete own" on public.comments;
create policy "cmt read all"   on public.comments for select using (true);
create policy "cmt insert own" on public.comments for insert with check (auth.uid() = user_id);
create policy "cmt delete own" on public.comments for delete using (auth.uid() = user_id);

-- ④ 방문/조회 로그: 홈 방문(code=null) + 나라별 조회(code=국가코드)
--    원본 로그는 직접 SELECT를 막고(정책 없음=조회 불가), 집계는 아래 함수로만 노출 → 프라이버시 보호
create table if not exists public.page_views (
  id         bigint generated always as identity primary key,
  code       text,                       -- null = 홈(사이트) 방문 / 값 = 그 나라 상세 조회
  user_id    uuid references auth.users(id) on delete set null,
  created_at timestamptz default now()
);
alter table public.page_views enable row level security;
drop policy if exists "pv insert own" on public.page_views;
create policy "pv insert own" on public.page_views for insert with check (auth.uid() = user_id);
-- (SELECT 정책 없음 → 일반 사용자는 원본 로그를 직접 못 읽음. 집계만 함수로 공개)

-- 집계 함수 1: 전체 방문자 수(누적/오늘). SECURITY DEFINER = 로그 원본 없이 숫자만 반환
create or replace function public.get_visit_stats()
returns table(total bigint, today bigint)
language sql stable security definer set search_path = public as $$
  select
    (select count(*) from page_views where code is null)::bigint,
    (select count(*) from page_views where code is null
       and created_at >= date_trunc('day', now()))::bigint;
$$;

-- 집계 함수 2: 나라별 조회수(인기 순위·카드 배지용)
create or replace function public.get_view_counts()
returns table(code text, views bigint)
language sql stable security definer set search_path = public as $$
  select code, count(*)::bigint from page_views
  where code is not null group by code;
$$;

grant execute on function public.get_visit_stats() to anon, authenticated;
grant execute on function public.get_view_counts() to anon, authenticated;

-- 끝. 이제 Authentication → 익명 로그인(Anonymous)을 켜고, data.js에 키를 넣으면 동작.
