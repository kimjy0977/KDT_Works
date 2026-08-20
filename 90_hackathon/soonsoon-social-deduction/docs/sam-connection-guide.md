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
