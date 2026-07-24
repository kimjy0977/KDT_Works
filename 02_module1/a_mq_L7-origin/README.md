# ORIGIN — 영감의 계보

> **디자인이 태동하던 원류에서 영감을 캐가는 아카이브.**
> 과거 화가부터 초기 디자이너들의 작업을 시대순으로 훑고, 마음에 드는 것을 나만의 무드보드에 모으고, **AI 큐레이터**가 "이게 오늘의 디자인으로 어떻게 이어졌는지"를 짚어준다.

KDT AI 에이전트 과정 · 바이브코딩2 「메인 퀘스트 — 나만의 웹 서비스 만들기」 제출물.
기획 문서는 [PRD.md](./PRD.md) 참조.

**🔗 라이브 배포: https://kdt-origin.vercel.app**

---

## 무엇을 하는 서비스인가

요즘 것에서 영감받는 곳(핀터레스트·Behance)은 넘친다. ORIGIN은 그 반대편 —
미술공예운동·아르누보·바우하우스·데 스틸·구성주의·아르데코·스위스 스타일의
**원류(原流) 작업**을 계보(오래된 뿌리 → 오늘)와 함께 보여준다.

- **아카이브 둘러보기** — 7사조 · 21작품을 시대순 그리드로
- **작품 상세** — 이미지 + 큐레이터 해설 + **AI 도슨트**("이 작업이 시작한 것 / 오늘로 이어진 지점")
- **무드보드** — 로그인 후 영감을 담기·메모(CRUD), **AI 취향 요약**("당신이 끌리는 계열은…")

---

## 기술 스택

| 층 | 기술 |
|---|---|
| 프론트엔드 | **Next.js 16 (App Router) · React 19 · TypeScript** |
| 백엔드/API | **Next.js Route Handlers** (`/api/board`, `/api/docent`, `/api/taste`) |
| DB · 인증 | **Supabase** (Postgres + Auth + Row Level Security) |
| AI | **Claude API** (서버 라우트에서만 호출 → 키 비노출) |
| 배포 | **Vercel** |

### 채점 5요소 대응
1. **PRD** — `./PRD.md`
2. **프론트 2화면↑** — 아카이브 · 상세 · 무드보드 (3화면) + 로그인
3. **백엔드 프레임워크** — Next Route Handlers로 무드보드 CRUD·AI 호출
4. **DB 연동** — Supabase 저장/조회, RLS 보안 정책 적용
5. **배포 + 새 시도** — Vercel 배포 · **로그인(Auth)** · **AI 큐레이터**

---

## 로컬 실행

```bash
npm install
cp .env.example .env.local   # 값 채우기 (아래)
npm run dev                  # http://localhost:3000
```

### 환경변수 (`.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR-PUBLISHABLE-ANON-KEY
ANTHROPIC_API_KEY=sk-ant-...
```

### DB 준비 (Supabase SQL Editor)
1. `supabase/schema.sql` 실행 — 테이블 + RLS 보안 정책
2. `supabase/seed.sql` 실행 — 7사조·37작품·6칼럼 시드 (위키미디어 퍼블릭 도메인 이미지)

---

## 보안 설계 (RLS)
- `movements`·`works` (콘텐츠) → 누구나 **읽기만**.
- `board_items` (개인 무드보드) → **쓰기·수정·삭제는 본인만**(`auth.uid() = user_id`), **읽기는 본인 또는 공개(`is_public = true`) 항목**.
- Claude API 키는 **서버 라우트에서만** 사용 → 클라이언트 번들에 노출되지 않음.

---

## 콘텐츠 출처
모든 작품 이미지는 **위키미디어 커먼즈**에서 가져왔고, 각 작품 상세페이지·`supabase/seed.sql`에 **원본 출처 링크(`source_url`)** 를 표기한다. 대부분 퍼블릭 도메인/CC이나, **개별 라이선스는 출처 페이지에서 확인**해야 한다(작품별 라이선스 일괄 보증 아님). 교육용 프로젝트.
