# Todo 앱 (로컬 SQLite)

## 개요
할 일을 추가·완료·조회하는 1인용 앱. 데이터는 `todo.db`(Node 내장 SQLite)에 저장.
화면(`node server.js`) 대신, AI는 아래 **CLI(`cli.js`)**로 데이터를 다룬다.

## 명령
- 목록:       `node cli.js list`
- 추가:       `node cli.js add "<내용>" [--due YYYY-MM-DD] [--tag <이름>]`
- 완료:       `node cli.js done <번호>`
- 오늘 완료:  `node cli.js summary`

## 규칙
- 데이터는 `todo.db`에 저장한다. 화면(server.js)은 이 같은 DB를 공유한다.
- 사용자에게 보여줄 문구는 존댓말로.

## 하지 말 것
- `todo.db`(실데이터)를 직접 지우거나 덮어쓰지 말 것.
- `server.js`의 기존 로직을 갈아엎지 말 것 — `cli.js`는 얇은 진입점일 뿐.
