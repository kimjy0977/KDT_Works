# SAM / SPUM 연결 가이드 — 팀 《순순히 따라와라》

> 2026-08-18 작성 · 작성자: 주영 세션(실제 연결 시행착오 기록)
> **이 문서는 "실제로 해보고 확인한 것"만 적었습니다.** 확인 못 한 건 확인 못 했다고 적었어요.

## 신뢰도 표기

| 등급 | 뜻 |
|---|---|
| ★★★★★ | 직접 해봐서 성공/실패를 눈으로 확인 |
| ★★★★☆ | 공식 문서에 명시됨 |
| ★★★☆☆ | 정황상 맞을 것 (미검증) |
| ★★☆☆☆ | 불확실 |
| ★☆☆☆☆ | 안 해봄 / 근거 없음 |

---

## 0. 먼저 — "연결"이 세 가지입니다 ★★★★★

팀원마다 "연결했다"는 말의 뜻이 달라서 혼선이 있었습니다. **셋은 완전히 다른 것**입니다.

| # | 무엇 | 한 줄 정의 | 되나? |
|---|---|---|---|
| **A** | **SAM을 Claude Code의 모델 게이트웨이로** | SAM을 통해 Claude/GPT를 씀 (요금이 SAM 크레딧으로) | ✅ 공식 지원 |
| **B** | **SAM MCP (`/mcp`)** | Claude가 SAM의 툴을 호출 | ⚠️ 계정 초기화 오류로 막힘 |
| **C** | **SPUM Studio 직접 조작** | Claude가 캐릭터·맵·월드를 만들고 고침 | ✅ **성공 (이게 우리가 쓰는 방법)** |

> **팀원이 "키 주니까 됐다"고 한 건 십중팔구 A입니다.** A는 "Claude를 SAM으로 돌리는 것"이지, "Claude가 SPUM을 조작하는 것"이 아닙니다. 목적을 먼저 정하세요.

---

## 1. 공통 준비 — API 키 얻기 ★★★★★

### 1-1. 키 종류

`sam.soonsoon.ai` → **API Keys** 메뉴

| 종류 | 설명 |
|---|---|
| **Master** | 자동 생성·삭제 불가. 웹 UI 사용량 기록용 |
| **Service** | SoonSoon 서비스 전용 관리형 키 (**SAC / Chat / SPUM** 3종) |
| **Custom** | 외부 앱 연동용. 직접 생성. **월 한도 지정 가능** |

**권장: 외부 연동은 Custom 키를 새로 만들어 쓰세요.** 마스터 키는 노출되면 계정 전체가 위험합니다.

### 1-2. ⚠️ 최대 함정 — 키가 잘려 보입니다 ★★★★★

화면에는 `sam-xxxxxxxx••••` 처럼 **앞 12자만** 보입니다.
**이걸 눈으로 읽어서 타이핑하면 100% 실패합니다.** (우리가 여기서 1시간 넘게 날렸습니다)

**반드시 이렇게:**
1. 키 줄 오른쪽 **👁 (눈) 아이콘** 클릭 → 전체 표시
2. 옆의 **📋 (복사) 아이콘** 클릭 → 클립보드에 **전체 키** 복사
3. 실제 키 길이는 **약 52자** 입니다. 12자면 잘린 것.

---

## 2. 방법 A — SAM을 Claude Code 모델 게이트웨이로 ★★★★☆

> 공식 문서(`sam.soonsoon.ai/api-docs` → **Code Agents (V2)**)에 명시된 방법입니다.
> 효과: **Claude Code가 SAM을 통해 동작** → 요금이 SAM 크레딧에서 나감.

```bash
export ANTHROPIC_BASE_URL="https://sam.soonsoon.ai/v2/anthropic"
export ANTHROPIC_AUTH_TOKEN="sam-여기에전체키"
export ANTHROPIC_MODEL="claude-sonnet-5"
export ANTHROPIC_SMALL_FAST_MODEL="claude-sonnet-5"

claude "Reply with exactly: SAM-CLAUDE-OK"
```

**주의사항 (공식 문서 기재) ★★★★☆**
- `ANTHROPIC_API_KEY`가 아니라 **`ANTHROPIC_AUTH_TOKEN`** 입니다.
- 검증된 모델은 **정확히 3개**뿐 — Claude Code용은 **`claude-sonnet-5`**.
  다른 모델을 넣으면 `MODEL_NOT_NATIVE_ON_SURFACE` 오류. 폴백 없음.
- **`agent:claude_code` 권한(grant)** 이 계정에 있어야 합니다. 없으면 회사에 요청.

PowerShell이면:
```powershell
$env:ANTHROPIC_BASE_URL="https://sam.soonsoon.ai/v2/anthropic"
$env:ANTHROPIC_AUTH_TOKEN="sam-여기에전체키"
$env:ANTHROPIC_MODEL="claude-sonnet-5"
```

**Codex 쓰는 팀원은** `~/.codex/config.toml`에 base `https://sam.soonsoon.ai/v2/openai`, 모델 `openai.gpt-5.6-terra`, `wire_api="responses"`, 그리고 **`web_search="disabled"`** (안 끄면 `HOSTED_TOOL_NOT_BILLABLE` 오류). ★★★★☆

---

## 3. 방법 B — SAM MCP 연결 ★★★★★ (현재 막힘)

### 3-1. 연결 절차

```bash
claude mcp add --transport http sam-mcp https://sam.soonsoon.ai/mcp --header "Authorization: Bearer sam-여기에전체키" --scope local
claude mcp list
```

**PowerShell에서 안전하게 (키를 명령줄에 안 남기는 법):**
```powershell
$k = Read-Host
# ← 빈 줄이 뜨면 그 줄에 키만 붙여넣고 Enter
$k.Length          # 52 정도 나와야 정상. 12면 잘린 것
claude mcp add --transport http sam-mcp https://sam.soonsoon.ai/mcp --header "Authorization: Bearer $k" --scope local
```

### 3-2. ⚠️ 우리가 겪은 함정들 ★★★★★

| 증상 | 원인 | 해결 |
|---|---|---|
| `✘ Failed to connect` | **키가 앞 12자만** 들어감 | 복사 버튼으로 전체 키 |
| `MCP server sam-mcp already exists` | 이미 등록됨 → **새 키가 반영 안 됨** | `claude mcp remove sam-mcp` **먼저** 실행 |
| 헤더에 `<SPUM_KEY>` 같은 글자가 그대로 | 예시 placeholder를 안 바꿈 | 실제 키로 치환 |
| `$k = Read-Host sam-xxx` 로 넣음 | 키가 **안내문구** 자리에 들어감 | `$k = Read-Host` 만 치고, **다음 빈 줄**에 키 입력 |

### 3-3. 인증 방식 — Bearer가 맞습니다 ★★★★★

문서에는 API 키가 `X-API-Key`라고 되어 있지만, **`/mcp`는 `Authorization: Bearer`가 정답**입니다. 직접 측정 결과:

| 헤더 | `initialize` 결과 |
|---|---|
| `Authorization: Bearer <키>` | **200 OK** ✅ |
| `X-API-Key: <키>` | 503 ❌ |

### 3-4. 🚧 현재 막힌 지점 ★★★★★

연결은 되는데 **툴 목록에서 막힙니다.**

```
POST /mcp  initialize  → 200  (서버명 sam-tools v1.0.0, tools capability 있음)
POST /mcp  tools/list  → 503  {"detail":"Account initialization is temporarily unavailable. Please retry."}
```

추가로 확인한 것:
- `GET /v1/models` → **200 (1.5초)** = **키·인증은 완전 정상**
- `GET /v1/spum/*` → 전부 **30초 지연 후 503** = **계정의 SPUM 초기화가 깨진 상태**

**즉 우리 설정 문제가 아니라 SAM 계정/서버 측 문제입니다.** 재부팅·새로고침·키 교체 전부 시도했으나 안 됩니다.
그리고 `sam-tools` MCP는 **공식 문서에 아예 없습니다**(문서 전체에서 MCP 언급은 Kiro 관련 한 줄뿐). **비공식/실험 기능으로 보입니다.** ★★★★☆

> **결론: 방법 B는 현재 추천하지 않습니다.** 회사에 문의가 필요한 사안입니다.

### 3-5. 🔐 보안 주의 ★★★★★

- **`--scope project`를 쓰지 마세요.** 레포의 `.mcp.json`에 키가 박혀 **커밋됩니다** (과제 규정: SAM 키 커밋 금지).
  → `--scope local`(기본) 또는 `user` 사용. 저장 위치는 `~/.claude.json`.
- **`claude mcp get <이름>` 은 키를 화면에 평문 출력합니다.** (`add`는 `[REDACTED]`로 가리는데 `get`은 안 가림)
  화면 공유·스크린샷 중이면 조심하세요.

---

## 4. 방법 C — SPUM Studio 직접 조작 ✅ **성공한 방법** ★★★★★

> **"Claude가 SPUM을 다룬다"의 정답은 이것입니다.** MCP 없이 됩니다.

### 4-1. 원리

SPUM Studio는 **자기 서버 API**를 씁니다. 로그인된 브라우저에서 같은 출처로 호출하면 됩니다.

```
GET /api/me                     로그인 확인
GET/PUT /api/studio/state       ★ 캐스트·맵·오브젝트·월드 전체
        /api/studio/storage
        /api/studio/revisions
        /api/studio/published-worlds/{id}
        /api/worlds/
        /api/sam/v1/generate    ★ Studio가 AI를 대신 프록시 (SAM 계정 문제 우회됨)
```

**핵심: 콘텐츠는 브라우저 localStorage에 있고 서버로 동기화됩니다.**

| localStorage 키 | 내용 |
|---|---|
| `sv_studio_characters_v1` | 캐릭터(캐스트) 배열 |
| `sv_studio_maps_v1` | 맵 |
| `sv_studio_smo_v1` | 오브젝트(타일 테마) |
| `sv_studio_draft_v1` | 월드 |

### 4-2. 작업 순서 ★★★★★

```js
// 0) 백업 먼저! (Downloads에 json 파일 저장됨)
window.spumStudioData.export();

// 1) 읽기
const chars = JSON.parse(localStorage.getItem("sv_studio_characters_v1"));

// 2) 수정 (기존 캐릭터를 템플릿으로 복제해서 만드는 게 안전)
// ...

// 3) 저장
localStorage.setItem("sv_studio_characters_v1", JSON.stringify(chars));
window.spumStudioData.saveServerSnapshot("작업이유");
```

`window.spumStudioData` 에 있는 것:
`export`(백업 다운로드) · `import(file)` · `saveServerSnapshot` · `listEmergencyBackups` · `restoreEmergency` · `clearLocal` · `hasLocalData`

### 4-2-a. ⚠️ 방향이 제일 중요 — 서버에 직접 쓰지 마세요 ★★★★★

팀원이 실제로 겪은 사례입니다.

> 서버 API로 오브젝트를 만들어 **서버엔 잘 들어갔는데**(revision 69, 오브젝트 4개),
> **브라우저를 새로고침하니 브라우저에 남아있던 기존 로컬 데이터(3개)가 서버를 다시 덮어써버림.**

**원인: SPUM Studio는 브라우저 `localStorage`가 원본(source of truth)이고, 서버는 그걸 받아 저장하는 백업/동기화 대상입니다.**

| 방향 | 결과 |
|---|---|
| ❌ 서버에 직접 PUT | 다음 새로고침 때 **브라우저 로컬이 서버를 덮어씀** → 작업 소실 |
| ✅ localStorage에 쓰고 → `saveServerSnapshot()` 호출 | 정상 반영·유지 |

즉 **항상 `로컬 → 서버` 순서**입니다. 반대로 하면 날아갑니다.

### 4-3. ⚠️ 함정 ★★★★★

| 함정 | 내용 |
|---|---|
| **캐스트 배치는 코드로 하지 마세요** | 배치 ID를 직접 만들면 앱이 *"없는/중복 캐릭터 배치 N개를 정리했습니다"* 로 **전부 삭제**합니다. → World Editor 좌측 `Characters`의 **`+` → "배치" 버튼**으로 하세요. 한 명씩 누르고 확인(연속 클릭은 리렌더로 씹힘) |
| **템플릿 복제 시 외형까지 복사됨** | 캐릭터들이 쌍둥이가 됩니다. `appearance.colors`(hair/clothing/pants/eye 헥스)로 구분하세요 |
| **localStorage가 앱보다 한 박자 늦음** | 코드로 쓴 뒤엔 **페이지 새로고침**해야 앱이 읽습니다 |
| **세션이 자주 만료됨** | `/api/me`가 `{"user":null}`이면 로그아웃. 다시 로그인 필요 |

### 4-4. 데이터 스키마 (핵심만) ★★★★★

**캐릭터**
```
{ id:"CHAR_xxx", name, tags, persona, appearance, animation,
  aiConfig, talkConfig, memory, stats, meta }

persona   = {occupation, mbti, age, gender, race, class, theme,
             personality[], traits[], speechStyle, background}
memory    = {summary, engram, summarizeThreshold,
             recent[{id,at,type,source,text,mood,activity,partnerId,summarized}]}  // 최대 20개
talkConfig= {model, systemPrompt}
```

**맵**
```
{ id, name, width, height, tileSize, tileSetAssetId, mapThemeId,
  layers[], objects[], ruleTiles{}, tilesets, spawnPoints, meta }
```

**월드** (`sv_studio_draft_v1`)
```
{ id:"WORLD_xxx", title, world:{ sceneCharacterIds[], casts[], mapId,
  ai:{enabled,title,worldGoal,currentTopic,tone,conversationMode:"fsm",...} }, meta }

casts[] 항목 = {characterId, instanceId, spawnTile{col,row}, spawnX, spawnY,
                role:"npc", runtimeEnabled, id, overrides{}}
```

---

### 4-5. 맵을 코드로 쓰기 — 실제로 성공한 절차 ★★★★★

> 2026-08-19 세션에서 맵 전체를 코드로 교체해 서버 반영까지 성공. 그때 확인한 것들.

**레이어 원소 모양** (§4-4의 `layers[]` 상세):
```
layers[] = [{ name:"back_1",  type:"back",     label:"", data:[...] },   // 바닥·가구(불투명)
            { name:"front_1", type:"front",    label:"", data:[...] },   // 캐릭터 위에 덮을 것
            { name:"walkable",type:"walkable", label:"", data:[0|1] },
            { name:"obstacle",type:"obstacle", label:"", data:[0|1] }]
```
`data` 길이 = `width * height` (40×30 = 1200). 인덱스 = `y * width + x`.

**타일셋 원소 + 타일 ID 공식** (이게 핵심):
```
tilesets[] 원소 = { id:"theme_SMO_xxx", tileIdBase, columns, tileWidth, tileHeight,
                    tiles:[{assetId:"sha256:...", slot:0}, ...] }

★ 타일 ID = tileIdBase + (row * columns) + col     // row·col 은 0부터
```
우리 테마: `tileIdBase 2049` · `columns 16` · 256타일 → ID 범위 2049~2304.

**작업 순서** (§4-2와 동일하되 맵 버전):
```js
window.spumStudioData.export();                     // ① 백업
const arr = JSON.parse(localStorage.getItem("sv_studio_maps_v1"));
const m = arr.find(x => x.id === "MAP_xxx");
m.layers.find(l => l.name === "back_1").data = 새배열;   // ② 레이어 교체
m.meta.updatedAt = new Date().toISOString();
localStorage.setItem("sv_studio_maps_v1", JSON.stringify(arr));
window.dispatchEvent(new CustomEvent("spum:studio-storage-write", {detail:{key:"sv_studio_maps_v1"}}));
await window.spumStudioData.saveServerSnapshot("manual");   // ③ 서버로
// ④ 새로고침해야 앱이 읽는다
```

**⚠️ 대용량 페이로드는 압축해서 넣을 것.** 1200칸 × 4레이어를 그대로 붙이면 컨텍스트를 태운다.
런렝스 인코딩(`52x2114.2x2280...`)하면 3KB로 줄고, 페이지에서 풀면 된다.

**추가 localStorage 키** (§4-1 표에 없던 것 — 용량이 크니 통째로 읽지 말 것):
| 키 | 내용 | 크기 예 |
|---|---|---|
| `spum-map-theme-source-state:{SMO_ID}` | 타일 테마 원본 상태 | **200KB~2.8MB** |
| `spum-map-theme-export-seed:{SMO_ID}` | 테마 추출 시드 | ~120KB |
| `sv_studio_thumb_{ID}` | 썸네일(캐릭터·월드) | ~4~9KB |
| `spum_studio_server_sync_v1` | 서버 동기화 상태 | 작음 |

**UI 위치** (브라우저 자동화할 때):
- 좌측 레일: Home · World · Map · Object · Cast
- 로그인 복구: 우측 상단 `로그인 필요` 배지 → ACCOUNT 패널 → 「다시 로그인」
- Map Editor: 우측 `MAP STRUCTURE > Layers` 의 **NAV 체크박스(장애물·워커블)를 꺼야** 실제 타일이 보인다
- World Editor: 상단 `Play` 로 시뮬 시작 — **끝나면 `Pause` 로 꺼둘 것**(계속 돌면 낭비)

---

### 4-6. 캐릭터 스프라이트 시트 추출본 스키마 ★★★★★

Cast Editor 추출물은 `{이름}_idle.png` + `{이름}_idle.json` 쌍이다. **배경 투명.**

```
{ characterId:"CHAR_xxx", characterName:"새침이", state:"idle",
  clipId:"legacy/00_Idle/0_idle", duration:0.5, fps:30, totalFrames:15,
  frameWidth:128, frameHeight:128, columns:8, rows:2,
  sheetWidth:1024, sheetHeight:256, background:"transparent", zoom:0.86 }
```

→ 엔진 `Animator` 로 재생 가능. **`characterName` 으로 반드시 검증할 것**(A-4: 직전 캐릭터 시트가 내려온다).
※ 별개로 Cast **초상** PNG(`assets/chars/*.png`)는 **알파가 없다(100% 불투명)** — 배경 제거 필요.

---

## 5. ★ 중요 — World 내장 AI 대화의 한계 ★★★★★

실제로 심문을 돌려본 결과입니다. **게임 설계에 직접 영향이 있으니 꼭 읽으세요.**

**되는 것**
- 페르소나·말투 재현이 아주 좋음 (능글맞은 톤, 발랄한 톤 등)
- `역할(role)`·`목표(goal)`·`memory` 데이터는 정상 주입됨
- 비용 저렴 (대화 2턴에 SSAM 약 2)

**안 되는 것**
- **`talkConfig.systemPrompt`가 무시됩니다.** 범인 캐릭터에게 "방에 있었다고 거짓말해라"라고 지시했는데, 오히려 *"부엌 근처 돌며 냄새 맡고…"* 라고 답했습니다.
- **memory를 사실 근거로 쓰지 않습니다.** 목격자가 "살살이를 봤다"는 기억을 갖고 있는데도 *"수상한 그림자 하나"* 라고만 답했습니다.
- **메모리에 없는 내용을 지어냅니다** (발자국·그림자 등).
- 응답이 1문장 분위기용입니다.

**원인**: 캐스트 AI 패널이 **`Local FSM` 고정**이고 설정이 `model / quality / 역할 / 목표` **4개뿐** — **시스템 프롬프트 입력란 자체가 없습니다.**

> **결론: SPUM의 내장 대화는 "앰비언트 NPC 애드립" 용도입니다.**
> 규칙 기반 심문(거짓말·모순·자백)이 필요하면 **SAM `/v1/generate`를 직접 호출해서 우리가 구현**해야 합니다.
> → SPUM = 화면·캐릭터·맵 / 우리 코드 = 게임 규칙·심문. 이 분담을 권장합니다.

---

## 6. 빠른 진단 체크리스트 ★★★★★

연결이 안 될 때 위에서부터 확인하세요.

```bash
# 1) 인터넷/서버 살아있나
curl.exe -s -o /dev/null -w "%{http_code}\n" https://sam.soonsoon.ai/docs      # 200 기대

# 2) 키·인증이 유효한가  (← 이게 200이면 키는 정상)
curl.exe -s -o /dev/null -w "%{http_code}\n" https://sam.soonsoon.ai/v1/models -H "X-API-Key: sam-전체키"

# 3) MCP 등록 상태
claude mcp list
```

| 결과 | 해석 |
|---|---|
| 1번 실패 | 네트워크 or SAM 서버 다운 |
| 2번 401 | **키가 잘못됨** (잘린 키일 확률 최상) |
| 2번 200인데 MCP만 ✘ | **계정 SPUM 초기화 문제** — 회사 문의 |
| PowerShell에서 `curl` 이상동작 | `curl.exe` 로 쓰세요 (그냥 `curl`은 다른 명령) |

---

## 7. 회사 문의용 문장 (그대로 복사)

> SAM API 키 인증은 정상입니다 (`GET /v1/models` → 200). 그런데 `GET /v1/spum/*` 전 엔드포인트가 약 30초 후 `503 {"detail":"Account initialization is temporarily unavailable. Please retry."}` 로 실패하고, 그 영향으로 `POST /mcp` 의 `tools/list` 도 503이 납니다. 계정의 SPUM 초기화 상태를 확인해 주실 수 있을까요?

문의 경로: SAM 페이지 우측 **RYU 어시스턴트** / 순순팩토리 디스코드 / `soonsoon@soonsoons.com`

---

## 8. 참고 자료 현황 ★★★★★

**중요: SPUM이 두 개입니다. 검색하면 대부분 엉뚱한 쪽이 나옵니다.**

| 대상 | 자료 |
|---|---|
| **Unity 에셋 SPUM** | 위키 17페이지·유튜브·블로그 다수 — **우리와 무관** |
| **SPUM Studio (웹)** | **튜토리얼·문서·영상 0건** |

**그래서 실제로 볼 것:**

| 자료 | 링크 | 가치 |
|---|---|---|
| **공개 데모 월드** (로그인 불필요) | `spum.soonsoon.ai/studio/sai-character-world-demo/` | ★ AI 캐스트가 도는 완성 레퍼런스 |
| **클라이언트 소스 = 사실상 공식 문서** | `spum.soonsoon.ai/packages/`, `/studio/` | 압축 안 됨 + 한국어 주석 |
| SAM API 문서 | `sam.soonsoon.ai/api-docs` | 인증·모델·에러코드·IDE 연동 |
| 순순빌리지 AI 마을 사례 | `soonsoon.io/ai-spum-agent-soonsoon-village/` | AI 에이전트 마을 구현기 |

주요 소스 파일: `packages/spum-character/schema/CharacterSchema.js`, `spum-world/core/WorldCastSync.js`, `spum-map/store/MapStore.js`, `studio/ai/AgentChat.js`

**⚠️ 과제정의서가 준다고 한 문서는 실제로 받을 수 없다 (2026-08-19 확인 ★★★★★)**
과제정의서 §6 제공자료 표에 *"기술 문서(README, AGENTS.md) — API 레퍼런스 포함"* 이 ✅로 적혀 있으나,
호스트에서 확인하니 **전부 404**:
`/AGENTS.md` · `/packages/spum-engine/AGENTS.md` · `/packages/spum-engine/README.md` ·
`/packages/spum-world/README.md` → 404 (루트 `/README.md` 562B 만 200).
→ **회사에 요청할 것.** 대표와 디스코드/화상 QA가 가능하다고 명시돼 있다(§9).
그전까지는 소스가 곧 문서다.

**패키지 미러링 — `spum-world` 는 `mirror.mjs` 가 실패한다 (★★★★★)**
`mirror.mjs` 는 상대 import 를 따라가는 재귀 미러다. `spum-engine`(65파일)은 잘 되지만
`spum-world` 는 peer 의존(`spum-engine`·`spum-character`·`spum-map`)이 **bare specifier** 라 초기 fetch에서 멈춘다.
→ `index.js` 를 먼저 받아 `'./...'` 목록을 뽑고 **curl 로 개별 수신**하면 된다(23파일 확보 완료).

**죽은 링크 주의**: `soonsoon.co` 도메인은 사라졌습니다(NXDOMAIN). 검색에 나오는 SPUM 문서 링크 대부분이 무효입니다.

---

## 9. 한 줄 요약

- **Claude를 SAM으로 돌리고 싶다** → 방법 A (공식, 잘 됨)
- **Claude가 SAM 툴을 쓰게 하고 싶다** → 방법 B (현재 계정 문제로 막힘, 비공식)
- **Claude가 SPUM을 조작하게 하고 싶다** → **방법 C** ✅ 우리가 쓰는 방법
- **키가 안 먹으면** → 십중팔구 **키가 잘렸습니다.** 복사 버튼으로 다시.

---

### 4-7. Map Editor / Object Editor 실물 조사 (2026-08-19 해커톤 세션 3차) ★★★★★

> 화면에서 직접 눌러 확인한 것. 서버 rev 84 시점.

**Map Editor — `MAP STRUCTURE > Layers` 패널**

```
Navigation   : 장애물(Block) · 워커블(Walk)   ← NAV 체크박스. 켜두면 실제 타일이 안 보인다
Visual Order : +1 Front  앞 레이어 1
                0        Character          ← ★ 캐릭터가 순서의 기준점(0)
               -1 Back   뒤 레이어 1
```

- **`+ Layer` 로 레이어를 추가할 수 있다.** 새 레이어는 **더 뒤(-2)** 로 붙는다. 직접 만들어 확인함.
- **`×` 와 `Delete` 는 다르다** — `×` = **레이어 내용 비우기**("back_2 레이어를 비웠습니다"),
  하단 `Delete` = **레이어 자체 삭제**. 헷갈리면 데이터를 날린다.
- `기본맵(MAP_mr0oraoy_3ABO)` 은 이미 `back_1 · back_2 · front_1` 을 쓴다
  → **다중 back 레이어는 정상 사용법이다.** 우리 셰어하우스 맵은 `back_1` 한 장뿐.
- 타일 위에 서면 정보줄에 `detail 06 · DECORATION · PASSABLE · SPEED 1` — **타일마다 분류·통행·속도가 붙는다.**

**Object Tile Editor — 조각을 만드는 곳**

파이프라인: `Reference Prompt + Preset` → `gpt-image-2 / 품질` → **Generate**
→ **Slice**(격자로 자르기, `256 cells / 173 resources`) → **Classify**(`gemma-3-4b` 자동 분류) → 리소스

`Object Properties`:

| 필드 | 값 예 | 대응 |
|---|---|---|
| NAME / TYPE | `detail 06` / `Decor` | 분류 |
| **MOVE** | `Walk` | `collision.blocksMovement` |
| **ACTION** | `None` | **`interaction.kind`** — 상호작용을 여기서 지정 |
| SIZE / **CELLS** | `32×32` / `1` | **여러 셀을 묶은 리소스가 가능**(`floor 01` = 73 cells) |
| LAYERS | `1` | 오브젝트가 차지하는 레이어 수 |

> **★ 핵심:** 리소스는 **여러 셀 묶음**이다. 즉 "방 한 칸짜리 조각"을 만들어 맵에 통째로
> 찍는 워크플로가 Studio 의 정공법이다. 우리 `build-map.mjs` 의 "스탬프"는 이걸 코드로
> 흉내 낸 것 — **원본 워크플로가 따로 있었다.**

**SMO 데이터 스키마** (`localStorage.sv_studio_smo_v1`, 현재 3개):

```
{ id, key, name, category,
  layerHint : "back" | "front",              ← 조각이 어느 레이어로 갈지 스스로 안다
  size      : { cols, rows },                 ← 여러 칸짜리 조각
  visual    : { kind:"pixel", pixels[], palette[], tileSize },
  collision : { blocksMovement, blocksVision },   ← ★ 시야 차단 필드가 존재한다
  interaction: { kind, prompt },              ← ★ 상호작용이 1급 시민
  terrain   : { footstep, moveSpeed, staminaCost, damagePerSecond },
  tags[], mapTheme{...}, builtin }
```

**맵의 오브젝트 배열** (`spum-world/core/WorldCastSync.js:328` 확인):
`map.objects[] = { id, name, rect:{x,y,w,h}, collider?, radius? }` — **현재 두 맵 모두 0개.**

**계정 현황 실측:** cast 5명 · map 2개 · SMO 3개 · world 1개 · SSAM 44,159 · 서버 rev 84.
※ Studio 의 AI Assistant 는 "캐릭터 4개·맵 1개"라고 답한다 — **틀렸다. 화면/데이터를 믿을 것.**

### 4-8. ★ 맵은 타일 테마를 **여러 개** 물 수 있다 ★★★★★

`기본맵` 이 실증한다 — 테마마다 **2048 간격**으로 ID 공간이 할당된다.

```
map.tilesets[] = [
  { id:"builtin_tp_tile01",              tileIdBase:    1, columns: 0, tiles:   0 },
  { id:"theme_SMO_BUILTIN_STONE_WALL",   tileIdBase: 2049, columns:16, tiles: 118 },
  { id:"theme_SMO_msydcapt_6LLF",        tileIdBase: 4097, columns:16, tiles: 256 },  // ← 2049+2048
]
```

**의미:** 기존 테마를 건드리지 않고 **새 테마를 추가**할 수 있다.
셰어하우스 맵(현재 `2049~2304` 한 테마)에 러그·덮개 조각 테마를 붙이면 `4097~` 대역을 쓴다.

> ⚠ **우리 로컬 렌더러는 아직 테마 하나만 안다.** `TileMapSystem({ tileSet })` 은 타일셋이
> 단수라, 두 테마를 쓰려면 **테마별로 TileMapSystem 을 나누거나**, 빌드 때 시트 두 장을
> 한 이미지로 합쳐야 한다. (앞/뒤 타일맵을 이미 나눠 놨으므로 같은 방식으로 확장 가능)

**맵 최상위 필드 전체** (이전에 `layers`·`objects` 만 알고 있었다):
```
id · name · description · version · width · height · tileSize · tileSetAssetId ·
mapThemeId · savedAt · layers[] · objects[] · ruleTiles[] · tilesets[] · spawnPoints[] · meta
```
→ `spawnPoints[]` 가 있다. 우리는 스폰을 코드(`build-map.mjs` SPAWNS)로만 관리해 왔다.

### 4-9. Object Editor 로 타일 테마 생성 — 실측 절차와 결과 ★★★★★

> 해커톤 세션 3차에서 **실제로 한 바퀴 돌려 본** 기록. 성공/실패 둘 다 적는다.

**절차**

1. Objects 패널 우상단 `button.page-side__add` → 새 SMO 생성(빈 테마, tiles 0)
2. **에디터는 iframe 안이다** — `document.querySelector('iframe').contentDocument` 로 접근
   (부모 문서 쿼리로는 컨트롤이 하나도 안 잡힌다. work-rules B-3)
3. 설정 후 `button.generate-button`(위에서 **두 번째** — `resource-model-row` 안) 클릭
4. 완료 판정: 버튼 라벨이 `Stop` → `Generate` 로 돌아온다
5. `button.slice-action` → 셀을 리소스로 묶는다 · `#classifyTilesButton` → 자동 분류

**자동화용 컨트롤 ID** (iframe 내부)

| 대상 | 선택자 | 값 |
|---|---|---|
| 타일/테마 이름 | `#tileNameInput` | ※ 테마명 입력란이 따로 있어 잘 안 먹는다 |
| 태그 | `#themeTagsInput` | |
| 참조 프롬프트 | `#resourcePromptInput` | textarea |
| 프리셋 | (id 없음) | `desert · forest · ice · dungeon` |
| 이미지 모델 | `#resourceModelSelect` | `gpt-image-2 · gpt-image · FLUX.2-pro` |
| 품질 | `select.resource-quality-select` | `low · medium · high` |
| 테마 타입 | `#themeTypeSelect` | `map-theme · tile-set · maze-theme` |
| 격자 / 타일크기 | `#themeGridSelect` / `#themeTileSizeSelect` | `16x16` / `32` |
| 타일 분류 | `#tileCategorySelect` | `floor · obstacle_blocking · obstacle_slowing · item · decoration` |
| 통행 | `#tileMovementSelect` | `passable · blocked · slowed · none` |
| **상호작용** | (id 없음) | **`none · collect · inspect · activate`** |

**생성은 img2img 다.** `Base 16x16 Map Reference`(1024×1024) 를 소스로 쓴다. 그래서 결과가
항상 16×16 격자로 나온다. 출력: 작업영역 1024×1024 + 결과카드 192×192.

**`mapTheme.tiles[]` 는 셀이 아니라 "리소스"(셀 묶음)다**

```
{ id:"2", name:"prop 02", category:"decoration", movement:"passable",
  interaction:"none", role:"object", count:57, cells:[...57개],
  assetId:"sha256:…", confidence:1, reason:"manual",
  properties:{ blocksMovement, blocksVision, moveSpeed, terrainType } }
```

한 번 돌린 결과: **63리소스가 256셀을 나눠 가짐**
(decoration 22 · obstacle_slowing 32 · floor 5 · obstacle_blocking 4).

**⛔ 결과 — 품질 `low` 로는 "넓게 깔 수 있는" 타일이 안 나온다**

생성물을 `tools/tile-report.mjs` 와 같은 식으로 채점한 결과:

| | 기존 셰어하우스 테마 | 새로 생성(품질 low) |
|---|---|---|
| 안전(점수 ≤40) 셀 | 6 | **0** |
| 최고 점수 | 32.7 | **67.3** (안전 기준의 1.7배) |

**색은 프롬프트대로 나왔다** — hue 216 남색(`#254371`), hue 77 올리브(`#4e5d2c`).
즉 "무엇을 그릴지"는 전달됐고, **"이어붙게 그려라"가 전달되지 않았다.**
이미지 모델은 `seamless` · `edge-matching` 같은 **추상 지시를 잘 못 따른다**.

→ 다음 시도는 ① 품질을 올리고 ② 추상어 대신 **구체적 사물**로 요청할 것
   (예: "flat woven carpet, solid color with subtle even weave, no border, no fringe").

**비용:** 화면 SSAM 배지가 생성 전후 **44,159 로 동일**했다. 이미지 생성이 SSAM 을 안 쓰는 것인지
배지가 실시간 갱신되지 않는 것인지 **확인 못 함 ★★☆☆☆**. `/api/usage` 류 엔드포인트는 없다.

> 실험용으로 만든 `SMO_mszlwdtk_U91G`(Custom SMO 3)는 아직 어느 맵에도 안 붙였다.
> 재시도에 재사용하거나, 접으면 지우면 된다.

#### 4-9-b. 2차 시도 — **성공.** 무엇이 달랐나 ★★★★★

같은 파이프라인에서 **두 가지만** 바꿔 다시 돌렸다.

| | 1차 (실패) | 2차 (성공) |
|---|---|---|
| 품질 | `low` | **`high`** |
| 프롬프트 | "MOSTLY **seamless** … **edge-matching**" (추상) | "Every tile is a **PLAIN FLAT COLOR FIELD** filling the whole square edge to edge. No borders, no frames, no objects, no shadows. Only very subtle fabric weave grain, almost uniform." (구체) |
| 안전(≤40) | 0장 | **2장** |
| 최고점 | 67.3 | **27.6** |
| 자동 분류 | obstacle_slowing 32 · floor 5 | **floor 53 · decoration 1 · 전부 `passable`** |

**핵심 통찰:** 이미지 모델에 `seamless` 를 요구하지 말 것. **"평평한 단색 면"** 을 요구하면
이어붙임은 **저절로 따라온다**(균일한 칸은 좌우·상하 가장자리가 자동으로 일치한다).

부수 효과로 **자동 분류도 정확해졌다** — 1차엔 러그를 "느려지는 장애물"로 봤는데,
2차엔 54개 전부 `passable`, 53개가 `floor`. 깨끗한 면이라 분류기도 헷갈리지 않는다.

**결과물 규격:** `192×192 · 셀 12px` — **기존 셰어하우스 시트와 완전히 동일**하다.
→ 로컬 파이프라인에 그대로 붙일 수 있다. 레포에 `proto/assets/tileset_rug.png` 로 넣어 뒀다.

**시트를 로컬로 빼내는 법** (base64 를 컨텍스트로 통과시키지 말 것 — work-rules B-1):
```js
const a = d.createElement('a');
a.href = 결과이미지.src; a.download = 'sheet.png';
d.body.appendChild(a); a.click(); a.remove();     // → 사용자 다운로드 폴더
```

**채점은 로컬에서 재현된다:** `node tools/tile-report.mjs assets/tileset_rug.png`
브라우저에서 잰 값(안전 2 · 비갈색 2 · 최고 27.6)과 **정확히 일치**했다.

---

### 4-10. ★ 32×32 격자로 "집 전체 평면도" 만들기 (가장 큰 발견) ★★★★★

16×16 격자로 타일 모음을 만들어 조각내 재조립하면 **원본의 밀도와 벽 구조가 버려진다.**
격자를 키워 **평면도를 통째로** 생성하면 자르고 붙이는 과정 자체가 사라진다.

**설정** (Object Editor · iframe 내부)
```
#themeGridSelect   → 32x32      (기본 16x16)
#sourceGridSelect  → 32x32
품질 select        → high        (low 로는 디테일이 뭉개진다)
#themeTileSizeSelect → 32
```

**프롬프트의 요점 — "타일 모음"이 아니라 "평면도"를 요구한다**
```
Top-down floor plan of a cozy shared house interior, pixel art, viewed straight from above.
THICK solid wooden walls with visible depth separating rooms — walls must read as real
structures, not thin lines.
Layout: five separate bedrooms around the edges each with a differently colored rug,
one kitchen with tiled floor and refrigerator, one large central living room with a big rug
and sofas, a bathroom, and WIDE corridors connecting everything.
Each room densely furnished: beds, wardrobes, bookshelves, tables, plants, lamps.
Vary floor material per room. Asymmetric organic layout, not a grid of identical quadrants.
No characters, no text, no UI, no labels.
```

**결과:** 1024×1024 · 셀 32px. 두꺼운 나무 벽 · 방마다 다른 색 러그 · 부엌(타일 바닥) ·
욕실 · 중앙 거실 · 복도. **게임 tileSize(32px)와 1:1 이라 확대 없이 선명하다.**

**Slice 결과:** `1024 cells / 887~925 resources` — 거의 모든 셀이 고유하다.
즉 **재사용 타일셋이 아니라 한 장짜리 그림**이다. 맵에 **항등 매핑**으로 깔면 된다:
```js
back_1[y * 32 + x] = tileIdBase + y * 32 + x;
```

**통행 판정은 우리가 만들어야 한다.** 평면도는 그림이라 어디를 걸을지 모른다.
→ `tools/floorplan-mask.mjs` — 셀별 **국소 대비(색 분산)** 로 가른다.
  바닥(나무결·카펫·타일)은 균일해 분산이 낮고, 가구·벽은 윤곽선이 있어 높다.
  **색으로는 못 가른다** — 빨간 카펫과 빨간 침대가 같은 색이다.
  임계값 실측: `flat<55` → 597칸 / `flat<65` → 719칸(통로가 넓어짐).

### 4-11. ⛔ `localStorage` 5MB 한도 — 테마 두세 개면 막힌다 ★★★★★

Studio 는 **브라우저 `localStorage`(오리진당 약 5MB)** 에 먼저 쓰고 서버로 올린다.
32×32 테마 하나가 약 0.4MB, 기본 제공 `SMO_BUILTIN_STONE_WALL` 소스만 **2.67MB**.

**실측:** 사용 4.86MB / 한도 4.98MB / 남은 공간 0.13MB → `QuotaExceededError`.
서버는 931MB, 브라우저 전체 저장소는 10GB 가 남아도 **소용없다.**

**증상 — 조용히 실패한다:**
- Slice 는 성공했다고 나오는데 `mapTheme.tiles` 가 **0** (로컬에 못 씀)
- `saveServerSnapshot()` 이 **HTTP 요청도 없이 `false`** 반환, 콘솔 무음
- 새로고침하면 서버 상태가 덮어써 작업이 사라진다

**용량 확인·정리**
```js
let used = 0; for (const k of Object.keys(localStorage)) used += localStorage.getItem(k).length;
used / 1048576                                   // MB

// 고아 테마 부속 키 찾기 (참조하는 SMO 가 없는 것)
const ids = new Set(JSON.parse(localStorage.sv_studio_smo_v1).map(o => o.id));
Object.keys(localStorage)
  .filter(k => /^spum-map-theme-(source-state|export-seed):/.test(k))
  .filter(k => !ids.has(k.split(':')[1]));       // → 지워도 되는 것
```
⚠ 삭제 전 `window.spumStudioData.export()` 로 백업할 것.

### 4-12. 생성물 시트를 로컬로 빼내는 법 ★★★★★

base64 를 대화 컨텍스트로 통과시키지 말 것(work-rules B-1). 페이지 안에서 다운로드시킨다.
```js
const d = document.querySelector('iframe').contentDocument;
const img = [...d.querySelectorAll('img')]
  .find(i => i.naturalWidth === 1024 && i.parentElement.className.includes('canvas-work-area'));
const a = d.createElement('a');
a.href = img.src; a.download = 'floorplan-32.png';
d.body.appendChild(a); a.click(); a.remove();     // → 사용자 다운로드 폴더
```

---

### 4-13. ★ 테마를 맵에 **코드로** 등록하는 법 ★★★★★

Map Theme Library(THEME 버튼)에서 카드를 눌러도 **브러시만 바뀌고 맵 테마는 안 바뀐다**
(상태줄에 `Theme brush ready: …`). 맵에 붙이려면 `tilesets[]` 를 직접 만들어야 한다.

**SMO 리소스 → 타일셋 슬롯 변환** (핵심)
```js
// SMO.mapTheme.tiles[] = 리소스(셀 묶음). cells 의 column/row 는 **1-based**.
// tilesets[].tiles[] = 슬롯별 배열. slot 은 0-based.
const G = 32;                                  // 격자
const slots = new Array(G * G).fill(null);
for (const res of smo.mapTheme.tiles)
  for (const c of res.cells || [])
    slots[(c.row - 1) * G + (c.column - 1)] = res.assetId;

const tileset = {
  ...기존_tileset을_본뜬다,                     // id/name/kind/imageUrl/source/tileProperties 등
  id: 'theme_' + smo.id, themeId: smo.id, themeName: smo.name,
  tileIdBase: 4097,                            // 테마마다 2048 간격 (§4-8)
  columns: G, tileWidth: 32, tileHeight: 32,
  tiles: slots.map((assetId, slot) => ({ assetId, slot })).filter(t => t.assetId),
};
map.tilesets = [builtin, tileset];
map.mapThemeId = smo.id;
```
**타일 ID = `tileIdBase + slot`.** 평면도를 통짜로 깔 때는 항등 매핑:
```js
back_1[y * 맵폭 + (x + OFFX)] = tileIdBase + y * G + x;
```

**맵 크기 변경:** Map Editor 상단 `[40] × [30] [Apply]`. 데이터로 바꾸려면 `m.width/height` 와
**모든 레이어의 `data.length` 를 함께** 맞춰야 한다(길이 = width × height).

### 4-14. ⛔ img2img 출력은 **항상 1024×1024** — 소스 비율을 안 따른다 ★★★★★

가로로 긴 맵을 만들려고 1280×960 소스를 올려 봤지만 **결과는 1024×1024** 였다.
격자만 40×30 으로 바꾸면 `1024/40 = 25.6` 로 안 떨어져 `502 PROVIDER_ERROR: curl edit failed`.

→ **격자는 1024 를 정수로 나누는 값만 쓴다: 16×16(64px) · 32×32(32px) · 64×64(16px).**
→ 가로로 긴 맵이 필요하면 **맵 크기를 크게 잡고 평면도를 가운데 배치**한다.
   (예: 맵 44×32 에 평면도 32×32 를 `x=6..37` 에. 좌우 6칸은 집 바깥 = 통행 불가)

### 4-15. 소스 이미지 직접 올리기 (`+ Add Source`) ★★★★★

Studio 에 이미지를 넣는 **유일한 구멍**이다(임포트 기능은 없다). 파일 입력이 iframe 안에 숨어 있어
`find`/`read_page` 로는 안 잡힌다. GitHub raw 를 경유하면 컨텍스트를 안 쓰고 넣을 수 있다.
```js
const blob = await fetch(RAW_URL).then(r => r.blob());
const file = new File([blob], 'x.png', { type: 'image/png' });
const d = document.querySelector('iframe').contentDocument;
[...d.querySelectorAll('button')].find(b => /Add Source/i.test(b.textContent)).click();
const input = d.querySelector('input[type=file][accept*="image"]');
const dt = new DataTransfer(); dt.items.add(file);
input.files = dt.files; input.dispatchEvent(new Event('change', { bubbles: true }));
```
⚠ 소스 하나가 **2.7MB** 를 먹는다(§4-11 한도 주의). 재로그인하면 **소스와 프롬프트가 초기화**된다.

### 4-16. ACCOUNT 패널 = 스냅샷·백업 창구 ★★★★★

우측 상단 배지 → ACCOUNT. 여기에 전부 있다.
- **SNAPSHOTS**: `rev N` 목록(캐릭터/맵/오브젝트/월드 개수 + hash) · 「다시 로드」/「로드」
- **BACKUP**: 「내 Studio 데이터 다운로드」(JSON) · 「**로컬 데이터 로드하기**」 ← 복구는 이걸로
- 「다시 로그인」 · 저장소 용량

> ⚠ **서버 스냅샷 복원이 실패할 수 있다** — `revision 로드 실패 · studio_state_object_missing`.
> 목록은 메타데이터만 남고 실제 객체가 없는 상태. **로컬 백업 JSON 이 유일한 생명줄이다.**
> 무거운 작업 전후로 「내 Studio 데이터 다운로드」를 눌러 둘 것.

### 4-17. 브라우저 자동화 함정 (오늘 새로 겪은 것) ★★★★★

- **파일 선택창은 프로그램 클릭으로 안 열린다.** 브라우저가 사용자 조작(user activation)을 요구한다.
  → `computer` 도구의 **실제 마우스 클릭**을 써야 한다.
- **창이 1024×640 보다 작으면** SPUM 이 "데스크톱 웹으로 접속해 주세요" 모달로 화면을 덮는다.
- **미리보기 확대 상태**로 스크린샷을 찍으면 전체가 안 보인다. 결과를 판단하려면
  다운로드해서 원본을 보는 편이 빠르다.
- 생성 결과 카드(refs)는 **마지막 것이 최신이 아닐 수 있다** — `is-active` 를 확인하고,
  최신을 보려면 마지막 카드를 눌러 활성화할 것. (이걸 몰라 옛 결과를 보고 잘못 판단했다)

### 4-18. ★ 평면도 프롬프트 — 5회 비교와 최종본 ★★★★★

| 시도 | 프롬프트 성격 | 결과 |
|---|---|---|
| v1 | `seamless`, `edge-matching` (추상) | 넓게 깔 타일 0장 |
| v2 | "평평한 단색 면" + 방 목록 (구체) | 좋음 — 부엌·욕실·색색 침실 |
| v3 | "큰 거실 / 넓은 복도" 강조 | 중앙이 전부를 먹어 벽 자리 소실 |
| v4 | 칸 수를 숫자로 지정 | 구조는 잡혔으나 부엌·욕실 소실 · 돌벽 |
| **v5** | **v2 + "중앙 거실엔 벽이 없다" 한 줄 추가** | **전 조건 충족** |

> **되는 프롬프트에 조건 하나만 더한다.** 추상어는 과잉 반응하고, 수치는 구조만 잡고
> 내용을 흘린다. 전면 재작성보다 국소 추가가 안전하다.

**v5 전문 (재현용 — 32x32 · 품질 high · 기본 정사각 소스)**
```
Top-down floor plan of a cozy shared house interior, pixel art, viewed straight from above.
THICK solid wooden walls with visible depth separating rooms — walls must read as real
structures, not thin lines.
Layout: five separate bedrooms around the edges each with a differently colored rug,
one kitchen with tiled floor and refrigerator, a bathroom, and WIDE corridors connecting
everything.
IN THE MIDDLE: one large OPEN central living room that has NO walls around it —
it flows directly into the surrounding corridors with no wall segments, stubs or pillars
enclosing it. It contains only a big red rug with two sofas and a low table at its edges,
and wide clear walkable floor.
Each bedroom densely furnished: beds, wardrobes, bookshelves, tables, plants, lamps.
Vary floor material per room. Asymmetric organic layout, not a grid of identical quadrants.
No characters, no text, no UI, no labels. Warm wooden interior, warm lighting, cohesive palette.
```

### 4-19. ★ World 시뮬레이션은 실제로 대사를 만든다 (2026-08-20 검증) ★★★★★

`game-spec.md` §6 의 "World 내장 AI 는 못 쓴다"는 **대화 자체가 안 된다는 뜻이 아니었다.**
`talkConfig.systemPrompt` 를 무시한다는 뜻이고, **대사 생성은 잘 된다.**

**켜는 법:** World Editor 상단 `Play` → `sim on actors 5`.
디렉터 LLM 이 돌기 시작하고 `POST /api/sam/v1/generate` 가 나간다.

**이벤트 두 종류가 나온다.**

`director_card` — 대사가 아니라 **행동 지시**다. NPC 한 명당 하나.
```json
{ "type":"director_card", "mode":"director", "participants":["폴짝이"],
  "message":"mood=들뜬 호기심 activity=1.4 sociability=1.3
             intention=\"어젯밤 본 단서를 신나게 떠올린다\"" }
```
월드 `목적`(어젯밤 케이크 도난) 을 읽어서 **이야기에 맞는 의도**를 만든다.

`conversation_turn` — **실제 대사.** 화면 하단 「캐릭터에게 지시 또는 메시지」에
입력하면 5명이 각자 자기 말투로 답한다.
```json
{ "type":"conversation_turn", "mode":"creator_response",
  "participants":["폴짝이"], "speaker":"폴짝이",
  "line":"좋아, 어젯밤 이야기부터 풀어보자! 수상한 냄새가 나거든?",
  "thought":"창조주 메시지: ...", "emotion":"happy" }
```

실측 예 (지시: "다들 어젯밤에 뭐 했는지 서로 물어보고 이야기해봐"):
```
살살이   좋지, 수상한 밤이었으니 한 사람씩 천천히 캐보자고.
새침이   흥, 굳이 떠들썩할 건 없지만 어젯밤 일은 정리해보죠.
오물오물  좋지, 난 부엌 근처였는데 우선 간식부터 먹으며 묻자.
폴짝이   좋아, 어젯밤 이야기부터 풀어보자! 수상한 냄새가 나거든?
꾸벅이   으음, 천천히 한 명씩 어젯밤 얘기 들어보면 되겠네.
```
**성격·말투가 살아 있다**(새침이 "흥", 꾸벅이 "으음", 오물오물 간식 언급).

⚠ **한계: `mode` 가 전부 `creator_response` 다.** 5명이 각자 **나에게** 답한 것이지
서로 주고받은 게 아니다. `participants` 도 1명씩이다.
50초 자율 시뮬에서는 `conversation_turn` 이 **0건**이었다 — 지시를 넣어야 나온다.

**NPC↔NPC 왕복은 `ConversationModel.js` 가 자료구조를 갖고 있다**
(제안 → 세션 → 턴 → 종료, `thought` 필드 포함). 다만 시뮬레이터가 그 경로를
자동으로 타지는 않는 것으로 보인다.

**비용:** 지시 1회에 SAM 호출 5회(캐릭터당 1). 디렉터는 별도로 주기적으로 돈다.
50초 자율 + 지시 1회 = 약 19호출 / 크레딧 37 소모.

### 4-20. 캐릭터 AI 판단 모드는 `local_fsm` 하나뿐 (소스 확정) ★★★★★

`packages/spum-character/store/CharacterStore.js`:
```js
CHARACTER_AI_DECISION_MODES = Object.freeze(['local_fsm'])
```
`aiConfig.decisionMode` 에 다른 값을 넣어도 `normalizeCharacterDecisionMode` 가
되돌린다. **캐릭터 단위 LLM 판단 모드는 존재하지 않는다.**

→ NPC 끼리 주고받는 대화가 필요하면 **우리가 구동해야 한다**(`src/npctalk.js`).
`aiConfig.model`(gpt-5.4-mini)·`role.goal` 은 **디렉터**가 쓰는 값이지
캐릭터가 스스로 판단하는 데 쓰이지 않는다.

### 4-21. 캐릭터 스프라이트는 데이터에 없다 — 렌더 결과다 ★★★★★

`sv_studio_characters_v1` 의 캐릭터에는 픽셀이 없다.
- `appearance` = `{equipment, colors, maskEnabled}` — **조합 레시피**
- `animation.idle` = 문자열(이름), 이미지 아님

엔진의 `CharacterRenderer` 는 `ImageCache` + `SkeletonData.SPRITE_KEY_MAP` 으로
**파츠 이미지를 조합해 그린다.** 그런데 `proto/vendor` 에 미러된 PNG 는 **0개**다
(파츠 아틀라스는 SPUM 서버에 있다).

→ 시트를 얻는 경로는 **Cast Editor 의 Export 뿐**이다. `CharacterStore.js` 에도
시트를 뽑는 API 는 없다. Export 는 A-4 함정(직전 캐릭터 시트가 내려옴)이 있으므로
받은 JSON 의 `characterName` 을 건건이 확인할 것.

### 4-22. 평면도 프롬프트 — 문을 그리게 하지 말 것 ★★★★★

생성된 방 입구에 **문짝·해치가 그려지면 그 칸은 벽으로 판정된다.**
우리는 문을 여는 로직이 없으므로 그 방은 영영 못 들어간다.

프롬프트에 다음을 명시할 것:

```
⚠ NO DOORS ANYWHERE. Every room opening is an EMPTY GAP in the wall — no door panels,
no hatches, no sliding doors, no airlocks, no frames across the opening. Rooms connect
through plain open gaps you can walk straight through.
```

실제로 우주선 1차 생성에서 격실 입구마다 금속 해치가 그려져 통행이 막혔다.

### 4-23. 격자는 1024 를 정수로 나누는 값만 ★★★★★

img2img 출력은 **항상 1024×1024** 다(§4-14). 따라서 쓸 수 있는 격자는:

| 격자 | 셀 | 비고 |
|---|---|---|
| 16×16 | 64px | 너무 성김 |
| 32×32 | 32px | 셰어하우스가 이것 |
| **64×64** | **16px** | 50×50 요청 시 여기로 올림 — 50 은 20.48px 이라 불가 |
| 128×128 | 8px | 너무 잘음 |

**50×50, 60×40 같은 값은 그대로 안 된다.** 가로로 긴 맵이 필요하면
64×64 로 뽑아 중앙 40행만 쓰는 식으로 **로컬에서 잘라야** 한다.

⚠ **새 SMO 는 격자 16×16, 품질 Low 로 시작한다.** 생성 전에 둘 다 확인할 것.
격자 숫자칸은 React 셀렉트가 되돌리므로 **숫자 입력칸에 직접** 넣는다(64, 64).

### 4-24. ★ 격자를 키워도 맵이 넓어지지 않는다 ★★★★★

**가장 흔한 착각이다. 격자 숫자는 "해상도"지 "넓이"가 아니다.**

AI 는 격자와 무관하게 **1024×1024 캔버스에 장면 하나**를 그린다. 격자를 32→64 로 올리면
**같은 그림을 더 잘게 썰 뿐**이다. 캐릭터만 그대로고 방·가구가 전부 두 배가 된다.

| | 32 격자 | 64 격자 |
|---|---|---|
| 방 하나 | 8×8 칸 | **16×16 칸** |
| 침대 하나 | 2×3 칸 | **4×6 칸** |
| 캐릭터 | 1.6칸 | 1.6칸 |
| 체감 | — | **좁은 집을 확대한 것** |

> 사용자 비유: *"천장이 낮아 높여 달랬더니 가구까지 다 커졌다."*

**넓이를 늘리는 진짜 레버는 프롬프트의 밀도다.** 같은 캔버스에 **방을 더 많이, 더 작게**
그리게 해야 한다.

```
⚠ SCALE: draw SMALL. This is a whole deck seen from far away, not a few rooms zoomed in.
Fit MANY compartments into the image — each room should be SMALL, roughly 1/9 of the image width.
A bunk is a tiny rectangle, a crate is a few pixels. Think blueprint density, not close-up detail.

CONTENT: at least SIXTEEN separate compartments — ... and LONG WINDING CORRIDORS linking them.
THIN walls (about 1/64 of the image wide) so corridors stay wide and walkable.
```

정리하면:

| 원하는 것 | 바꿀 것 |
|---|---|
| 타일이 잘아지길(그림이 선명) | **격자** 32 → 64 |
| **걸을 공간이 넓어지길** | **프롬프트 밀도** — 방 8개 → 16~20개, 벽을 얇게 |
| 둘 다 | 격자 64 **+** 밀도 프롬프트 |

⚠ 격자만 올리고 프롬프트를 그대로 두면 **아무것도 넓어지지 않는다.** 실제로 그렇게 한 번 헛돌았다.

### 4-25. ★ 평면도 프롬프트 정본 — 구조화 템플릿 ★★★★★

지금까지 프롬프트를 감으로 고쳐 왔다. OpenAI 이미지 모델 프롬프트 가이드를 찾아
**근거 있는 구조**로 다시 썼다. 출처는 이 절 끝.

**핵심 원칙 4가지**

1. **라벨 + 줄바꿈으로 나눈다.** 한 문단으로 길게 쓰지 말 것. 모델은 구조에 보상하고
   모호함에 벌을 준다.
2. **순서를 지킨다:** 용도 → 장면 → 대상 → 세부 → 제약 → 스타일
3. **재질을 구체적으로.** "shiny metal" ✗ → **"brushed steel"** ✓
4. **금지 목록을 명시적으로 나열한다.** "무엇을 유지하고 무엇을 바꿀지" 둘 다 적는다.

**정본 템플릿** (테마만 바꿔 재사용)

```
USE CASE: a top-down tile map for a 2D game. Read like an architect's floor plan.

SCENE:
One entire <장소> seen from directly above, drawn small and far away.
The whole <장소> fills the image edge to edge.

SUBJECT:
Sixteen or more small rooms — <방 목록> — linked by long winding corridors.
In the centre, one open <공용공간> holding a single small <가구>.

DETAILS:
Each room is about one ninth of the image wide. A bed is a small rectangle.
Walls are THIN, about one sixty-fourth of the image wide.
Materials: <구체적 재질 3개>.
Each room has a differently coloured floor; corridors share one continuous <바닥재>.

FLOOR CONTINUITY (important):
The floor runs UNBROKEN from every corridor straight into every room.
At a room entrance the floor colour changes, but the surface stays FLAT and CONTINUOUS —
no step, no raised lip, no threshold strip, no frame, no trim line across the opening.
A person could walk from corridor to room without stepping over anything.

CONSTRAINTS — the image must NOT contain:
- doors of any kind: no door panels, hatches, sliding doors, or frames across an opening
- free-standing wall stubs, lone pillars, or partial walls that lead nowhere
- any wall that does not separate two different rooms
- thresholds, door sills, steps, or trim strips between corridor and room
- characters, text, UI, labels, watermarks, borders, or a frame around the image

STYLE: pixel art, <분위기>, cohesive palette, straight top-down, no perspective.
```

**각 블록이 푸는 문제**

| 블록 | 없으면 생기는 문제 |
|---|---|
| `USE CASE` | 일러스트처럼 그려서 타일로 못 씀 |
| `SCENE` + "drawn small" | 방 몇 개를 확대해 그림 (§4-24) |
| `DETAILS` 의 "one ninth" | 방이 커져 걸을 공간이 안 늘어남 |
| **`FLOOR CONTINUITY`** | 방 입구에 문턱·테두리가 생겨 **바닥이 끊김** |
| **`CONSTRAINTS` 문 금지** | 문짝이 벽으로 판정돼 **방에 못 들어감** (§4-22) |
| **`CONSTRAINTS` 벽 금지** | **어디에도 안 붙은 벽 토막**이 생겨 통로를 막음 |
| `no borders` | 프레임 테두리 1px 선 (스프라이트에서도 같은 문제, work-rules) |

**출처**
- OpenAI Cookbook — GPT Image Models Prompting Guide
  https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide
- OpenAI Cookbook — gpt-image-1.5 Prompting Guide
  https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide

---

### 4-26. 격자 64 는 "맵 4배"가 되지만 마스크가 어려워진다 ★★★★★

`4-24`("격자를 키워도 맵이 넓어지지 않는다")의 후속. 넓히는 법은 **격자 + 정수배 확대**다.

| | 셰어하우스 | 우주선 |
|---|---|---|
| 격자 | 32 | **64** |
| 원본 셀 | 32px | 16px |
| 확대 | 그대로 | **×2 (최근접)** |
| 타일셋 | 1024² | **2048²** |
| 맵 | 32×32 타일 | **64×64 타일 (면적 4배)** |

셀이 32px 보다 작으면 `build-world-map.mjs` 가 정수배로 키운다. 픽셀아트라
최근접 확대해도 뭉개지지 않고, 가구가 캐릭터 대비 **원래 비율을 유지**한다.

⚠ 대가: 셀 16px 이 그림의 바닥 타일 한 장과 같은 크기가 되어 **픽셀 기반 통행 판정이
무너진다**(work-rules M-1). SPUM Slice 의 role 을 쓸 것(M-2).

⚠ `60×40` 같은 가로로 긴 맵은 **불가능하다** — img2img 출력이 항상 정사각 1024²(§4-14)라
잘라내야 하는데, 잘라내면 방이 통째로 날아간다. 대신 격자를 키워 **면적**으로 넓힌다.

---

### 4-27. ★ World 대화는 세 가지 모드가 있다 — 우리는 `baked` 로 쓰고 있었다 ★★★★★

`§4-19` 에서 "World 시뮬레이터도 대사를 만들지만 모든 턴이 `creator_response` 라 서로
주고받지 않는다"고 적었다. **원인을 찾았다. 모드가 `baked` 였다.**

**월드 설정 → 대화 시스템** (`world.ai` 에 저장)

| 항목 | 값 | 뜻 |
|---|---|---|
| **`conversationMode`** | **`fsm` \| `baked` \| `llm`** | FSM(더미 풀) · **베이킹 데이터** · **실시간 LLM** |
| `llmModel` / `controlModel` | `light` \| `medium` \| `expert` | 대화 모델 · 제어 모델 |
| `worldGoal` | 문자열 | 월드 목표 |
| `currentTopic` | 문자열 | 현재 화제 |
| `autonomy` | `balanced` | 자율성 |
| `directiveMode` | `character_based` | 지시 방식 |
| `globalRules` | `[]` | 전역 규칙 |
| `missionManagerEnabled` / `Interval` | `false` / `7` | 자동 미션 생성 |
| `timeScale` · tempo · speed | 1 | 행동 템포 · 월드 속도 |

`baked` 는 **베이크 탭에서 미리 구워 둔 대사를 재생**한다. `bakeBuilder` 가 그 설정이다:
`threadCount 8 · turnsPerThread 4 · thoughtCount 2 · maxLineChars 54 · generationMode "company"`.
즉 8스레드 × 4턴을 SAM 으로 한 번 생성해 두고 계속 튼다. **유동적일 수가 없다.**

⚠ 함정: `bakeBuilder.sourceText` 가 **"평화의 픽셀월드를 만드는 것입니다"** 로 남아 있었다.
우리 사건과 무관한 원문으로 구운 대사를 틀고 있었던 것이다. 베이크를 쓸 거면 여기부터 고칠 것.

**`runtime` 표시가 진실을 말해 준다** — 퍼블리시 베이크 패널의 `runtime: dummyconversation
bakeddata`. 이게 `dummyconversation` 이면 실시간이 아니다.

**`llm` 로 바꾼 뒤 실측 (2026-08-20)**
- 화면·`sv_studio_draft_v1.world.ai.conversationMode` 둘 다 `llm` 로 바뀜 ★★★★★
- Play → `sim on · actors 5` 로 시뮬레이션은 돌아감 ★★★★★
- **그런데 30초 동안 "아직 AI 통신 로그가 없습니다"** — 대사가 안 나온다 ★★★★★
  → 모드만 바꿔선 부족하다. 트리거(근접·지시·화제)가 더 필요한 것으로 보인다 ★★☆☆☆

**`<select>` 는 JS 로 못 바꾼다**(React 가 되돌림). 클릭해 포커스를 준 뒤 **방향키**로 옮기면
`change` 가 정상 발생한다. 이번에 이 방법으로 성공했다.

### 4-28. 캐스트 스키마 v2 — 대화에 영향을 주는 필드 ★★★★☆

`sv_studio_characters_v1` (캐릭터 6명)

```
persona   : occupation · mbti · age · gender · race · class · theme
            personality[] · traits[] · speechStyle · background
            creatorResponseLevel (0~100, 기본 50)   ← 창조주 응답 성향
profiles  : coreStats(RPG 8스탯) · rpg · village{role, affinity, energy, mood, schedule[]}
appearance: equipment{body,eye,hair,helmet,...}
```

- **`creatorResponseLevel`** — `§4-19` 의 "모든 턴이 `creator_response`" 와 이름이 겹친다.
  낮추면 창조주 대신 서로에게 말할 가능성이 있다 ★★☆☆☆ (미검증)
- **`village.schedule[]`** — 비어 있다. 시간대별 행동을 넣는 자리로 보인다 ★★☆☆☆
- 캐스트 배치 패널의 `view` = `auto | rpg | village | social` — 어떤 스탯 묶음을 쓸지
- `mood` = `calm | happy | excited | tired | sad | angry`

⚠ **월드에 캐릭터가 5명뿐이다**(두리번이 없음). 로컬 게임은 6명이다. 무대가 어긋나 있다.

### 4-29. ★ `llm` 모드는 진짜로 NPC 끼리 대화한다 — 실측 전문 ★★★★★

`§4-27` 에서 모드만 바꿨을 땐 로그가 비어 있었다. **원인은 트리거였다.**
캔버스 아래 지시 입력창에 한 줄 넣자 즉시 대화가 시작됐다.

```
다들 거실에 모여서 어젯밤 냉장고 케이크가 없어진 일을 서로 이야기하세요.
한 명씩 어젯밤 어디 있었는지 말하고, 남의 말에 반응하세요.
```

**로그 구조** (JSONL 내려받기 가능 — Event Log 우측 `JSONL`)

```
Conversation start (llm): A ↔ B      ← 짝 단위. 여러 짝이 동시에 돈다
Conversation log: director_card       ← 디렉터가 화제·짝을 조율한다
LLM request:  A → B · medium
LLM response: <대사>
Conversation turn (llm): A · <대사>   ← turn 0,1,2,3,4 로 이어짐
Conversation end (llm): A ↔ B · complete
```

**실제로 나온 대화** (교차 검증이 성립한다)

```
살살이   에이, 누가 그랬을까 웃기지, 근데 폴짝이 너 어젯밤 복도에서 뭐 못 봤어?
폴짝이   어머, 있잖아! 내가 열한 시쯤 냉장고 앞에서 포크 짤랑거리는 소린 들었는데,
         발소리는 살짝살짝이었어!
살살이   오, 포크까지 챙긴 정성이면 초범은 아닌데, 살짝살짝이면 오물오물 쪽이 더 수상하지 않아?
폴짝이   어머 맞아, 근데 있잖아! 오물오물은 그때 콧노래였고, 냉장고 앞 그림자는
         네 방 쪽으로 훅 갔어!

새침이   좋아, 말로 넘기지 말고 어젯밤 네가 몇 번 열었는지부터 말해.
오물오물 음, 열긴 두 번 열었어어, 근데 케이크는 안 건드렸고 요거트랑 남은 만두만 봤다아.
새침이   두 번이면 충분히 수상하거든, 몇 시였는지랑 케이크 자리가 비어 있었는지 말해.
오물오물 으음, 열한 시쯤엔 케이크 있었고, 자정 넘어서 봤을 땐 접시만 남아 있었어어.
```

**LLM 요청에 실리는 필드** — 우리 로컬 구현보다 풍부하다

```json
{ "speaker","partner","topic","turn",
  "deployMode":"off", "baseBehavior":"cooperative", "worldTone":"cozy-mystery",
  "relationship":{ "trust":0.5,"familiarity":0,"tension":0,"affinity":0,
                   "emotion":"","summary":"","recentSummary":"",
                   "lastInteractionAt":0,"importantConversationIds":[] },
  "recentCount":0, "nearbyObjectCount":0 }
```

→ **관계 모델(trust·familiarity·tension·affinity)과 대화 요약·중요 대화 id 가 이미 있다.**
우리 로컬 엔진에는 없는 축이다.

**화제는 짝마다 다르게 배정된다** (director_card 가 정하는 것으로 보임 ★★★☆☆)
`범인은 누구일까?` · `아는 것이 없음을 설명한다` · `새침한 사람의 일상` · 내가 넣은 지시문.

**비용:** 위 대화 한 판(대사 17턴)에 SSAM 약 250.

### 4-30. 베이크 탭의 `purpose` 가 `company` 였다 ★★★★☆

`presetId` `frame-compact | frame-link-balanced | link-rich | custom` ·
`detailLevel` `summary | balanced | rich` · `model` `light | medium | expert` ·
**`purpose` `company | product | story | qa`**

우리는 `company`(회사 소개) + sourceText "평화의 픽셀월드" 로 구워 놓고 있었다.
베이크를 쓸 거라면 **`story`** 로 바꾸고 sourceText 를 사건 설명으로 갈아야 한다.
다만 `llm` 모드를 쓰면 베이크 자체가 필요 없다.

---

### 4-31. ★★ Studio World 전체 데이터 모델 — 미확인 기능 일괄 조사 ★★★★★

> 2026-08-20. "확인 못 한 기능"으로 남겨 뒀던 10건을 데이터 층에서 확정한다.
> UI 라벨보다 `sv_studio_draft_v1` · `sv_studio_characters_v1` 이 정확하다.

#### (1) `world` 최상위

```
sceneCharacterIds[]  unitPixelScale  ai{}  mapId  mapResourceId
bakeBuilder{}  casts[]  runtime{bakedData}  publishBake{}
```

**`events` · `props` · `story` · `missions` 키는 아예 없다.** UI 의 Events(0)·Props(0)·
스토리 탭은 **아직 데이터가 없는 빈 기능**이다. 스토리 탭은 「스토리 재생/중지」 버튼만
있고 입력 필드가 없다 → 별도 생성물이 있어야 재생되는 구조로 보인다 ★★☆☆☆.

#### (2) `world.ai` — 월드 AI 전체

| 필드 | 값 | 비고 |
|---|---|---|
| `conversationMode` | `fsm \| baked \| llm` | §4-27 |
| `worldGoal` | 문자열 | 월드 전체 목표 |
| `currentTopic` | 문자열 | **지시창에 넣은 말이 여기 덮어써진다** (실측) |
| `tone` | `cozy-mystery` | 프롬프트에 `worldTone` 으로 실림 |
| `autonomy` | `balanced` | 자율성 |
| `directiveMode` | `character_based` | 지시 대상 방식 |
| **`globalRules[]`** | **빈 배열** | 전역 규칙 주입구. UI 노출 위치 못 찾음 ★★☆☆☆ |
| `missions[]` | 빈 배열 | 미션 매니저가 자동 생성 |
| `missionManagerEnabled` / `Interval` | `false` / `7` | ON + Play 시 자동 생성 (패널 안내문) |
| `llmModel`/`controlModel`/`apiKey` | `""` | 비워 두면 SAM 기본값을 쓴다 |
| `timeScale` | 1 | tempo·speed 와 별개 |

#### (3) ★ 캐릭터 `aiConfig` — **비밀 역할 슬롯이 여기 있다**

```json
aiConfig: {
  enabled: true, model: "gpt-5.4-mini", qualityMode: "balanced",
  role: { title: "셰어하우스 주민(범인)",
          goal : "자신이 케이크를 먹은 사실을 들키지 않는다" },
  extraPrompt: "기억에 없는 것은 지어내지 않는다.",
  decisionMode: "local_fsm",
  thinkMinMs: 4000, thinkMaxMs: 12000,
  action: { text: "", weight: 0.5 },
  state: { currentSituation, userIntent, shortTermGoal, longTermGoal, nextActionHint }
}
```

⚠ **앞서 "역할은 Villager 뿐"이라고 적은 것은 오류였다.** 그건 `profiles.village.role`
(마을 직업)이고, **AI 역할은 `aiConfig.role`** 로 완전히 별개다. 마피아의 비밀 역할은
이 필드로 표현된다.

★ **`role.goal` 이 대화 화제(topic)로 쓰인다.** 실측: 꾸벅이의 goal `"아는 것이 없음을
설명한다"` 가 로그에 그대로 topic 으로 찍혔다. **목표를 쓰면 그게 그 캐릭터의 대화
방향이 된다** — Studio 에서 역할극을 만드는 핵심 손잡이다.

현재 설정 상태(2026-08-20): 살살이=범인 · 폴짝이=목격자 · 오물오물/새침이/꾸벅이=용의자 ·
**두리번이=빈칸(월드 미배치)**.

#### (4) 캐릭터 `memory` — 기억 구조

```json
memory: { summary: "어젯밤 11시~새벽 1시 사이의 기억",
          engram: "", summarizeThreshold: 6,
          recent: [ { id, at, type:"thought", source:"world_fsm", text,
                      mood, activity, partnerId, summarized } ],
          creatorMessages: [], relationships: {} }
```

- `recent` 는 최대 20개가 쌓이고 `summarizeThreshold: 6` 마다 요약되는 것으로 보인다 ★★★☆☆
- `type:"thought"` · `source:"world_fsm"` — 행동 판단이 남긴 혼잣말도 기억에 들어간다
- **알리바이를 심으려면 여기다 넣는다** (`summary` 또는 `recent`)

#### (5) `talkConfig` — **여전히 무시된다**

`talkConfig.systemPrompt` 에 361자가 들어 있으나, `llm` 모드 LLM 요청 필드는
`speaker/partner/topic/turn/deployMode/baseBehavior/worldTone/relationship/recentCount/
nearbyObjectCount` 뿐이다. **systemPrompt 가 실리지 않는다.** §4-19 의 결론은 유효하다.
캐릭터 성격은 `persona` 와 `aiConfig.role` 로 전달된다.

#### (6) `profiles.village.schedule[]` — 빈 배열

시간대별 행동을 넣는 자리로 보이나 **요소 스키마를 확인할 수 없다**(예시 데이터 없음) ★★☆☆☆.

#### (7) `persona.creatorResponseLevel` = 50

전원 기본값. 이름상 창조주 응답 성향이나 **효과 미검증**. 로그에서 `creator_response`
턴과 `llm` 턴이 섞여 나오는 것과 관련 있을 것으로 추정 ★★☆☆☆.

#### (8) `casts[]` — 배치 인스턴스

```json
{ characterId, instanceId, spawnTile:{col,row}, spawnX, spawnY,
  role: "npc", runtimeEnabled: true, overrides: {} }
```

`overrides` 는 빈 객체 — **배치별로 캐릭터 설정을 덮어쓰는 자리**로 보인다 ★★☆☆☆.

#### (9) SPUM Link / Frame

상단 버튼 2개. `publishBake` 에 `script: "embedded-world"`(선택지 `soonsoon-factory |
embedded-world | startup-demo`)가 있고 `publish: "SPUM Link / SoonSoon Frame"` 로 표기된다.
**대외 공개 동작이라 누르지 않았다** — 확인 필요 시 주영님 승인 후 진행.

#### (10) 시뮬레이션 탭 — 비활성(`disabled`)

버튼이 잠겨 있다. 활성 조건 불명 ★☆☆☆☆.

---

### 4-32. Studio 만으로 만드는 마피아 — 되는 것과 안 되는 것 ★★★★★

**되는 것** (전부 실측)

| 요소 | 방법 |
|---|---|
| 비밀 역할 | `aiConfig.role.title/goal` |
| 알리바이 | `memory.summary` / `memory.recent[]` |
| 자율 토론 | `conversationMode: "llm"` + 지시 한 줄 |
| 교차 검증·의심 전가 | 저절로 발생 (§4-29 로그) |
| 단계 진행 | 지시창에 단계 선언 → `currentTopic` 이 갈린다 |
| 지목 발언 | 지시창에 "각자 한 명 지목하라" |

**구조적으로 없는 것**

1. **은닉 정보가 없다.** Event Log 에 범인의 대사·속마음이 다 보인다
2. **집계·승패가 없다.** 표를 세는 주체가 없다 — 사람이 눈으로 센다
3. **플레이어가 캐릭터로 못 들어간다.** Play = 관전 + 지시

→ Studio 산출물은 **"규칙 있는 게임"이 아니라 "자율 추리극"** 이다. 그 자체로 데모 가치가
있으나, 승패가 필요한 게임은 SPUM **Engine** 층에서 만들어야 한다(우리 로컬 구현).

---

### 4-33. ★ Studio 판 「누가 내 케이크 먹었어?」 세팅 절차 (완료본) ★★★★★

> 2026-08-20. 팀 분업 — 팀원은 HTTP/SPUM Engine 게임, 주영님은 **Studio 판**.
> 아래는 실제로 적용해 동작을 확인한 설정이다.

**① 월드 설정 → 대화 시스템**

| 항목 | 값 |
|---|---|
| `mode` | **실시간 LLM** (`baked` 아님 — §4-27) |
| 대화 모델 / 제어 모델 | 보통(medium) |
| 미션 매니저 | **ON** (7틱 간격 자동 생성) |
| 월드 목표 | 어젯밤 냉장고의 케이크를 훔쳐 먹은 범인을 찾아낸다 |

**② 캐스트 6인 배치 + 역할** — 캐스트 배치 탭 → 캐릭터 선택 → **AI 탭**의 `역할`·`목표`

| 캐릭터 | 역할 | 목표(= 대화 화제로 쓰인다) |
|---|---|---|
| 살살이 | 주민(**범인**) | 자신이 케이크를 먹은 사실을 들키지 않는다 |
| 폴짝이 | 주민(**목격자**) | 자신이 목격한 것을 전한다 |
| 오물오물 | 주민(용의자) | 자신이 범인이 아님을 밝힌다 |
| 새침이 | 주민(용의자) | 결백을 밝히되 개인 비밀은 감춘다 |
| 꾸벅이 | 주민(용의자) | 아는 것이 없음을 설명한다 |
| 두리번이 | 주민(용의자) | 잠귀가 밝아 밤에 들은 소리를 근거로 수상한 사람을 짚는다 |

⚠ **캐릭터를 월드에 배치해야 AI 탭이 열린다.** 미배치 캐릭터는 역할을 못 넣는다.
배치는 `Characters` 헤더의 `+` → 「월드에 배치할 캐릭터 추가」에서 카드 클릭.

**③ 진행 대본** — 캔버스 아래 지시 입력창에 순서대로 넣는다. 넣은 문장이
`world.ai.currentTopic` 을 덮어쓰며 그게 대화 방향이 된다(실측).

```
[저녁] 잠들기 전 거실에 모여 오늘 하루 있었던 일과 오늘 밤 계획을 이야기하라.
       케이크 이야기는 아직 꺼내지 마라.

[밤]   각자 방으로 흩어져라. 마주친 사람이 있으면 누구였는지 기억하라.

[아침] 어젯밤 냉장고의 케이크가 사라졌다. 여섯 명 모두 거실에 모여 어젯밤 11시부터
       새벽 1시 사이 각자 어디서 무엇을 했는지 말하라. 남의 말에서 시각과 장소가
       어긋나는 곳을 짚고 되물어라.

[지목] 이제 한 사람씩 차례로, 범인으로 의심되는 사람의 이름을 하나만 대고
       그렇게 생각하는 이유를 한 문장으로 말하라.
```

**④ 확인 방법** — Event Log 를 `AI` 로 거르면 `Conversation start/turn/end (llm)` 이 보인다.
우측 `JSONL` 로 전체 로그를 받아 대사만 뽑을 수 있다(§4-29).

**실측 결과**: `sim on · actors 6` 로 6인 전원이 짝을 지어 대화하며, 시각 대조 추궁이 나온다.
> 꾸벅이 · 으응… 그럼 열한 시 반 발소리 뒤에도 누가 깨어 있었네, 거실엔 누구였는지 봤어…?

**⑤ 못 하는 것** (§4-32) — 은닉 정보·표 집계·승패·플레이어 참여. 지목 발언은 나오지만
**표는 사람이 센다.** 승패 판정이 필요하면 SPUM Engine 층(로컬 게임)을 쓴다.

⚠ `globalRules[]` 는 데이터에 존재하나 **UI 노출 위치를 끝내 못 찾았다** ★★☆☆☆.
전역 규칙은 대신 지시 입력창으로 넣는다.

### 4-34. 영상에서 본 기능들은 전부 우리 Studio 에도 있다 ★★★★★

순순랩스 「순순빌리지」 소개 영상의 기능을 우리 월드에서 하나씩 찾았다. **전부 있다.**

| 영상 속 이름 | 우리 Studio 위치 | 데이터 필드 |
|---|---|---|
| **엔그램 · #6요약** | 캐스트 배치 → **메모리 탭** | `memory.engram` · `summarizeThreshold: 6` |
| **미요약 N · 전체 M** | 메모리 탭 `RECENT 1/20` | `memory.recent[]` (최대 20) |
| **상호작용 (N명) ·「불쾌」** | 메모리 탭 `RELATIONSHIPS` | `memory.relationships` (UNIT/AFF/EVALUATION) |
| **행동 결정 기록** `moving/goto_char` | Event Log 의 `INTENT` 줄 | — |
| **SAI 마을 상황 요약** | 우측 **AI Assistant** 패널 | — |
| **캐릭터에 AI 모델 달기** | 캐스트 → AI 탭 `model` | **`aiConfig.model`** |

**★ 메모리 탭에 「수동 기억 추가」 입력란이 있다.** `RECENT` 아래 텍스트 칸 + 「추가」 버튼.
→ **알리바이를 직접 심을 수 있다.** 마피아를 만들 때 범인·목격자의 밤 기억을 여기에 넣는다.
(Studio 판 세팅의 마지막 조각 — §4-33 의 역할·목표와 짝이 된다.)

**★ 캐릭터마다 모델이 다르게 붙는다** (실측)

```
오물오물 · 살살이 → aiConfig.model = "gpt-5.4-mini"
나머지 4명        → ""  (월드 기본값 사용)
```

영상의 *"이 캐릭터한테 소넷 4.6을 달아놨다"* 가 이 기능이다. **중요한 캐릭터(범인)만 좋은
모델을 붙여 연기력을 올리고 나머지는 기본값으로 두는 운용이 가능하다.**
AI 탭의 `model` 선택지는 `월드 기본 / light / medium / expert` 이고, `quality` 는 별도로
`fast / balanced / …` 가 있다. 구체 모델 id(`gpt-5.4-mini`)가 어디서 들어왔는지는
확인 못 했다 ★★☆☆☆ — SAI 가 설정했거나 이전 UI 의 흔적일 수 있다.

⚠ **로그인이 30분 내외로 자주 만료된다.** 만료되면 상태바에 *"로그인 세션 만료 감지 ·
작업을 긴급 보관본으로 저장했습니다"* 가 뜨고 **서버 백업이 멈춘다**(로컬엔 남음).
계정 배지 → 「다시 로그인」 이면 복구되고 페이지가 새로고침된다. 긴 작업 중에는 중간에
한 번 확인할 것.

### 4-35. ⛔ SAI 의 "마을 상황 요약"은 우리 계정에서 아직 안 된다 ★★★★★

영상의 SAI(마을 상황 한눈에 파악·인물별 감정 표·"뚜룩이 의심한 이유 3가지")를 보고
우리 월드의 AI Assistant 에 같은 질문을 넣었다.

> 질문: "지금 마을에서 어떤 일이 벌어지고 있어? 인물별 감정과 지금까지의 흐름을 정리해줘."

**답변(원문 요지):**
> 지금은 World Editor의 월드 구성 화면을 보고 있어요. … 방금 요청한 "지금 마을에서 어떤
> 일이 벌어지고 있어?"는 **이 화면의 AI 직접 실행 기능이 붙으면 처리할 수 있게 연결할
> 예정입니다.** 현재 바로 실행 가능한 AI 작업은 **Cast Editor의 캐릭터 생성·수정·스탯·
> 애니메이션** 쪽입니다.

→ **World Editor 화면에서의 AI 직접 실행은 미구현이다.** 영상은 다른 제품 화면
(순순빌리지 전용 뷰)이거나 미출시 버전으로 보인다 ★★★☆☆.

**결과: "SAI 를 판정자로 세운다"는 계획은 지금은 불가능하다.** 지목 발언을 사람이 읽고
세는 수밖에 없다(§4-32 의 "집계·승패 없음"이 그대로 유효).

### 4-36. Props(장소 오브젝트) — 데이터 키가 아예 없다 ★★★★☆

`world.props` **키 자체가 없다**(`world` 최상위: sceneCharacterIds · unitPixelScale · ai ·
mapId · mapResourceId · bakeBuilder · casts · runtime · publishBake).
좌측 패널의 `Props 0` 옆 `+` 를 눌러도 추가 대화상자가 열리지 않는다.

영상의 순순빌리지에는 이름 붙은 오브젝트가 7개 있었다
(`대장간 4,7 · 여관 16,5 · 뚜룩의집 26,8 · 에라의집 32,8 · 상점 7,20 · 실바의집 26,20 · 우물 18,19`).
**우리 월드는 0개다.** 그래서 "부엌을 조사해라" 같은 **장소 지시가 해석될 근거가 없다.**

행동 의도(INTENT)의 목표 필드도 이렇다:

```json
intent: { type:"idle", motivation:"", priority:0,
          targetActorId:"", targetTile:null }
```

**사람(`targetActorId`)과 칸(`targetTile`)만 있고 "장소 이름"이 없다.**
→ 좌표성 지시("가운데로 모여라")는 먹고, 이름성 지시("부엌으로")는 근거가 없다 ★★★☆☆.

### 4-37. ⛔ "너희끼리 마피아 게임 해" 는 실패한다 — 사회자가 4명이 된다 ★★★★★

완전 자율(사회자까지 캐릭터가 정하게) 가능성을 **실제로 던져서** 확인했다.
케이크 월드를 **복제**해 사본에서 시험했다(원본 보호 — Worlds 목록의 「복제」).

> 지시: "지금부터 너희끼리 마피아 게임을 해라. 너희 중에서 사회자를 한 명 정하고,
> 사회자가 마피아 한 명을 몰래 정한 뒤 밤과 낮을 선언하며 진행해라. 나는 관여하지 않는다."

**결과 — 반응은 좋았다. 실행은 하나도 안 됐다.**

```
새침이   흥, 지시는 알겠어. 사회자는 내가 맡고 깔끔히 진행할게.
폴짝이   우와, 재밌겠다! 내가 사회자 후보도 모아볼게!
두리번이 좋아, 규칙만 정리되면 내가 진행도 맡을 수 있어.
살살이   좋지, 내가 판 깔아도 되고…
   ↓ 이후 짝 대화에서
두리번이 좋습니다, 그럼 사회자는 살살이님이 하시고…      (살살이 ↔ 두리번이 짝)
새침이   나 사회자 할게, 밤부터 갈 테니까…                (새침이 ↔ 폴짝이 짝)
살살이   저는 밤 선언할 테니 다들 11시 알리바이부터…
```

**원인이 그대로 보인다: 짝(1:1) 대화라 짝마다 따로 사회자를 정한다.** 합의가 형성될
채널이 없다. 4명이 동시에 사회자를 자처하고, 역할 배정도 밤 선언도 일어나지 않았으며,
얼마 안 가 원래 화제(케이크)로 돌아갔다.

→ **§4-32 의 "전체 공지 수단이 없다"가 게임 진행을 막는 결정적 이유임이 실증됐다.**
사회자는 반드시 **지시창(사람)** 이어야 한다. 캐릭터 사회자를 세워도 그가 전체에 공지할
방법이 없으므로 의미가 없다.

**부수 확인:** Worlds 목록의 「복제」로 월드를 통째로 복사할 수 있다(캐스트·역할·기억까지).
실험은 사본에서 하면 원본이 안전하다.

---

### 4-38. ★★ 「소넷 4.6」의 정체 = `expert` 등급 (소스 확정) ★★★★★

`/packages/spum-world/runtime/WorldLLMModels.js` 를 직접 읽어 확정했다.

```js
export const WORLD_LLM_MODEL_ALIASES = Object.freeze({
  'claude-haiku': 'light',   'claude-haiku-4-5': 'light',
  'gpt-5.4-nano': 'light',   'glm-4.7-flash': 'light',
  'gpt-5.4-mini': 'medium',                      // ← 우리가 쓰던 것
  'gemini-3.5-flash': 'medium',
  'claude-sonnet-4.6': 'expert',                 // ← 영상의 그 모델
  'claude-sonnet-4-6': 'expert',
  'claude-opus-4.6/4.7/4.8': 'expert',
  'gpt-5.4': 'expert', 'gpt-5.5': 'expert',
});
export const WORLD_LLM_QUALITY_MODELS = { fast:'light', balanced:'medium', rich:'expert' };
```

**영상의 "이 캐릭터한테 소넷 4.6을 달아놨다" = `expert` 를 골랐다는 뜻이다.**
그리고 `normalizeWorldLLMModel()` 이 **구체 모델 id 를 등급으로 정규화**한다. 그래서
SAI 의 `updateAIConfig` 로 `claude-sonnet-4.6` 을 넣어도 값이 남지 않는다(§4-34 의 미스터리 해소).

⚠ **그런데 우리 계정에서는 `expert` 를 고르면 LLM 호출이 통째로 실패한다**
(`LLM request failed or returned invalid JSON` · SAM 요청 수 0 증가). 모델 접근 권한은
있다(직접 호출 시 `claude-sonnet-4.6` 200 OK). **SPUM 게이트웨이 쪽 문제로 보이며
회사 문의 항목이다** ★★★☆☆.

### 4-39. 「상호작용(관계)」 평가가 안 생기는 이유 ★★★★★

`/packages/spum-world/core/RelationshipMemory.js` 기준. 갱신 함수가 셋인데 **역할이 다르다.**

| 함수 | 채우는 것 |
|---|---|
| `applyRelationshipDelta` | `trust`·`familiarity`·`tension` **숫자만** |
| `setRelationshipSummary` | `recentSummary` 만 (**`emotion` 안 건드림**) |
| **`setRelationshipMetrics`** | **`emotion`(≤10자)·`summary`(≤200자)**·affinity·tension |

화면의 **「불안」「신뢰」 라벨은 `emotion`** 이고, 이건 **`setRelationshipMetrics` 로만** 들어간다.
즉 **대화를 끝내는 것만으로는 안 채워지고, 평가용 LLM 호출이 따로 성공해야 한다.**

우리 월드가 계속 `0 · 아직 평가 없음` 인 이유 ★★★☆☆
1. 실행 시간이 짧아 평가 단계까지 못 감
2. **관계는 짝(partnerId)별로 저장** — 같은 상대와 반복 대화가 쌓여야 한다
3. 메모리 `reset` 을 눌러 계속 0으로 되돌렸다(아래 4-40)

관계 저장 구조: `memory.relationships[partnerId] = { trust, familiarity, tension, affinity,
emotion, summary, recentSummary, lastInteractionAt, importantConversationIds[≤24] }`

### 4-40. ⛔ 메모리 패널의 `reset` 은 **캐스트 전체를 되돌린다** ★★★★★

기억만 비우려고 6인 전원에게 Memory 옆 `reset` 을 눌렀다. 결과:

```
지워진 것  memory                                    (의도한 것)
+ 부작용   aiConfig.role.title/goal 이 옛 값으로 복귀
           두리번이 aiConfig.enabled = false
           캐스트 배치 6인 → 5인, 스폰 좌표가 맵 밖(33 · 맵은 32×32)
결과       actors 0 — 시뮬레이션이 빈 채로 돌아 아무 일도 안 일어남
```

→ **기억만 지우려면 `reset` 을 쓰지 말 것.** `SUMMARY` 를 덮어쓰고 `RECENT` 항목은
개별 `×` 로 지운다. 세팅을 다시 하는 편이 빠를 만큼 광범위하게 되돌아간다.

**복구법:** Worlds 목록의 「복제」로 원본을 다시 복사한다(원본은 건드리지 않는 게 이 때문).

### 4-41. 지시 프롬프트에 **같은 월드 캐스트 명단이 실리지 않는다** ★★★★★

마피아 1판(2026-08-20, 전문 = `docs/logs/mafia-round-2026-08-20.md`)에서 확정.

전체 브로드캐스트로 "가장 의심스러운 사람 한 명을 지목하라"고 했더니
**6명 전원이 존재하지 않는 이름을 댔다** — 토실이·민호·모카·냠냠이·부스럭이.
같은 월드에 배치된 나머지 5명의 이름을 아무도 모른다.

지시문에 `이 집에 사는 사람은 오물오물·새침이·살살이·꾸벅이·폴짝이·두리번이
여섯 명뿐이다` 를 직접 써 넣자 **6명 중 5명이 즉시 실제 이름으로 교정**했다.

→ 다인 추리·투표·지목을 하려면 **매 지시마다 명단을 손으로 붙여야 한다.**
   Studio 가 캐스트 목록을 알고 있는데도 프롬프트에 안 넣어 주는 것이라
   개선 요청 대상이다(`spum-feedback.md` E절).

### 4-42. `aiConfig.role.goal`(비밀 역할)이 **지시 응답에 반영되지 않는다** ★★★★★

오물오물에게 `role.goal = "나는 마피아다. …"` 를 저장해 두고
대상을 오물오물 단독으로 지정해 밤 밀담을 보냈다. **2회 모두 부인했다.**

```
1차 → 응? 난 그냥 케이크 먹던 주민인데, 그건 좀 이상한데.
2차 → 에이, 난 촌사람인데… 케이크 먹은 범인부터 찾자.
```

"네 역할 설정에도 그렇게 적혀 있다"고 명시해도 소용없었다.
**기본 페르소나(성격·말투)가 역할 목표를 이긴다.**

→ ⛔ **Studio 만으로 비밀 역할 게임(마피아·인랑)은 성립하지 않는다.**
   §4-37(자율 진행 실패)과 합치면, Studio 의 역할 슬롯은
   *공개된 직업 설정*까지는 되지만 *숨겨야 하는 정체*로는 못 쓴다.

### 4-43. 자율 짝대화는 **조우(이동) 이벤트가 트리거로 보인다** ★★★☆☆

같은 월드·같은 설정인데 이번 판은 9분 내내 `Conversation start` 0건이었다.
전원이 거실 한곳에 밀집한 채 INTENT 가 계속 `idle` 이었다.
§4-29 에서 짝대화가 났을 때는 캐릭터들이 흩어져 **이동 중**이었다.

→ 붙어 있는 것만으로는 대화가 시작되지 않는다. 데모에서 자율 대화를 보여줄
   생각이라면 **스폰을 흩뿌려 두고** 시작해야 한다. [추정 — 반증 실험 미실시]

### 4-44. 반대로, **확실히 되는 것** (같은 판에서 실측) ★★★★★

```
진행자 브로드캐스트   6/6 전원 응답, 각자 말투 유지, 실패 0건
맥락 유지             아침에 5/5 가 두리번이의 직전 발언을 정확히 인용
형식 지정             "이름을 문장 맨 앞에" → 6/6 이 집계 가능한 형태로 답함
역할 연기             마피아 본인이 남에게 표를 돌리는 물타기까지 나옴
비용                  6인 9분 = 165 SSAM  (분당 약 18 — 자율 대화 없을 때)
```

**결론:** Studio 는 *진행자가 있는* 다인 대화극에는 충분하다.
부족한 것은 자율성과 비밀 정보 관리 두 가지다.

### 4-45. 말풍선 타이핑은 **구현돼 있다** — 상수가 꺼놓고 있을 뿐 ★★★★★

`BubbleRenderer.update()` 에 타이핑 애니메이션이 원래 있다.

```js
const typingDuration = Math.min(0.4, this._text.length * 0.018);
```

**0.4초 상한** 때문에 41자면 초당 100자가 넘어 사실상 즉시 표시된다.
옵션도 직렬화 키도 없어서 설정으로 못 바꾼다.

라이브 Studio 에서 그 식만 `길이 / 11` 로 몽키패치하니 **3.7초**가 되고,
문장이 도중에 끊긴 말풍선이 실제로 관찰됐다(패치 전에는 원리상 불가능한 프레임).

```js
// 콘솔에서 즉석 확인용 — 새로고침하면 사라진다. 서버에는 아무것도 안 남는다.
const u = performance.getEntriesByType('resource').map(e=>e.name)
  .find(n=>/BubbleRenderer\.js/.test(n));
const { BubbleRenderer: B } = await import(u);
// B.prototype.update 를 같은 로직 + `길이/CPS` 로 교체한다 (본문 참조)
```

→ 데모에서 쓰려면 **매번 콘솔로 다시 넣어야 한다.** 저장되지 않으므로
   발표 자료에 "SPUM 에서 이렇게 된다"고 쓰면 안 된다. **"이렇게 될 수 있다"** 가 맞다.

### 4-46. `WorldSpeechDirector` — 대화 페이싱 체계는 이미 정교하다 ★★★★☆

`StudioSpumWorldRuntime.js` 의 `WORLD_PERFORMANCE_TIMING.speech`
(`gapMs 320` · `prepareMs 180` · `turnChainDelayMs 420` · `minMs 2200` · `maxMs 5600`).

- `splitLongSpeech()` — 긴 대사를 3줄 단위로 쪼개 순차 표시(카톡 연속 메시지처럼)
- `speechChunkDurationMs()` — 유지 시간 `1200 + 글자수 × 65ms`, 길이 비례
- `applyBubbleAvoidance()` — 말풍선끼리 겹치지 않게 자리를 옮긴다

`createWorldSpeechDirector({ timing })` 로 **주입 가능**하지만 Studio 는 고정 상수를 넘기고,
그 상수는 `Object.freeze` + export 안 됨 → 사용자 접근 경로 없음(라이브 확인).

> 우리 로컬 게임(`proto/src/typing.js`)은 이 설계를 참고하되 **직접 구현**했다.
> Studio 런타임을 쓰지 않기 때문이다(아키텍처 = 프로젝트 `CLAUDE.md` §3).

### 4-47. ⭐ `world.ai.globalRules[]` — 전 대화 공통 규칙 주입구(UI 없음) ★★★★☆

§4-31 에서 "UI 노출 위치 못 찾음 ★★☆☆☆" 로 남겼던 항목. **소스로 확정했다.**

```
core/WorldAIState.js         globalRules: _cleanList(ai.globalRules)   ← 정규화
runtime/WorldLLMConversation.js
   `globalRules: ${...join(' / ')}`   ← 「③ 월드 톤」 블록으로 프롬프트에 삽입
studio/pages/WorldPage.js    참조는 있으나 input/textarea 바인딩 없음 ← UI 부재 확정
```

**모든 LLM 대화 프롬프트에 들어간다.** 즉 §4-41(캐스트 명단이 프롬프트에 없다)의
정면 해법이 데이터 모델에는 이미 있었다.

**넣는 법(미검증):** `world.ai.globalRules = ["...", "..."]` 를 §4-1 절차
(로컬 → 이벤트 → `saveServerSnapshot`)로 써야 한다.
⚠ 그 경로는 §4-40 에서 캐스트를 되돌린 전례가 있으므로 **원본이 아닌 복제본에서** 시도할 것.

→ 다음에 Studio 로 다인 상호작용을 만든다면 **여기부터** 시도한다.

### 4-48. SPUM 「Frame」 = 그래픽 배너가 아니라 **월드 임베드 위젯** ★★★★★

World Editor 상단의 `⊞ Frame` 을 누르면 **SoonSoon Frame Builder** 가 열린다
(`/studio/world-frame-builder/`). 배너 이미지를 그리는 도구로 오해하기 쉬운데 아니다.

```
하는 일   퍼블리시된 월드를 <iframe> 으로 박아 넣는 코드를 만들어 준다
설정      SIZE(1200×600) · RATIO(2:1 Hero) · VIEWPORT(zoom·x·y) · RADIUS · 변형 여러 개
출력      FRAME LINK + <iframe …> 소스코드
전제      **publishId 가 있어야 한다** — 즉 월드를 대외 공개해야 쓸 수 있다
관련 코드 studio/pages/world/WorldPublishUrls.js
          createWorldFrameUrl        → /studio/world-frame/
          createWorldFrameBuilderUrl → /studio/world-frame-builder/
```

**쓸모:** 블로그·발표자료·랜딩페이지에 **살아 움직이는 월드**를 그대로 얹을 수 있다.
정적 스크린샷보다 훨씬 강하다.

⚠ **퍼블리시는 대외 공개**라 되돌리기 어렵다. 주영님 승인 없이 누르지 않는다.
   우리 타이틀 화면은 그래서 **자체 에셋**(맵 아트 + 그라데이션)으로 먼저 만들었다.
