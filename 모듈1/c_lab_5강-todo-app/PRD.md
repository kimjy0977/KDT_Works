# PRD — 내 Todo 앱 (노드5 실습)

- **[무엇]** 내 컴퓨터에서 도는 Todo(할 일) 앱
- **[기본 기능(CRUD)]** 할 일 추가 / 목록 보기 / 완료 표시 / 삭제
- **[저장]** 데이터는 내 컴퓨터의 무료 DB(SQLite `todo.db`)에 저장 — 껐다 켜도 남기
- **[내가 넣고 싶은 기능]**
  - ① 마감일(due_date) 표시 — 지난 마감은 빨강 강조
  - ② 태그(카테고리) — 할 일 하나에 태그 여러 개 (다대다)
  - (보너스) '오늘 마감'·'남은 것'·'완료' 필터
- **[규칙]** 무료 도구만 · 비밀값은 `.env`로 · (로그인은 넣지 않음. 단일 사용자 로컬)

## DB 구조 (표 3개)

| 표 | 열 | 설명 |
|---|---|---|
| `todos` | id(PK) · title · is_done · due_date · created_at | 할 일 본체 |
| `tags` | id(PK) · name(unique) | 태그 창고 |
| `todo_tags` | todo_id(FK) · tag_id(FK) · PK(둘) | **연결표 — 다대다(N:M)** |

- `todos` 1 : N `todo_tags` N : 1 `tags` → 할 일↔태그가 다대다로 이어짐
- 회원(users) 표는 뺌 — 로컬 단일 사용자. 3부(Supabase)에서 로그인 붙이면 `todos.user_id` 추가.

## 기술 스택
- **Node.js 내장 SQLite(`node:sqlite`, v22.5+)** — `better-sqlite3` 빌드 불필요
- 순수 Node `http` 서버 + 바닐라 JS 프론트 (npm 설치 0)
