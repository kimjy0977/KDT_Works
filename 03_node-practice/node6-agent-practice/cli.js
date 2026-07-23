// 노드6 실습 · Todo 앱 CLI (얇은 진입점)
// server.js의 todo.db·테이블을 그대로 재사용. 화면 대신 터미널로 AI가 다루게.
// 실행: node cli.js <list|add|done|summary>
//   node cli.js list
//   node cli.js add "우유 사기" --due 2026-07-25 --tag 집안일
//   node cli.js done 3
//   node cli.js summary
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');

const DB_PATH = path.join(__dirname, 'todo.db');   // server.js와 같은 데이터
const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA foreign_keys = ON');

// 완료 시각 컬럼 보강(없으면 추가) — summary '오늘 완료'를 세려면 필요(강의 안내).
const cols = db.prepare('PRAGMA table_info(todos)').all().map(c => c.name);
if (!cols.includes('completed_at')) {
  db.exec('ALTER TABLE todos ADD COLUMN completed_at TEXT');
}

const q = {
  list: db.prepare(`
    SELECT t.id, t.title, t.is_done, t.due_date, t.completed_at,
           GROUP_CONCAT(tg.name) AS tags
    FROM todos t
    LEFT JOIN todo_tags tt ON tt.todo_id = t.id
    LEFT JOIN tags tg      ON tg.id = tt.tag_id
    GROUP BY t.id
    ORDER BY t.is_done ASC, (t.due_date IS NULL) ASC, t.due_date ASC, t.created_at DESC
  `),
  insertTodo: db.prepare(`INSERT INTO todos (title, due_date) VALUES (?, ?)`),
  done:       db.prepare(`UPDATE todos SET is_done = 1, completed_at = datetime('now','localtime') WHERE id = ?`),
  insertTag:  db.prepare(`INSERT OR IGNORE INTO tags (name) VALUES (?)`),
  findTag:    db.prepare(`SELECT id FROM tags WHERE name = ?`),
  link:       db.prepare(`INSERT OR IGNORE INTO todo_tags (todo_id, tag_id) VALUES (?, ?)`),
  doneToday:  db.prepare(`
    SELECT id, title, completed_at FROM todos
    WHERE is_done = 1 AND date(completed_at) = date('now','localtime')
    ORDER BY completed_at ASC
  `),
};

// ---- 명령 ----
function cmdList() {
  const rows = q.list.all();
  if (!rows.length) return console.log('(할 일이 없습니다)');
  for (const r of rows) {
    const box = r.is_done ? '[x]' : '[ ]';
    const tags = r.tags ? '  #' + String(r.tags).split(',').join(' #') : '';
    const due = r.due_date ? `  (~${r.due_date})` : '';
    console.log(`${box} ${r.id}. ${r.title}${due}${tags}`);
  }
}

function cmdAdd(args) {
  // add "제목" [--due YYYY-MM-DD] [--tag 이름 ...]
  let title = '', due = null; const tags = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--due') { due = args[++i] || null; }
    else if (args[i] === '--tag') { if (args[i + 1]) tags.push(args[++i]); }
    else if (!title) { title = args[i]; }
  }
  title = (title || '').trim();
  if (!title) { console.error('제목은 필수입니다. 예) node cli.js add "우유 사기"'); process.exit(1); }
  const info = q.insertTodo.run(title, due);
  const id = info.lastInsertRowid;
  for (const raw of tags) {
    const name = String(raw).trim(); if (!name) continue;
    q.insertTag.run(name); q.link.run(id, q.findTag.get(name).id);
  }
  console.log(`추가됨: ${id}. ${title}${due ? `  (~${due})` : ''}${tags.length ? '  #' + tags.join(' #') : ''}`);
}

function cmdDone(args) {
  const id = Number(args[0]);
  if (!id) { console.error('완료할 번호를 주세요. 예) node cli.js done 3'); process.exit(1); }
  const info = q.done.run(id);
  if (info.changes === 0) { console.error(`${id}번 할 일을 찾을 수 없습니다.`); process.exit(1); }
  console.log(`완료 처리: ${id}번`);
}

function cmdSummary() {
  const rows = q.doneToday.all();
  // 로컬 시각 기준 날짜(SQL의 date('now','localtime')와 일치). toISOString은 UTC라 자정 부근에 하루 어긋남.
  const d = new Date();
  const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  if (!rows.length) { console.log(`오늘(${today}) 완료한 할 일이 없습니다.`); return; }
  console.log(`# 오늘 완료 (${today}) — ${rows.length}건`);
  for (const r of rows) console.log(`- [완료] ${r.title} (#${r.id})`);
}

const [cmd, ...rest] = process.argv.slice(2);
switch (cmd) {
  case 'list': cmdList(); break;
  case 'add': cmdAdd(rest); break;
  case 'done': cmdDone(rest); break;
  case 'summary': cmdSummary(); break;
  default:
    console.log('사용법: node cli.js <list | add "제목" [--due YYYY-MM-DD] [--tag 이름] | done <번호> | summary>');
}
