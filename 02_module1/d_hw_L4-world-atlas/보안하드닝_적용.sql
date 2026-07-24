-- ⚠️ 2026-07-24: 이 테이블들은 이후 접두사로 개명됨(a_mq_origin_* / c_lab_todo_* / d_hw_atlas_*).
-- 아래는 초기 세팅 SQL(옛 이름 기록). 현재 스키마 정본 = 라이브 DB(kdt_works). 재실행 시 개명 반영 필요.

-- ============================================================
-- 세계국가도감 · 라이브 DB 보안 하드닝 (피어리뷰 반영, 2026-07-21)
-- 실행: Supabase 대시보드 → 프로젝트(world-atlas) → SQL Editor → New query
--       → 아래 전체 붙여넣고 Run.  (SQL Editor = 오너 권한 → RLS 우회, 잔여행 삭제 가능)
-- 재실행해도 안전(idempotent).
-- ============================================================
begin;

-- 0) 리뷰 중 남은 테스트/비정상 행 정리 (comments code='ZZ_NOPE' 등) — CHECK 걸기 전 필수
delete from public.comments      where code !~ '^[a-z]{2}$';
delete from public.country_marks where code !~ '^[a-z]{2}$';
delete from public.favorites     where code !~ '^[a-z]{2}$';
delete from public.page_views    where code is not null and code !~ '^[a-z]{2}$';

-- 1) code 형식·길이 CHECK: 2글자 소문자 국가코드만 허용 (초장문 code = 저장소 고갈 DoS 차단)
alter table public.comments      drop constraint if exists comments_code_chk;
alter table public.comments      add  constraint comments_code_chk      check (code ~ '^[a-z]{2}$');
alter table public.country_marks drop constraint if exists country_marks_code_chk;
alter table public.country_marks add  constraint country_marks_code_chk check (code ~ '^[a-z]{2}$');
alter table public.favorites     drop constraint if exists favorites_code_chk;
alter table public.favorites     add  constraint favorites_code_chk     check (code ~ '^[a-z]{2}$');
alter table public.page_views    drop constraint if exists page_views_code_chk;
alter table public.page_views    add  constraint page_views_code_chk    check (code is null or code ~ '^[a-z]{2}$');

-- 2) 집계 성능 인덱스
create index if not exists page_views_code_idx on public.page_views (code) where code is not null;
create index if not exists page_views_home_idx on public.page_views (created_at) where code is null;

commit;

-- 3) 확인용 (선택 실행): 아래 3개 모두 0이어야 정상
select 'comments_bad'   as chk, count(*) from public.comments      where code !~ '^[a-z]{2}$'
union all
select 'marks_bad',            count(*) from public.country_marks where code !~ '^[a-z]{2}$'
union all
select 'pageviews_bad',        count(*) from public.page_views    where code is not null and code !~ '^[a-z]{2}$';

-- 4) ZZ_NOPE 삭제 확인 (0행이어야 함)
select * from public.comments where code = 'ZZ_NOPE';
