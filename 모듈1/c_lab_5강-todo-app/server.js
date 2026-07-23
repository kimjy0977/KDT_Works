// 노드5 실습 · 내 Todo 앱 (로컬 SQLite)
// Node v22.5+ 내장 SQLite(node:sqlite) 사용 → better-sqlite3 빌드 불필요.
// 실행: node server.js  (기본 http://localhost:5610)

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');

const PORT = process.env.PORT || 5610;
const DB_PATH = path.join(__dirname, 'todo.db');
const INDEX = path.join(__dirname, 'public', 'index.html');       // 로컬(SQLite) 화면
const INDEX_CLOUD = path.join(__dirname, 'index.html');           // 클라우드(Supabase) 화면 = 배포 시 GitHub Pages가 서빙하는 파일

// ---- DB 준비 (표 3개: todos · tags · todo_tags 연결표) ----
const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA foreign_keys = ON');
db.exec(`
  CREATE TABLE IF NOT EXISTS todos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    is_done    INTEGER NOT NULL DEFAULT 0,
    due_date   TEXT,                                   -- 마감일(커스텀) · 없어도 됨
    created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
  );
  CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE                           -- 태그(커스텀) · 중복 방지
  );
  CREATE TABLE IF NOT EXISTS todo_tags (               -- 다대다(N:M) 연결표
    todo_id INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (todo_id, tag_id)
  );
`);

// ---- 준비된 쿼리 ----
const q = {
  list: db.prepare(`
    SELECT t.id, t.title, t.is_done, t.due_date, t.created_at,
           GROUP_CONCAT(tg.name) AS tags
    FROM todos t
    LEFT JOIN todo_tags tt ON tt.todo_id = t.id
    LEFT JOIN tags tg      ON tg.id = tt.tag_id
    GROUP BY t.id
    ORDER BY t.is_done ASC, (t.due_date IS NULL) ASC, t.due_date ASC, t.created_at DESC
  `),
  insertTodo: db.prepare(`INSERT INTO todos (title, due_date) VALUES (?, ?)`),
  toggle:     db.prepare(`UPDATE todos SET is_done = ? WHERE id = ?`),
  remove:     db.prepare(`DELETE FROM todos WHERE id = ?`),
  insertTag:  db.prepare(`INSERT OR IGNORE INTO tags (name) VALUES (?)`),
  findTag:    db.prepare(`SELECT id FROM tags WHERE name = ?`),
  link:       db.prepare(`INSERT OR IGNORE INTO todo_tags (todo_id, tag_id) VALUES (?, ?)`),
};

function rowsToTodos(rows) {
  return rows.map(r => ({
    id: r.id, title: r.title, is_done: !!r.is_done,
    due_date: r.due_date, created_at: r.created_at,
    tags: r.tags ? String(r.tags).split(',') : [],
  }));
}

function addTodo({ title, due_date, tags }) {
  title = (title || '').trim();
  if (!title) throw new Error('제목은 필수입니다.');
  const info = q.insertTodo.run(title, due_date || null);
  const todoId = info.lastInsertRowid;
  for (const raw of (tags || [])) {
    const name = String(raw).trim();
    if (!name) continue;
    q.insertTag.run(name);
    const tag = q.findTag.get(name);
    q.link.run(todoId, tag.id);
  }
  return todoId;
}

// ---- 아주 작은 HTTP 서버 (정적 파일 + JSON API) ----
function sendJSON(res, code, data) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}
function readBody(req) {
  return new Promise((resolve) => {
    let b = '';
    req.on('data', c => (b += c));
    req.on('end', () => { try { resolve(b ? JSON.parse(b) : {}); } catch { resolve({}); } });
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const { pathname } = url;

  try {
    // --- API ---
    if (pathname === '/api/todos' && req.method === 'GET') {
      return sendJSON(res, 200, rowsToTodos(q.list.all()));
    }
    if (pathname === '/api/todos' && req.method === 'POST') {
      const body = await readBody(req);
      addTodo(body);
      return sendJSON(res, 201, rowsToTodos(q.list.all()));
    }
    const m = pathname.match(/^\/api\/todos\/(\d+)$/);
    if (m && req.method === 'PATCH') {
      const body = await readBody(req);
      q.toggle.run(body.is_done ? 1 : 0, Number(m[1]));
      return sendJSON(res, 200, rowsToTodos(q.list.all()));
    }
    if (m && req.method === 'DELETE') {
      q.remove.run(Number(m[1]));
      return sendJSON(res, 200, rowsToTodos(q.list.all()));
    }

    // --- 정적: 로컬(SQLite) 화면 ---
    if (pathname === '/' || pathname === '/index.html') {
      return fs.readFile(INDEX, (err, buf) => {
        if (err) { res.writeHead(500); return res.end('index.html 없음'); }
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(buf);
      });
    }
    // --- 정적: 클라우드(Supabase) 화면 (3부) ---
    if (pathname === '/cloud' || pathname === '/index-supabase.html') {
      return fs.readFile(INDEX_CLOUD, (err, buf) => {
        if (err) { res.writeHead(500); return res.end('index-supabase.html 없음'); }
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(buf);
      });
    }

    res.writeHead(404); res.end('Not Found');
  } catch (e) {
    sendJSON(res, 400, { error: e.message });
  }
});

server.listen(PORT, () => {
  console.log(`✅ Todo 앱 실행 중 → http://localhost:${PORT}`);
  console.log(`   DB 파일: ${DB_PATH}`);
});
