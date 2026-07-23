# 내 Todo 앱 — 노드5 · DB 실습

> 🏷️ **노드 5 · 실습(따라하기)** — 루브릭 제출 과제가 **아님**. 배운 CRUD·관계·RLS를 손에 익히는 연습 산출물.

## ▶ 라이브 데모 (클라우드 · Supabase)
### 👉 https://kimjy0977.github.io/KDT_Works/모듈1/c_lab_5강-todo-app/
> 할 일을 추가하면 **클라우드 DB(Supabase Postgres)** 에 저장돼, 새로고침·다른 기기에서도 남습니다.
> 마감일·태그(다대다) 지원. ☁️ RLS 켠 공개 데모.

같은 앱을 **두 가지 저장소**로 만든 실습입니다(강의 "길 A 로컬 / 길 B 클라우드").

---

## 구성

| 파일 | 설명 |
|---|---|
| `index.html` | **길 B · 클라우드(Supabase)** 화면 — supabase-js 직결, GitHub Pages 라이브 |
| `server.js` | **길 A · 로컬(SQLite)** 백엔드 — Node 내장 SQLite + 정적 서빙 |
| `public/index.html` | 길 A 로컬 화면 |
| `supabase_schema.sql` | Supabase에 붙여넣는 스키마(표3 + RLS + 정책) |
| `PRD.md` | 요구사항 한 장 + DB 구조 |
| `.gitignore` | `todo.db`·`.env` 등 제외 |

## 로컬(길 A)로 실행

```bash
node server.js
# 로컬(SQLite)     : http://localhost:5610/
# 클라우드(Supabase): http://localhost:5610/cloud
```
Node **v22.5+ 내장 SQLite(`node:sqlite`)** 사용 → `better-sqlite3` 빌드 불필요, npm install 0개.

## DB 구조 (표 3개 · 다대다)

- `todos`(id·title·is_done·due_date·created_at) · `tags`(id·name unique)
- `todo_tags`(todo_id·tag_id, PK 둘) = **N:M 연결표**

## 클라우드(Supabase) 보안 메모

- **RLS ON** + anon 정책(공개 데모). ⚠️ 링크 아는 사람 누구나 수정 가능 = 공개 게시판 성격.
  실서비스면 auth + `todos.user_id` + `using(auth.uid()=user_id)`로 좁힐 것(노드4 방식).
- **publishable(공개) 키만** 클라이언트에 노출 — 설계상 안전. secret 키는 절대 코드/깃에 두지 않음.

## 배운 것과의 연결
- 5·1 "껐다 켜도 남는 기억" → 새로고침·재조회로 검증
- 5·3 N:M 연결표 → 태그가 `todo_tags`로 실제 저장
- 5·4 공개 키 vs 비밀 키 / 5·5 RLS → 켠 상태로 배포
