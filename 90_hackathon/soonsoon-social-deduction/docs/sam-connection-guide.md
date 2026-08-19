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
