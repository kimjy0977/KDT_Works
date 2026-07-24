# ORIGIN v2 — 설계 문서 (Design Spec)

> 2026-07-22 · 레퍼런스 리서치(Are.na·Google Arts&Culture·Design Reviewed·Public Domain Review·Cosmos·Fonts In Use·Letterform·Cooper Hewitt) 기반 확장 설계.
> [PRD.md](PRD.md)의 컨셉을 유지하되, "풍부한 미술사 콘텐츠 + 맞춤 온보딩 + 이중언어 + 라이트/다크"로 확장.

---

## 1. 확장 배경

초기 v1(아카이브·상세·무드보드 3화면)은 검증 완료. v2는 사용자 피드백 3건을 반영:
1. **전문적 미술사 지식 · "디자인이 시작된 때" 칼럼** 등 풍부한 에디토리얼.
2. **관심사·직군 기반 맞춤 온보딩** (경쟁 아카이브의 공통 패턴).
3. **EN/KO 토글(영어 기본) · 다크/라이트 토글(라이트 기본).**

## 2. 채택한 레퍼런스 패턴

1. 사조/시대를 1차 브라우즈 축 + 부가 필터 (Design Reviewed, Google A&C).
2. 에세이 ↔ 작품이 한 시각 시스템에서 상호링크 (Public Domain Review, Google Stories).
3. 미술관식 존중 프레젠테이션 — 큰 액자·조용한 타입·여백 (Letterform, Cooper Hewitt).
4. 개인 컬렉션 + 메모 + 출처 (Are.na, Cosmos).
5. 가벼운 맞춤 — 행동 우선, 강제 필터 아닌 **재정렬만** (Are.na, Google A&C).

## 3. 사이트맵

| 경로 | 화면 | 핵심 |
|---|---|---|
| `/welcome` | 온보딩 | 2문항(관심 사조·직군), 건너뛰기 가능, 최초 1회 → `profiles` |
| `/` | 홈 | 레일 3개: For you(관심순) · 7사조 타일 · 추천 칼럼 |
| `/archive` | 아카이브 | 사조별 그리드, 관심순 재정렬, 사조 필터칩 |
| `/works/[id]` | 작품 상세 | 큰 이미지+출처 · AI 도슨트(직군 톤) · 담기 · 관련작품 · 관련칼럼 |
| `/essays` | 칼럼 목록 | PDR식 카드 |
| `/essays/[slug]` | 칼럼 상세 | 장문 + 본문에 작품 카드 임베드 |
| `/board` | 무드보드 | 담은 작품·메모·AI 취향요약 (+공개토글=스트레치) |
| `/profile` | 프로필 | 관심사·직군 수정 |

## 4. 온보딩 맞춤 (최소·실효)

- **Q1** 관심 사조 (복수선택): 7사조 slug.
- **Q2** 직군 (단일): graphic·product·student·illustrator·curious.
- **저장**: `profiles(interests text[], role text, onboarded_at)`.
- **효과**: 홈·아카이브가 `내 관심 사조 먼저` 정렬(`ORDER BY (movement_id = ANY(...)) DESC`). AI 도슨트 프롬프트에 role 주입 → 말투 맞춤.
- **원칙**: 강제 필터 금지(전부 탐색 가능, 순서만). "건너뛰기"·"관심 초기화" 제공.

## 5. 칼럼(에세이)

- **작품 카드 임베드형** (PDR). `essays` 테이블 + 본문 마크다운. 본문 토큰 `[[work:ID]]` → 작품 카드 인라인 렌더.
- **런칭 4편**(각 이중언어): ①디자인이라는 개념은 언제 태어났나 ②바우하우스: 학교가 만든 문법 ③스위스가 정보를 디자인한 방법 ④곡선의 시대, 아르누보.
- 상세페이지 하단에 "이 사조를 다룬 칼럼" 자동 노출(같은 movement_slug).

## 6. 이중언어 + 테마

- **언어**: 콘텐츠 `*_ko`/`*_en` 컬럼 + UI 사전(`lib/i18n.ts`). **쿠키 `lang`(기본 en)** 을 서버가 읽어 SSR 분기. 토글=쿠키 세팅+refresh. AI는 선택 언어로 응답.
- **테마**: `[data-theme]` on `<html>`, **라이트 기본**. `<head>` 인라인 스크립트가 localStorage 읽어 초기 flash 방지. 토글=localStorage+속성.
- CSS 변수 팔레트를 라이트/다크 2세트로.

## 7. 데이터 모델 변경

```
movements: + blurb_en, name_en(있음)
works:     + description_en, lineage_en
profiles(id uuid=auth.uid PK, interests text[], role text, onboarded_at timestamptz)
essays(id, slug unique, title_ko, title_en, dek_ko, dek_en, body_ko, body_en,
       hero_url, movement_slug, featured bool, sort)
board_items: + is_public bool default false  (스트레치)
```
RLS: movements·works·essays = 공개 읽기. profiles = 본인 읽기/쓰기. board_items = 본인(공개 보드는 공개 읽기 — 스트레치).

## 8. 스코프 티어

- **코어**: 이중언어+라이트/다크 · 온보딩+관심순 · 칼럼4편+임베드 · 관련작품/칼럼 · 홈 리디자인 · 프로필.
- **스트레치**: 무드보드 공개토글+공유URL · 색상 브라우징 · 칼럼 추가.

## 9. 리스크·주의

- Next16: `params` Promise, `proxy.ts`, 외부이미지 `<img>`.
- SSR 언어분기는 쿠키로(서버가 localStorage 못 읽음). 테마는 CSS라 localStorage로 충분.
- 라이브 검증·배포는 Supabase/Claude 키 수령 후 (사용자 제공 대기). **키 받기 전엔 새 schema.sql/seed.sql로 실행해야 함**(v1 SQL 아님).
- preview_screenshot 타임아웃(구글폰트+supabase) → eval/snapshot 검증.

## 10. 구현 순서(플랜)

1. 데이터: schema.sql/seed.sql 재작성(EN 콘텐츠 + essays + profiles) + essays 시드 4편.
2. 테마 시스템: 라이트 기본 팔레트 + 다크 토글 + 무플래시 스크립트.
3. i18n: 쿠키 기반 lang(en 기본) + UI 사전 + 언어 토글.
4. 온보딩 `/welcome` + profiles 저장 + 관심순 정렬 쿼리.
5. 홈 리디자인(레일 3개) + 아카이브를 `/archive`로.
6. 상세 확장(관련작품·관련칼럼·직군 톤 AI) + 칼럼 `/essays`(+임베드).
7. 프로필 · 무드보드 이중언어 · (스트레치 공개토글).
8. 빌드·검증 → 키 수령 시 라이브·배포.
