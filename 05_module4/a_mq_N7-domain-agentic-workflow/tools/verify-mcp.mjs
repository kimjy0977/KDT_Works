// MCP 서버를 «자식 프로세스로 띄워» 실제 stdio 로 두드린다.
//   node tools/verify-mcp.mjs
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER = path.join(HERE, '..', 'mcp', 'server.mjs');

const proc = spawn(process.execPath, [SERVER], { stdio: ['pipe', 'pipe', 'inherit'] });
const waiting = new Map();
let buf = '';
proc.stdout.on('data', (d) => {
  buf += d;
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
    if (!line) continue;
    const m = JSON.parse(line);
    const r = waiting.get(m.id);
    if (r) { waiting.delete(m.id); r(m); }
  }
});
let seq = 0;
const rpc = (method, params) => new Promise((res, rej) => {
  const id = ++seq;
  waiting.set(id, res);
  proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  setTimeout(() => { if (waiting.delete(id)) rej(new Error('응답 없음: ' + method)); }, 30000);
});
const call = async (name, args) => {
  const m = await rpc('tools/call', { name, arguments: args });
  return { isError: !!m.result?.isError, text: m.result?.content?.[0]?.text || '' };
};

let pass = 0, fail = 0;
const FAILS = [];
async function check(label, fn) {
  try { const msg = await fn(); console.log(`  ok   ${label}${msg ? ' — ' + msg : ''}`); pass++; }
  catch (e) { console.log(`  FAIL ${label} — ${e.message}`); FAILS.push(label); fail++; }
}
const must = (c, m) => { if (!c) throw new Error(m); };

console.log('■ MCP 서버 — 실제 stdio JSON-RPC');
await check('initialize 핸드셰이크', async () => {
  const m = await rpc('initialize', { protocolVersion: '2024-11-05', capabilities: {} });
  must(m.result?.serverInfo?.name === 'myth-archive', JSON.stringify(m).slice(0, 120));
  must(m.result.capabilities?.tools, 'tools capability 없음');
  must(m.result.instructions?.length > 40, 'instructions 가 비었다 — 남의 에이전트가 쓸 줄 모른다');
  return `${m.result.serverInfo.name} v${m.result.serverInfo.version} · ${m.result.protocolVersion}`;
});
await check('notifications 에는 응답하지 않는다 (id 없음)', async () => {
  proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  await new Promise((r) => setTimeout(r, 250));
  must(waiting.size === 0, '대기 중인 응답이 남았다');
  return '무응답 — 규약대로';
});
let names = [];
await check('tools/list — 읽기 도구만', async () => {
  const m = await rpc('tools/list');
  names = m.result.tools.map((t) => t.name);
  must(names.length === 6, `${names.length}종`);
  must(!names.some((n) => n.startsWith('emit_')), `쓰기 도구가 노출됨: ${names.filter((n) => n.startsWith('emit_'))}`);
  for (const t of m.result.tools) {
    must(t.inputSchema?.type === 'object', `${t.name} inputSchema 없음`);
    must(t.description.includes('반환:'), `${t.name} 설명에 반환 형태가 없다`);
  }
  return names.join(', ');
});
await check('archive_facets — 실데이터', async () => {
  const r = await call('archive_facets', { by: 'myth', top: 4 });
  must(!r.isError, r.text.slice(0, 90));
  const d = JSON.parse(r.text);
  must(d.total === 982 && d.facets.length === 4, r.text.slice(0, 90));
  return `${d.total}점 · ${d.facets.map((f) => f.value + ' ' + f.count).join(' · ')}`;
});
await check('archive_search — 실데이터', async () => {
  const r = await call('archive_search', { q: 'Apollo and Daphne', topK: 2 });
  must(!r.isError, r.text.slice(0, 90));
  const d = JSON.parse(r.text);
  must(d.hits.length >= 1, '결과 없음');
  return `${d.hits.length}건 · 1위 ${d.hits[0].title}`;
});
await check('★쓰기 도구는 «이유를 밝히며» 거부', async () => {
  const r = await call('emit_record', {});
  must(r.isError, '거부되지 않았다');
  must(/쓰기 도구/.test(r.text), r.text.slice(0, 90));
  return r.text.slice(0, 60);
});
await check('모르는 도구도 죽지 않는다', async () => {
  const r = await call('nope', {});
  must(r.isError && /모르는 도구/.test(r.text), r.text.slice(0, 80));
  return '에러가 «결과»로 돌아온다 — 모델이 관찰할 수 있게';
});
await check('도구 실패도 결과로 돌아온다 (예외로 안 던진다)', async () => {
  const r = await call('wd_entity', { qid: 'not-a-qid' });
  const d = JSON.parse(r.text);
  must(d.ok === false && d.reason === 'bad_qid', r.text.slice(0, 90));
  return 'bad_qid';
});
await check('지원하지 않는 method 는 JSON-RPC 에러', async () => {
  const m = await rpc('resources/list');
  must(m.error?.code === -32601, JSON.stringify(m).slice(0, 100));
  return `-32601 ${m.error.message}`;
});

proc.stdin.end();
console.log('\n' + '='.repeat(56));
console.log(`통과 ${pass} · 실패 ${fail}`);
for (const f of FAILS) console.log('  ✗ ' + f);
process.exit(fail ? 1 : 0);
