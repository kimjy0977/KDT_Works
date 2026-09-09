#!/usr/bin/env node
// 내 아카이브를 «남의 에이전트»에게 도구로 열어 주는 MCP 서버.
//
// 왜 만들었나 — 이 앱 안에서만 쓰이는 도구는 이 앱을 떠나면 사라진다.
// MCP 로 내놓으면 Claude Desktop·Claude Code 같은 «다른 에이전트»가 내 아카이브를 직접 쓴다.
// 도구 정의는 app/tools.js 를 «그대로» 재사용한다 — 설명과 스키마가 두 벌이 되면 반드시 어긋난다.
//
// ★의존성 0. JSON-RPC over stdio 를 직접 구현했다.
//   npm install 을 요구하면 「링크만으로」 써 보는 문턱이 올라가고, node_modules 가 레포에 섞인다.
//
// ★읽기 도구만 내놓는다. 쓰기 도구(emit_*)는 승인 게이트가 «이 앱 안»에 있으므로
//   밖으로 내보내면 게이트 없이 호출될 수 있다. 그래서 목록에서 뺀다.
//
// 쓰는 법 — Claude Desktop 설정(claude_desktop_config.json):
//   { "mcpServers": { "myth-archive": { "command": "node",
//     "args": ["<이 폴더>/mcp/server.mjs"] } } }
//
// 손으로 확인:
//   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node mcp/server.mjs

import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { TOOLS, callTool } from '../app/tools.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const archive = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'data', 'works-index.json'), 'utf8'));

// 쓰기 도구는 내보내지 않는다. 승인 게이트가 없는 곳에서 열리면 안 된다.
const EXPOSED = TOOLS.filter((t) => !t.writes);

const PROTOCOL = '2024-11-05';
const send = (m) => process.stdout.write(JSON.stringify(m) + '\n');
const ok = (id, result) => send({ jsonrpc: '2.0', id, result });
const err = (id, code, message) => send({ jsonrpc: '2.0', id, error: { code, message } });

async function handle(msg) {
  const { id, method, params } = msg;

  if (method === 'initialize') {
    return ok(id, {
      protocolVersion: PROTOCOL,
      capabilities: { tools: {} },
      serverInfo: { name: 'myth-archive', version: '1.0.0' },
      instructions:
        '신화 명화 아카이브 982점을 검색·조회하는 도구입니다. ' +
        'archive_facets 로 분포를 먼저 보고 archive_search 로 찾으세요. ' +
        'wd_* 와 commons_file 은 Wikidata·Wikimedia Commons 조회입니다. 전부 읽기 전용입니다.',
    });
  }

  // 알림에는 id 가 없다. 응답하면 안 된다.
  if (method === 'notifications/initialized' || method?.startsWith('notifications/')) return;

  if (method === 'ping') return ok(id, {});

  if (method === 'tools/list') {
    return ok(id, {
      tools: EXPOSED.map((t) => ({
        name: t.name,
        description: t.description + `\n\n반환: ${t.output}`,
        inputSchema: t.input,
      })),
    });
  }

  if (method === 'tools/call') {
    const name = params?.name;
    if (!EXPOSED.some((t) => t.name === name)) {
      // 존재는 하지만 «내보내지 않은» 도구를 부른 경우, 왜 없는지 알려 준다.
      const hidden = TOOLS.find((t) => t.name === name);
      return ok(id, {
        isError: true,
        content: [{ type: 'text', text: hidden
          ? `${name} 은 쓰기 도구라 MCP 로 열지 않습니다. 승인 게이트가 앱 안에 있어서입니다.`
          : `모르는 도구: ${name}` }],
      });
    }
    const out = await callTool(name, params?.arguments || {}, { archive });
    // MCP 는 «에러도 결과»로 돌려주는 편이 낫다 — 모델이 관찰하고 다음 행동을 정할 수 있으니까.
    return ok(id, {
      isError: !out.ok,
      content: [{ type: 'text', text: JSON.stringify(out, null, 1) }],
    });
  }

  if (id !== undefined) err(id, -32601, `지원하지 않는 method: ${method}`);
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on('line', async (line) => {
  const s = line.trim();
  if (!s) return;
  let msg;
  try { msg = JSON.parse(s); } catch { return err(null, -32700, 'JSON 파싱 실패'); }
  try { await handle(msg); } catch (e) { if (msg?.id !== undefined) err(msg.id, -32603, String(e?.message || e)); }
});
rl.on('close', () => process.exit(0));
