# ORIGIN — 영감의 계보

> 바이브코딩2 「메인 퀘스트 — 나만의 웹 서비스 만들기」 제출용 PRD
> 작성: 김주영 · 2026-07-22 · v1.0

---

## 0. 한 줄 요약

**요즘 것이 아니라, 디자인이라는 개념이 태동하던 원류(原流)를 훑으며 영감을 캐가는 아카이브.**
과거 화가부터 초기 디자이너들의 작업을 시대순으로 보고, 마음에 드는 것을 나만의 무드보드에 모으고, AI 큐레이터가 "이 작업이 오늘의 디자인으로 어떻게 이어졌는지"를 짚어준다.

---

## 1. 문제 정의 — 이 서비스가 해결하는 문제

- 요즘 디자이너의 영감 소스(핀터레스트·Behance·Dribbble)는 **"지금 유행하는 결과물"** 로 가득하다. 남들이 보는 걸 나도 보게 되니 **레퍼런스가 서로 닮아간다.**
- 정작 그 스타일들의 **뿌리** — 미술공예운동, 아르누보, 바우하우스, 데 스틸, 스위스 타이포그래피 — 는 위키·논문·절판 도서에 흩어져 있어 **"영감을 얻는 방식"으로 소비하기 어렵다.**
- 즉, **원류를 "영감 아카이브"의 형태로, 계보(오래된 뿌리 → 지금)와 함께 보여주는 서비스가 없다.**

**→ ORIGIN은 디자인의 원류를 "핀터레스트처럼 훑고 모으되, 그 계보와 현대적 의미까지 읽히는" 경험으로 제공한다.**

---

## 2. 타겟 유저

| 구분 | 설명 |
|---|---|
| 1차 | 남들과 다른 레퍼런스를 찾는 **디자이너·디자인 전공생** |
| 2차 | 미술사·디자인사에 관심 있는 **크리에이터·기획자** |
| 니즈 | "새것 말고 뿌리에서 영감 받고 싶다 / 이 스타일이 어디서 왔는지 알고 싶다" |

---

## 3. 핵심 기능 (MVP — 반드시 있어야 할 최소 기능)

1. **계보 아카이브 둘러보기** — 원류 작업들을 사조·시대순으로 탐색 (그리드/타임라인).
2. **작품 상세** — 작품 이미지 + 작가·사조·연도 + 해설. 여기에 **AI 도슨트**가 "이 작업이 시작한 것 / 오늘로 이어진 지점"을 설명.
3. **로그인 (회원가입/로그인)** — 유저별로 자기 데이터를 관리.
4. **나의 무드보드 (컬렉션 CRUD)** — 영감을 담기/메모 추가/빼기. 로그인 유저별 저장.
5. **AI 큐레이터 취향 요약** — 내 무드보드를 AI가 읽고 "당신이 끌리는 원류는 ○○ 계열" 요약.

### 발전(여유 시)
- 사조별 필터·검색, 계보 연결선 시각화, 무드보드 공개 링크 공유.

---

## 4. 화면 구성

| # | 화면 | 핵심 요소 | 데이터 흐름 |
|---|---|---|---|
| 1 | **아카이브 홈** (`/`) | 사조/시대순 작품 그리드, 필터 | DB에서 작품 목록 조회 |
| 2 | **작품 상세** (`/works/[id]`) | 이미지·메타·해설 + **AI 도슨트** + "담기" 버튼 | DB 조회 + Claude API 호출 + 무드보드 담기(API) |
| 3 | **나의 무드보드** (`/board`) | 내가 담은 작품·메모, **AI 취향 요약** | 로그인 유저의 컬렉션 조회/수정/삭제 + Claude API |
| — | **로그인** (`/login`) | 이메일 회원가입·로그인 | Supabase Auth |

→ 요구 조건 "화면 2개 이상"을 **3개 + 로그인**으로 초과 충족.

---

## 5. 데이터 구조 (DB)

Supabase(Postgres). 핵심 테이블:

> 실제 스키마 정본 = `supabase/schema.sql` · 시드 = `supabase/seed.sql`. (한/영 이중언어라 `*_en` 컬럼 포함)

```
movements  (사조)
  id, slug, name_ko, name_en, era_start, era_end, blurb, blurb_en, sort

works      (원류 작품)
  id, movement_id → movements.id,
  title, title_en, creator, year, image_url, source_url,
  description, description_en, lineage_note, lineage_en

essays     (칼럼 · 한/영)
  id, slug, title_ko, title_en, dek_ko, dek_en,
  body_ko, body_en,            -- 본문에 [[work:ID]] 토큰 → 작품 카드 임베드
  hero_url, movement_slug, featured, sort

profiles   (유저 · 온보딩 맞춤)   -- Supabase auth.users 연동
  id (= auth uid), interests text[], role, onboarded_at

board_items (무드보드 = 컬렉션)
  id, user_id → auth.users.id,
  work_id → works.id,
  note,                        -- 내 감상 메모
  is_public, created_at
  UNIQUE(user_id, work_id)     -- 중복 담기 방지
```

- **읽기 전용 콘텐츠**(movements·works·essays)는 전체 공개(RLS: select 허용).
- **개인 데이터**(profiles·board_items)는 RLS로 보호: **쓰기·수정·삭제는 본인만**(`auth.uid() = user_id`, 프로필은 `auth.uid() = id`). 단, `board_items`의 **읽기는 본인 또는 공개(`is_public = true`) 항목**까지 허용(무드보드 공개 공유용).

---

## 6. 기술 스택 & 채점 대응

| 채점 항목 | 구현 |
|---|---|
| ① PRD·기획 | 본 문서 |
| ② 프론트 화면 2개↑ | **Next.js(App Router)** — 아카이브·상세·무드보드 3화면 |
| ③ 백엔드/API 프레임워크 | **Next.js Route Handlers**(`/api/*`) — 무드보드 CRUD, AI 호출 |
| ④ DB 연동 | **Supabase Postgres** — 저장·조회, RLS 보안 |
| ⑤ 배포 + 새로운 시도 | **Vercel** 배포 + **로그인(Auth)** + **Claude API 큐레이터** |

- **AI**: Claude API를 **서버 측 Route Handler에서만** 호출 → API 키가 클라이언트에 노출되지 않음(보안).
- **인증**: Supabase Auth(이메일). 로그인 = 가점 요소.

---

## 7. 진행 순서

PRD(완료) → DB 스키마·시드 → 프론트 3화면 → 백엔드 API + 로그인 → AI 큐레이터 → Vercel 배포 → 접속 확인 → 회고·시연영상.

---

## 8. 제출물 체크리스트

- [ ] GitHub repo (코드 + 본 PRD 포함)
- [ ] 실제 접속 가능한 배포 URL
- [ ] (모듈 최종) 회고 1장 · 시연영상 3분
- [ ] 구글폼 제출: repo URL + 배포 URL — https://forms.gle/f494q8PFhHh5z6z86
