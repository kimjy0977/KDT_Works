# 보안·백엔드 리뷰 — node4-world-atlas

> 노드4 백엔드 루브릭 기준 리뷰. **라이브 Supabase 백엔드에 실제 요청을 보내 실측**한 결과를 담았습니다.
> 리뷰 대상: `country.html` · `index.html` · `data.js` · `SUPABASE_설정.sql`

---

## 0. 한 줄 결론

루브릭 4개 기준(보안 자가점검 / 실동작 백엔드 / 프론트↔백엔드 연동 / 서비스 직관성)을 **모두 충족**한다. RLS·CHECK·`SECURITY DEFINER` 집계 함수가 정석대로 구성되어 있고, 프론트를 우회한 직접 API 공격도 DB가 최종 차단한다. 다만 **익명 로그인 기반 집계 무결성**과 **`code` 컬럼 검증**에 실제 구멍이 있으며, 이는 개선으로 메울 수 있다.

---

## 1. 라이브 실측 결과 (read-only)

publishable 키로 REST API를 직접 호출해 확인:

| 점검 | 결과 | 판정 |
|---|---|---|
| RPC `get_visit_stats` | `[{"total":25,"today":12}]` | 백엔드 실동작 ✅ |
| RPC `get_view_counts` | 나라별 집계 정상 반환 | ✅ |
| `page_views` 원본 직접 SELECT | `[]` (0행) | 프라이버시 차단 ✅ |
| 남의 `favorites` SELECT | `[]` (0행) | RLS 격리 ✅ |
| `comments` SELECT | 정상(read-all) | ✅ |

## 2. 네거티브(공격) 실측 결과

익명 토큰으로 실제 공격 요청을 넣어 **거부**를 확인:

| 공격 | 응답 | 판정 |
|---|---|---|
| 댓글 301자 | `400 / 23514 comments_body_check` | 거부 ✅ |
| `kind='hack'` | `400 / 23514 country_marks_kind_check` | 거부 ✅ |
| 타인 `user_id` 위조 댓글 | `403 / 42501 RLS` | 거부 ✅ |

→ README의 "실측으로 막힘 확인" 주장은 사실이다.

---

## 3. 강점

- **이중 방어**: 프론트 `maxlength` + DB CHECK.
- **인가**: 익명 로그인 → `auth.uid() = user_id`로 본인 것만 insert/delete. 1인 1표(`country_marks` PK = `(user_id,code,kind)`).
- **프라이버시 설계**: `page_views` 원본은 SELECT 정책 없음(차단), 집계만 `SECURITY DEFINER` 함수로 노출. `set search_path = public`까지 명시(하이재킹 방어). — **이 프로젝트에서 가장 잘한 백엔드 설계.**
- **비밀값 관리**: publishable 키만 노출, `service_role` 미사용. 정확한 이해.
- **XSS**: 사용자 입력(닉네임·댓글)이 모두 `esc()`를 거쳐 렌더 → 현재 XSS 벡터 없음.

---

## 4. 발견된 문제점 (우선순위)

### P1-1. 익명 시빌 → 집계 조작 가능
- `page_views`에 사용자/기간 제약이 없어, 한 익명 유저가 API 직접 호출로 특정 나라 조회수를 무한 증가 가능. `logView`의 세션 중복방지는 클라이언트(sessionStorage)뿐이라 우회된다.
- 결과적으로 **"🔥 인기순위"는 조작 가능한 지표**다.

### P1-2. `code` 컬럼 검증 없음 (실측 확인)
- 존재하지 않는/비정상 `code`로 삽입이 그대로 통과(`201`). `code`는 **길이 제한도 없음**(2000자 통과).
- 실제 임팩트: XSS·SQLi·권한상승은 **불가**(code는 UI에서 렌더되지 않고, 쿼리는 파라미터화됨). 하지만—
  - **집계 오염**: 가짜 code가 `get_view_counts` 원본을 더럽힘.
  - **저장소 고갈(DoS)**: `code`가 길이 무제한 + `page_views`에 **DELETE 정책이 없음** → 익명 유저가 대용량 code를 무한 insert하면 **아무도 지울 수 없고** 무료 티어(500MB)를 채워 서비스 마비 가능.

### P2. 코드 견고성
- 댓글이 `innerHTML` + `esc()` 단일 방어로 렌더됨. 공격자 제어 + read-all 표면이라, 향후 `esc()` 하나만 누락하면 저장형 XSS. → 댓글 렌더는 `textContent` 권장.
- 집계 함수가 `page_views` 풀스캔(인덱스 없음).

### P3. 품질
- `index.html`/`country.html`에 인증·테마·언어토글 로직 중복(공유용 `data.js` 미활용).
- 상세 페이지마다 Wikipedia REST 5회 런타임 fetch(캐시 없음) + 히어로 이미지 Wikimedia 핫링크 → 성능·견고성 취약.
- 문서 스테일 카피(런북 "26개국" vs README "40개국" 등).

---

## 5. 개선안 (SQL)

```sql
-- (1) code 형식 화이트리스트: 형식+길이 동시 해결 (2자 고정 → 초장문 불가)
alter table public.comments      add constraint comments_code_chk      check (code ~ '^[a-z]{2}$');
alter table public.country_marks add constraint country_marks_code_chk check (code ~ '^[a-z]{2}$');
alter table public.favorites     add constraint favorites_code_chk     check (code ~ '^[a-z]{2}$');
alter table public.page_views    add constraint page_views_code_chk    check (code is null or code ~ '^[a-z]{2}$');

-- (2) page_views 저장소 고갈·조회수 인플레 방어: 1인 code별 하루 1회
alter table public.page_views add column if not exists day date
  generated always as ((created_at at time zone 'UTC')::date) stored;
create unique index if not exists page_views_dedup
  on public.page_views (user_id, coalesce(code,''), day);

-- (3) 집계 성능 인덱스
create index if not exists page_views_code_idx on public.page_views (code) where code is not null;
create index if not exists page_views_home_idx on public.page_views (created_at) where code is null;
```

프론트: 익명 기반 집계는 본질적으로 근사치이므로, README에 "집계는 익명 기반 근사치"임을 한 줄 명시하는 것이 정직하다.

---

## 6. ⚠️ 보안 점검 중 DB에 주입한 데이터 (투명성 고지)

이 리뷰는 **라이브 DB에 실제 쓰기 공격**을 포함했다. 무엇을 넣었고 어떻게 처리했는지 전부 공개한다.

### (A) 자가 정리 완료 — 흔적 없음
`comments` 테이블(삭제 정책 있음)에 아래를 삽입한 뒤 **같은 토큰으로 즉시 삭제**했다. 남은 것 없음(`204` 삭제 + 재조회 0행 확인).

| 시점 | 넣은 것 | 처리 |
|---|---|---|
| 네거티브 실측 | 301자 댓글 / `kind='hack'` / 위조 user_id | **DB가 거부** → 애초에 저장 안 됨 |
| `code` 검증 PoC | `code="ZZZZZ"`, `code`=2000자, `code="kr'; drop--"` (body 마커 `POC_CODEVAL_SELFCLEAN`) | 삽입 후 **전량 삭제 완료** |

### (B) 남아 있는 1건 — 수동 삭제 필요
초기 검증 때 `comments`에 넣은 아래 **1행**은, 삽입에 쓴 익명 토큰을 보관하지 않아 **다른 세션으로는 RLS가 삭제를 거부**한다(=인가가 정상 작동한다는 추가 증거이기도 함).

- 테이블: `public.comments`
- 내용: `id=6`, `code='ZZ_NOPE'`, `nickname='probe'`, `body='code-constraint-test'`
- UI 영향: **없음**(`ZZ_NOPE`에 해당하는 국가 페이지가 없어 화면에 노출되지 않음).

**정리 방법** — Supabase 대시보드 → SQL Editor에서:

```sql
delete from public.comments where code = 'ZZ_NOPE';
```

> 참고: 이 공격들은 모두 **삭제 정책이 있는 `comments` 테이블에서만** 수행했다. `page_views`는 DELETE 정책이 없어 되돌릴 수 없으므로(위 P1-2 참조) 의도적으로 건드리지 않았다.

---

*리뷰: 라이브 백엔드 실측 기반. 지적한 개선점은 감점 요소가 아닌 심화 제안이며, P1 두 항목만 반영해도 "보안 자가점검" 기준의 실제 구멍이 메워진다.*
