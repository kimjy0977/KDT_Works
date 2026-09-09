# API_SPEC — 각 부분이 서로에게 하는 약속

> **Main Quest 4 · CURATOR** · 김주영 · 2026-09-09
> 노드7 3강이 요구한 *「화면과 서버의 약속」* 문서.

> ⚠ **이 앱에는 서버가 없습니다.** 정적 배포이고 에이전트 루프가 **브라우저 안에서** 돕니다.
> 그래서 「화면 ↔ 서버」 대신 **「화면 ↔ 루프 ↔ 도구 ↔ 모델 백엔드」의 약속**을 적습니다.
> 없는 서버의 엔드포인트를 지어내지 않았습니다. (서버를 둔다면 §5 에 대응표를 적어 뒀습니다.)

---

## 0. 경계 넷

```
 ui.js  ──①──▶  agent.js  ──②──▶  tools.js  ──▶  Wikidata · Commons · 로컬 색인
   ▲               │
   └──④ onEvent ───┘
                   └──③──▶  llm.js  ──▶  Ollama · Anthropic · OpenAI
```

| # | 경계 | 계약 |
|---|---|---|
| ① | 화면 → 루프 | `newRun` · `step` / `runToApproval` · `approveAndCommit` · `reject` |
| ② | 루프 → 도구 | `callTool(name, args, ctx)` — **항상 `{ok, …}` 를 돌려준다. 예외를 던지지 않는다** |
| ③ | 루프 → 모델 | `complete(cfg, {system, messages})` — 백엔드가 달라도 **같은 모양** |
| ④ | 루프 → 화면 | `onEvent(run)` — 스텝마다. `run` 은 **전부 직렬화 가능** |

---

## 1. 화면 → 루프 (`app/agent.js`)

### `newRun({title, artist?, backend, model, workflow})`

```ts
run = {
  runId: string,            // "run-<ms>-<rand>"
  input: {title, artist},
  workflow: "intake" | "curate",
  backend, model,
  startedAt: number,
  phase: "identify"|"facts"|"license"|"dedupe"|"draft"|"approval"|"commit",
  steps: Step[],            // 트레이스 — 이게 곧 «관찰 가능성»
  toolCalls, parseFails, repairs?: number,
  usage: {in, out},
  status: "running"|"awaiting_approval"|"done"|"stopped"|"failed",
  finish: Finish|null,      // 모델이 낸 최종 초안
  gate:  Gate|null,         // ★런타임이 «다시» 매긴 안전 판정
  approved: boolean,        // ★쓰기 도구의 열쇠
  record: object|null,      // 확정된 결과물
  stopReason?: {reason, detail},
}
```

### `runToApproval(run, cfg, ctx, onEvent)`

`status !== "running"` 이 될 때까지 `step` 을 반복하고 **스텝마다 저장**한다.

```ts
cfg = {
  backend, model, host?, apiKey?, numCtx?, timeoutMs?,
  workflow?: "intake"|"curate",
  autoRepair?: boolean,
  limits?: {maxSteps, maxToolCalls, wallClockMs, maxParseFails, maxRepeat},
  complete?: Function,      // 주입점 — 데모 재생·시험용 가짜 모델
}
ctx = { archive: Work[] }   // 로컬 색인 982점
```

**기본 한도** — `maxSteps 12` · `maxToolCalls 20` · `wallClockMs 180000` · `maxParseFails 2` · `maxRepeat 3`

### `approveAndCommit(run, edits, ctx, cfg)` — ★되돌리기 어려운 작업 앞의 문

| 조건 | 결과 |
|---|---|
| `status !== "awaiting_approval"` | `{ok:false, reason:"not_ready"}` |
| `gate.blocked` | 화면이 버튼을 **잠근다**(런타임은 호출 자체는 허용하되 스키마·승인 검사) |
| 통과 | `run.approved = true` → 워크플로의 쓰기 도구 호출 → `run.record` |

`edits` 는 **사람이 고친 필드만**. `steps` 에 `{kind:"commit", editedFields:[…]}` 로 남는다.

---

## 2. 루프 → 도구 (`app/tools.js`)

### 공통 계약

```ts
callTool(name, args, ctx) -> { ok: boolean, ms: number, ...payload }
// ok:false 일 때 { reason: string, detail?: string }
```

**★실패를 예외로 던지지 않는다.** 루프가 **관찰하고 다음 행동을 정해야** 하기 때문이다.

| `reason` | 뜻 | 루프의 정상 대응 |
|---|---|---|
| `empty_query` | 질의가 비었다 | 인자를 채워 다시 |
| `bad_qid` | Q번호 형식이 아니다 | 검색 단계로 되돌아감 |
| `not_found` | 그 엔티티가 없다 | 다른 후보 / 재질의 |
| `http_4xx` `http_5xx` | 원격 응답 | 5xx·429 는 **내부에서 백오프 2회** 후 반환 |
| `timeout` `network` | 연결 | 재시도 또는 폴백 |
| `index_not_loaded` | `ctx.archive` 없음 | 호출자 잘못 |
| `repeated_call` | **같은 호출 2회째** | 인자를 바꾸거나 `finish` |
| `not_approved` | **승인 전 쓰기 시도** | **막힌다** |
| `unknown_slug` | 아카이브에 없는 작품 | 큐레이션 확정 거부 |
| `too_few` | 작품 6점 미만 | 큐레이션 확정 거부 |
| `schema` | 필수 필드 누락 | 확정 거부 |
| `unknown_tool` | 없는 도구 | 도구 목록에서 고르기 |

### 도구 8종

| 도구 | 입력 | 출력 | 권한 |
|---|---|---|---|
| `wd_search` | `{query, mode:"fulltext"\|"label", artist?, lang, limit≤5}` | `{results:[{qid,label,description}], empty}` | 읽기 |
| `wd_entity` | `{qid:/^Q\d+$/, lang}` | `{entity:{label,description,instanceOf,creator,inception,material,location,collection,movement,depicts,commonsFile,copyrightStatus}}` | 읽기 |
| `wd_sparql` | `{artistQid, limit≤30}` | `{works:[{qid,label,inception}], empty}` | 읽기 · **질의 템플릿 고정** |
| `commons_file` | `{title}` \| `{search}` | `{file:{title,imageUrl,license,licenseUrl,author,verdict}, verdict}` | 읽기 |
| `archive_search` | `{q, topK≤8}` | `{hits:[{slug,title,origTitle,artist,era,people,url,score}]}` | 읽기(로컬) |
| `archive_facets` | `{by:"myth"\|"era"\|"people", top≤25}` | `{by,total,facets:[{value,count}]}` | 읽기(로컬) |
| **`emit_record`** | 등재 레코드 | `{record}` | **쓰기 · 승인 필수** |
| **`emit_exhibition`** | `{title, statement?, sections:[{name,wallText?,works:slug[]}]}` | `{exhibition}` | **쓰기 · 승인 필수** |

`commons_file.verdict` ∈ `pd` \| `cc` \| `restricted` \| **`unknown`** — **`unknown` 이면 등재를 진행하지 않는다.**

### ★쓰기 도구의 검사 순서

1. **모델에게 카탈로그로 보여 주지 않는다**(`toolCatalog` 가 워크플로의 `tools` 만 낸다)
2. `callTool` 이 `tool.writes && !ctx.approved` → `not_approved`
3. 도구 자신이 `ctx.approved` 를 다시 검사
4. `emit_exhibition` 은 추가로 **모든 slug 가 `ctx.archive` 에 있는지** 대조

---

## 3. 루프 → 모델 (`app/llm.js`)

```ts
complete(cfg, {system, messages}) ->
  { ok:true,  text, usage:{in,out}, ms, raw? } |
  { ok:false, reason, detail, ms }
```

| 백엔드 | 엔드포인트 | 비고 |
|---|---|---|
| `ollama` | `POST {host}/api/chat` | `format:"json"` · **`think:false`**(안 끄면 한 스텝 2분 초과) · `temperature 0` |
| `anthropic` | `POST /v1/messages` | `anthropic-dangerous-direct-browser-access: true` · **키는 브라우저 밖으로 안 나감** |
| `openai` | `POST /v1/chat/completions` | `response_format:{type:"json_object"}` |
| `demo` | — | `{ok:false, reason:"demo_backend"}` — 재생은 `ui.js` 가 한다 |

`reason: "ollama_unreachable"` 은 **CORS·미기동을 사람이 읽을 수 있게** 바꾼 값이다.

### 모델이 지켜야 할 «출력 계약»

최상위 키 **정확히 하나**:

```json
{"thought":"…","action":{"tool":"…","args":{…}}}
{"thought":"…","finish":{…}}
{"thought":"…","stop":{"reason":"…","detail":"…"}}
```

**어긋나도 `normalize()` 가 받아 준다** — `action.tool === "finish"|"stop"` 승격, `action` 누락 보정.
그래도 못 읽으면 `parse_fail` 로 **2회까지 견디고** 3회째 중단하며, **모델이 뱉은 원문을 트레이스에 남긴다.**

---

## 4. 루프 → 화면 (`onEvent`)

`Step` 다섯 종류. **화면은 이 다섯만 그리면 된다.**

| `kind` | 필드 |
|---|---|
| `act` | `thought, action{tool,args}, observation, toolMs, modelMs, tokens, repaired?` |
| `parse_fail` | `raw`(모델 원문), `ms`, `tokens` |
| `finish` | `thought, finish, gate, ms, tokens` |
| `stop` / `reject` | `detail`, `thought?` |
| `commit` | `editedFields[]`, `ms` |

`observation` 은 **줄여서** 넣는다(`summarize`) — 컨텍스트가 터지면 루프가 **조용히** 망가진다.

### 저장·재개

`localStorage["mq4.runs"]` — 최근 **20건**. 초과분은 버린다(저장소가 차면 **조용히** 실패하므로).
대화는 `steps` 에서 **파생**되므로 되살린 `run` 으로 **이어서 진행**된다.

---

## 5. MCP 서버 (`mcp/server.mjs`) — 유일한 «프로토콜» 경계

**JSON-RPC 2.0 over stdio**, 줄 단위. 프로토콜 `2024-11-05`.

| method | 응답 |
|---|---|
| `initialize` | `{protocolVersion, capabilities:{tools:{}}, serverInfo:{name:"myth-archive",version}, instructions}` |
| `notifications/*` | **무응답**(id 없음) |
| `tools/list` | **읽기 6종만.** 각 `{name, description, inputSchema}` |
| `tools/call` | `{isError, content:[{type:"text", text: JSON}]}` |
| 그 밖 | `error: {code:-32601}` |

**에러도 «결과»로** 돌려준다 — 모델이 관찰하고 다음 행동을 정할 수 있어야 하므로.
쓰기 도구를 부르면 **이유를 밝히며 거부**한다(「없는 도구」라고 하면 왜 없는지 알 수 없다).

---

## 6. 서버를 «둔다면» — 대응표

이 앱은 서버가 없지만, 노드7 PRD 처럼 웹 서버를 두는 구조로 옮긴다면 이렇게 대응한다.

| 지금 (브라우저) | 서버를 둘 때 |
|---|---|
| `newRun()` | `POST /projects` → `{projectId}` |
| `runToApproval()` | `POST /projects/:id/runs` → `{runId}` · 진행은 SSE/폴링 |
| `onEvent(run)` | `GET /runs/:id/events` (스트림) |
| `run.status === "awaiting_approval"` | `GET /runs/:id` → `{status:"waiting_for_user", question, options}` |
| `approveAndCommit()` | `POST /runs/:id/answer` → 상태를 `running` 으로 되돌림 |
| `localStorage` | DB — **질문·답변·현재 단계를 저장**해야 서버 재시작 후 재개된다 |

⚠ 노드7 4강이 짚은 대로 — **새로고침과 서버 재시작은 다르다.**
서버를 두면 **메모리에서 기다리던 콜백이 재시작으로 사라지므로**, 세션 ID «만» 저장해서는 복구되지 않는다.
지금 구조는 **상태 전부가 직렬화**되어 있어 이 문제를 애초에 피한다.
