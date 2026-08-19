# SPUM Studio + SAM 작업 가이드 (팀 공용)

> 팀 《순순히 따라와라》가 SPUM 으로 실제 작업하며 **대가를 치르고 얻은 것**만 모았습니다.
> SPUM Studio 는 공식 문서·튜토리얼이 사실상 없어서, 지금은 이게 팀이 가진 가장 정확한 자료입니다.
> **이 파일 하나로 완결됩니다.** 더 깊은 내용은 맨 아래 링크.
>
> 📌 **Claude 쓰시는 분:** 이 파일을 **프로젝트 폴더에 `CLAUDE.md` 라는 이름으로 저장**하면
> 그 폴더에서 연 세션에 아래 규칙이 자동 적용됩니다. §0 만 각자 채우세요.

> ## ⚠️ 먼저 — **이게 SPUM 의 전부가 아닙니다**
>
> 저희도 **마감에 필요한 것만 골라서** 써봤습니다. **안 만져본 기능이 훨씬 많습니다.**
> 여기 없다고 "SPUM 에 없는 기능"이라고 생각하지 마세요 — **저희가 아직 안 해본 것**일 가능성이 큽니다.
> 미확인 목록은 맨 아래 [§ 아직 아무도 안 해본 것](#아직-아무도-안-해본-것-) 에 정직하게 적어뒀습니다.
>
> 그리고 SPUM 은 **지금도 업데이트되는 제품**입니다(1인 개발). 저희가 확인한 시점은 **2026-08-19** 이고,
> 그 뒤에 동작이 바뀌었을 수 있습니다. **틀린 게 보이면 알려주세요.**

## 신뢰도 표기 — 모든 항목에 붙어 있습니다

| 표기 | 뜻 |
|---|---|
| ★★★★★ | 우리가 **직접 해보고** 확인함 |
| ★★★★☆ | **소스/문서 근거** — 코드는 읽었으나 실행까지는 안 해봄 |
| ★★★☆☆ | 추정 |
| ★☆☆☆☆ | 미확인 |

★★★★★ 가 아닌 항목은 **본인 환경에서 한 번 확인하고** 쓰세요.

---

# ⛔ 급하면 이것만 — 모르면 무조건 당하는 3가지

### 1. 서버에 직접 쓰면 작업이 날아갑니다 ★★★★★
SPUM 은 **브라우저 `localStorage` 가 원본**이고 서버는 그걸 받는 백업입니다.
서버에 직접 `PUT` 하면 다음 새로고침 때 브라우저 로컬이 서버를 덮어써서 **작업이 사라집니다.**
(팀원이 3번 당했습니다 — revision 69까지 올렸다가 통째로 소실)

### 2. 세션이 30분쯤에 만료됩니다 ★★★★★
`/api/me` 가 `{"user":null}` 이면 만료입니다.
우측 상단 배지 → **ACCOUNT → 「다시 로그인」** → 4초. **비밀번호 안 물어봅니다.**
> 우리는 이 증상을 **"권한 차단"으로 오진**해서 시간을 버렸습니다.

### 3. World 내장 AI 는 게임 규칙에 못 씁니다 ★★★★☆
`talkConfig.systemPrompt` 를 **무시**하고, 캐릭터 메모리를 사실 근거로 **쓰지 않으며**, 없는 내용을 **지어냅니다.**
대화 모드가 Local FSM 으로 고정돼 시스템 프롬프트 입력란 자체가 없습니다.
→ **대화 로직은 SAM 직접 호출(`/v1/generate`)로** 만드세요.

---

# 0. 이 프로젝트 (각자 채우기)

- **무엇을 만드나:**
- **마감:**
- **과제 성공 기준:** ← ⛔ **과제정의서 원본을 먼저 읽고 여기 옮겨 적으세요.**

> ⚠️ 우리가 실제로 낸 실수: 팀 자체 기획서를 요건으로 착각해 **채점표에 없는 기능을 최우선**으로 잡았습니다.
> **자체 기획 ≠ 과제 요건.** 우선순위는 항상 과제정의서 기준으로.

---

# 1. 🔒 보안 — 손대기 전에

- **SAM 키를 어떤 파일에도 쓰지 않는다.** 전체든 **접두사든**. `.env`(gitignore) 또는 환경변수만. ★★★★★
  → 우리는 문서에 적은 **키 앞 8자리** 때문에 git 히스토리를 재작성해야 했습니다.
- **`claude mcp add --scope project` 금지** — 레포 `.mcp.json` 에 키가 박혀 커밋됩니다. `local`/`user` 사용. ★★★★☆
- **`claude mcp get <이름>` 은 키를 평문 출력합니다** — 화면 공유 중 주의. ★★★★☆
- **회사 제공 자료(과제정의서·회사소개서)는 커밋하지 않는다.** gitignore 폴더(`_local/` 등)로. ★★★★★
- 커밋 전 1초 자문: **"이거 공개 레포에 올라가도 되나?"**
- 커밋 전 점검: `grep -rn "sam-[0-9a-f]\{8\}" .`

---

# 2. 태도

- **확인 안 한 건 "확인 안 됨"이라고 말한다.** 7/7이면 7/7, 2/5면 2/5. 실패를 성공처럼 보고하지 않는다.
- 위 **신뢰도 5단계**로 표기한다.
- **산출물은 만든 즉시 실제로 적용해서 눈으로 확인한다.** (맵을 만들어놓고 월드에 안 붙인 전례)
- **결과물에서 멀어지면 즉시 중단하고 보고한다.** (도구 연결에 매달렸는데 결국 무관했던 전례)

---

# 3. 🔥 SPUM Studio 함정

## 3-1. 쓰기 방향은 반드시 `로컬 → 서버` ★★★★★

```js
window.spumStudioData.export();                      // ① 백업 먼저 (항상)
localStorage.setItem(KEY, JSON.stringify(data));     // ② 로컬에 쓰기
window.dispatchEvent(new CustomEvent("spum:studio-storage-write", {detail:{key:KEY}}));
await window.spumStudioData.saveServerSnapshot("manual");  // ③ 서버로
// ④ 페이지 새로고침해야 앱이 읽는다
```

**localStorage 키** — `Object.keys(localStorage)` 로 본인 환경에서 먼저 확인하세요.

| 키 | 내용 | 신뢰도 |
|---|---|---|
| `sv_studio_characters_v1` | 캐릭터(캐스트) | ★★★★★ |
| `sv_studio_maps_v1` | 맵 | ★★★★★ |
| `sv_studio_smo_v1` | 오브젝트(타일 테마) | ★★★★★ |
| `sv_studio_draft_v1` | 월드 | ★★★★☆ *(문서 근거 — 우리 덤프에선 안 보였음)* |
| `spum-map-theme-source-state:{SMO_ID}` | 테마 원본 — **최대 2.8MB, 통째로 읽지 말 것** | ★★★★★ |

`window.spumStudioData` 에 있는 것:
`export` · `import(file)` · `saveServerSnapshot` · `listEmergencyBackups` · `restoreEmergency` · `clearLocal` · `hasLocalData`

## 3-2. 캐스트 "배치"만은 코드로 하지 마세요 ★★★★☆ *(팀 경험 · 우리는 재현 안 함)*
`world.casts[]` 를 코드로 만들면 앱이 *"없는/중복 캐릭터 배치 N개를 정리했습니다"* 로 **전부 삭제**합니다.
→ World Editor 좌측 `Characters` 의 **＋ → "배치"** 버튼으로. 한 명씩 누르고 확인(연속 클릭은 리렌더로 씹힘).
※ 캐릭터 **생성·수정·삭제·외형**, **맵 레이어**, **월드 mapId 교체**는 코드로 잘 됩니다. ★★★★★

## 3-3. Cast Export(스프라이트 시트)를 신뢰하지 마세요 ★★★★☆
Generate 가 비동기라 **직전 캐릭터의 시트가 다운로드됩니다.** 미리보기로 눈 확인해도 어긋납니다.
→ 받은 뒤 반드시 JSON 의 `characterName` 으로 검증.
> 결과: 우리는 캐릭터 5명 중 **고유 스프라이트가 2개뿐**이었습니다(뒤늦게 발견). ★★★★★

## 3-4. 썸네일은 코드로 외형을 바꿔도 갱신 안 됩니다 ★★★★☆
`localStorage` 로 `appearance` 를 바꿔도 `sv_studio_thumb_*` 는 예전 이미지 그대로.
목록·추출물이 쌍둥이로 보이면 이것 때문. → Cast Editor 에서 UI로 한 번 편집·저장하면 재생성됩니다.

## 3-5. 타일셋 셀 크기는 이미지에서 계산하세요 ★★★★★
`grid: "16x16"` 은 셀이 16px 이라는 뜻이 **아니라 "16칸"**이라는 뜻입니다.
**셀 = 이미지폭 ÷ 칸수.** 우리 경우 192px ÷ 16 = **12px** 이었고, 64로 착각해 한참 헤맸습니다.

## 3-6. 맵은 손으로 안 찍어도 됩니다 — 코드로 통째 교체됩니다 ★★★★★

```
타일 ID   = tileIdBase + (row × columns) + col     // row·col 은 0부터
레이어    = [{ name, type:"back|front|walkable|obstacle", label, data:[width*height] }]
칸 인덱스 = y * width + x
```

1200칸 × 4레이어를 그대로 붙여넣으면 컨텍스트가 탑니다 → **런렝스 압축**해 넣고 페이지에서 푸세요.

## 3-7. Map Editor 에서 타일이 안 보이면 ★★★★★
오른쪽 `MAP STRUCTURE → Layers` 의 **NAV 체크박스(장애물·워커블)를 끄세요.**
초록/빨강 오버레이가 타일을 가리고 있는 것입니다.

## 3-8. Object 와 Map 을 헷갈리지 마세요 ★★★★★
**Object Editor** = 바닥·벽·소품의 **그림(타일 재질)** 을 만드는 곳.
**Map Editor** = 그 타일로 **배치(레이아웃)** 하는 곳.
제작 순서는 **Object → Map → Cast → World** 입니다.

---

# 4. 🔥 브라우저 자동화 함정

- **4-1.** 앱 내장 브라우저 말고 **실제 크롬(`claude-in-chrome`)** 을 쓰세요. 내장 브라우저는 SPUM 로그인 세션이 없어 아무것도 못 합니다. 증상이 **"권한 차단"처럼 보여도 원인은 이것**입니다. ★★★★★
- **4-2.** `javascript_tool` 반환값이 `[BLOCKED]` 로 막힐 때가 있습니다(민감·대용량). → **요약해서 반환**하거나 `document.title` 에 써서 탭 제목으로 읽는 우회가 통합니다. ★★★★★
- **4-3.** 네트워크/DOM 덤프로 **base64 를 뽑지 마세요.** 컨텍스트가 순식간에 고갈됩니다. 개수·상태코드만. ★★★★☆
- **4-4.** Object Tile Editor 는 **iframe**(`/studio/pixeldeidtor/index.html`)입니다. 부모 document 쿼리로는 안 잡힙니다. → `document.querySelector('iframe[src*="pixeldeidtor"]').contentDocument` ★★★★☆
- **4-5.** 커스텀 드롭다운은 화면 클릭으로 안 열립니다. 내부 `<select>` 를 찾아 `value` 설정 후 `input`/`change` dispatch. ★★★★☆
- **4-6.** Object Editor 에서 **프리셋을 바꾸면 프롬프트가 리셋**됩니다. **프리셋 먼저 → 프롬프트 나중.** ★★★★☆

---

# 5. 🔥 환경 함정

- **5-1. 한글 파일명은 유니코드 정규화(NFC/NFD)가 어긋납니다.** bash 로 보이는 이름이 PowerShell `-LiteralPath` 로 **안 열립니다.** → `Get-ChildItem` 으로 **실제 파일 객체**를 얻어 다루고, 이름 문자열로 조립하지 마세요. **폴더·파일명은 영문 slug 권장.** ★★★★★
- **5-2. 정적 서버의 MIME 을 확인하세요.** `.js` 를 `text/plain` 으로 주면 브라우저가 **ES 모듈 import 를 거부**합니다. SPUM Engine 붙이기 전에 필수. ★★★★★
- **5-3. 비활성 탭에서는 `requestAnimationFrame` 이 멈춥니다.** FPS 0 이 떠도 코드 문제가 아닙니다. 게임 루프 검증은 `engine.pause()` → `engine.step(1/60)` 반복으로 **결정론적으로**. ★★★★★
- **5-4. 제공 문서는 실제로 받을 수 없습니다.** 과제정의서가 준다던 `AGENTS.md`·`README.md` 가 **404** 입니다. → **소스가 곧 문서**(압축 안 됨 + 한국어 주석). 회사에 요청할 항목. ★★★★★
- **5-5. "SPUM"이 두 개입니다.** 검색하면 대부분 **Unity 에셋 SPUM**이 나오는데 **우리와 무관**합니다. `soonsoon.co` 도메인은 사라져서(NXDOMAIN) 검색 링크 대부분 무효. ★★★★☆
  → 볼 것: 공개 데모 `spum.soonsoon.ai/studio/sai-character-world-demo/` · 소스 `spum.soonsoon.ai/packages/`

---

# 6. SPUM Engine — 있는 것 / 없는 것

**있습니다 — 직접 짜지 마세요** *(존재는 전부 소스 확인. "실행" = 우리가 돌려봤는지)*

| 기능 | 쓰는 법 | 실행 |
|---|---|---|
| 타일맵 | `TileSet` + `TileMapSystem` + `TileMapRenderer` | ★★★★★ |
| 입력·카메라 | `InputManager` · `Camera` | ★★★★★ |
| **AI 이동(A*)** | `PathfindingManager.buildFromTileMap(tileMap, opts)` → `NavAgent.setDestination(x, y)` | ★★★★☆ |
| **말풍선** | `BubbleRenderer` — speech / thought / shout / whisper | ★★★★☆ |
| 애니메이션 | `Animator` (스프라이트 시트 필요) | ★★★★☆ |
| 저장·복원 | `Scene.toJSON()` / `fromJSON()` | ★★★★☆ |
| 관계·대화 구조 | `spum-world`: `RelationshipMemory` · `ConversationModel` · `WorldSpeechDirector` | ★★★★☆ |

### ⚠️ `BubbleRenderer` 는 패키지 루트에서 import 안 됩니다 ★★★★★

```js
import { BubbleRenderer } from ".../spum-engine/lib/domain/ui/index.js";   // ✅
import { BubbleRenderer } from ".../spum-engine/index.js";                 // ❌ 루트에 없음
```

### ⚠️ 길찾기는 "별도 obstacle 배열"이 아니라 타일맵 레이어를 읽습니다 ★★★★★

`buildFromTileMap(tileMap, { collisionLayer: 0, emptyIsWalkable: true, nonEmptyIsBlocked: false })`
→ 충돌 정보를 **TileMap 레이어로 올린 뒤** 그 인덱스를 `collisionLayer` 로 지정하세요.
0/1 값을 쓸 거면 **`nonEmptyIsBlocked: true`** 로 줘야 `1` 이 벽으로 잡힙니다.

### 없습니다 — 직접 만들어야 합니다 ★★★★★ *(소스 전수 검색)*
- **시야 제한 / 안개(fog of war)** · **조명**
- **추적 카메라** — `CameraController` 는 **마우스 줌/팬 전용**입니다.

### 그 외 주의
- `TileSet(img, cellW, cellH, …)` 는 시트에서 **잘라올** 크기 / `TileMapSystem({ tileWidth, tileHeight })` 는 화면에 **그릴** 크기. **별개입니다.** ★★★★★
- `Camera.isMain = true` 를 켜야 엔진이 메인 카메라로 인식합니다. ★★★★★
- 렌더 순서 = `sortingLayer` → `transform.y` → `renderOrder`. ★★★★★

---

# 7. git

- **push 전 `git pull`.** 같은 clone 을 여러 세션이 공유하면 **동시 git 작업 금지.** ★★★★★
- **`git add -A` 를 조심하세요.** 다른 세션이 작업 중인 미완성 파일이 딸려 들어갑니다. → **경로를 명시**해서 add. (우리가 실제로 당했습니다) ★★★★★
- **비가역 작업**(force push · history 재작성 · 삭제 · 개명)은 반드시 사람 확인 후. ★★★★★

---

# 더 자세한 자료 (전문)

| 자료 | 내용 |
|---|---|
| [화면 가이드 (HTML)](https://github.com/kimjy0977/KDT_Works/blob/main/90_hackathon/soonsoon-social-deduction/pitch/spum-guide.html) | 에디터 화면 캡처에 ①②③ 번호를 얹은 매뉴얼. **처음 여시는 분은 여기부터** (다운로드 후 브라우저로 여세요) |
| [SPUM/SAM 연결 정본](https://github.com/kimjy0977/KDT_Works/blob/main/90_hackathon/soonsoon-social-deduction/docs/sam-connection-guide.md) | 연결 3종 구분 · 데이터 스키마 · **맵을 코드로 쓰는 절차(§4-5)** · 스프라이트 시트 스키마(§4-6) |
| [엔진 기능 감사](https://github.com/kimjy0977/KDT_Works/blob/main/90_hackathon/soonsoon-social-deduction/docs/engine-capability-audit.md) | 기획한 기능이 엔진으로 되는지 소스로 확인한 표 |
| [함정 원본](https://github.com/kimjy0977/KDT_Works/blob/main/90_hackathon/soonsoon-social-deduction/docs/work-rules.md) | 이 문서의 출처 |
| [전체 폴더](https://github.com/kimjy0977/KDT_Works/tree/main/90_hackathon/soonsoon-social-deduction/share) | 공유 자료 모음 |

---

# 아직 아무도 안 해본 것 ★☆☆☆☆

**정직하게 남깁니다. 아래는 "없는 기능"이 아니라 "저희가 확인 못 한 기능"입니다.**
해보신 분 계시면 공유해 주세요 — 이 문서에 반영하겠습니다.

### SPUM Studio 기능
- **SPUM Link 배포** — 결과물이 어떤 형태인지 (버튼만 봤습니다)
- **SPUM Frame** — 임베드 방식
- **미션 / 스토리(Reverse Story Bake)** — scene·node·thread 자동 생성, 말풍선 재생
- **시뮬레이션(자율행동)** — Event Log·INTENT·비용 구조
- **Object Editor** — Slice(생성 이미지 자동 격자 분할) · 픽셀 편집 · 프리셋 전반
- **Cast Editor** — Animation 탭 실사용 · Export 형식별 차이(PNG / PNG+JSON / GIF) · Manage 탭
- **Rule Tiles** — 맵 데이터에 `ruleTiles` 필드가 있는데 안 써봤습니다
- **맵의 `objects[]` · `spawnPoints[]`** — 프롭·스폰 지점 배치
- **다중 맵 / 월드 전환**

### SPUM Engine (소스에 있는 건 봤지만 안 돌려봤습니다)
- **파티클·이펙트** (`ParticleSystem` · `EffectManager`)
- **투사체** (`ProjectileSystem` · 프리셋들)
- **스탯 시스템** (`StatRegistry` · `StatContainer`)
- **스크립트 시스템** (`ComponentRegistry` · `ScriptSandbox` · `ScriptManager`)
- **`Prefab`** (프리팹 인스턴스화)
- **`Animator` 실사용** — 스프라이트 시트로 실제 재생까지

### 패키지 전체
- **`spum-character` · `spum-map`** 패키지 — 저희는 `spum-engine` 과 `spum-world` 만 봤습니다
- `spum-world` 의 대부분 모듈도 **존재만 확인**했지 써보진 않았습니다

### SAM
- 모델 종류별 차이 · 옵션(temperature·max_tokens 외) 전반
- 스트리밍(`stream: true`) 동작
- 요금 정책 (저희는 소진 속도만 측정: **대화 턴당 약 1.7 SSAM**)

---

**틀린 내용이나 새로 알아내신 게 있으면 알려주세요. 반영하겠습니다.**
*작성: 팀 《순순히 따라와라》 · 확인 시점 2026-08-19*
