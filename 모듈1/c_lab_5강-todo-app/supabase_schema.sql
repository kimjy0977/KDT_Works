-- ============================================================
-- 노드5 실습 3부 · Todo 앱 스키마 (kdt-nodes 프로젝트로 이관 · lab_ 접두사)
-- 실습(lab) 테이블: 과제(atlas)의 countries/comments 등과 한 DB에서 이름으로 구분.
-- ============================================================
create table if not exists public.lab_todos (
  id         bigint generated always as identity primary key,
  title      text        not null,
  is_done    boolean     not null default false,
  due_date   date,
  created_at timestamptz not null default now()
);
create table if not exists public.lab_tags (
  id   bigint generated always as identity primary key,
  name text not null unique
);
create table if not exists public.lab_todo_tags (
  todo_id bigint not null references public.lab_todos(id) on delete cascade,
  tag_id  bigint not null references public.lab_tags(id)  on delete cascade,
  primary key (todo_id, tag_id)
);
alter table public.lab_todos     enable row level security;
alter table public.lab_tags      enable row level security;
alter table public.lab_todo_tags enable row level security;
drop policy if exists "demo_lab_todos"     on public.lab_todos;
drop policy if exists "demo_lab_tags"      on public.lab_tags;
drop policy if exists "demo_lab_todo_tags" on public.lab_todo_tags;
create policy "demo_lab_todos"     on public.lab_todos     for all to anon using (true) with check (true);
create policy "demo_lab_tags"      on public.lab_tags      for all to anon using (true) with check (true);
create policy "demo_lab_todo_tags" on public.lab_todo_tags for all to anon using (true) with check (true);
