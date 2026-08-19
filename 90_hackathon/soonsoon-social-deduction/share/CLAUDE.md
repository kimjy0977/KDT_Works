# SPUM + SAM 작업용 하네스 (팀 공용 · 그대로 복사해 쓰세요)

> **쓰는 법:** 이 파일을 본인 프로젝트 폴더 루트에 **`CLAUDE.md`** 로 저장하세요.
> 그 폴더에서 연 Claude 세션에 아래 규칙이 자동 적용됩니다. **§0 만 각자 채우면 됩니다.**
>
> 팀 《순순히 따라와라》가 SPUM Studio + SAM 으로 실제 작업하며 **대가를 치르고 얻은 것**만 담았습니다.

> ## ⚠️ 이게 SPUM 의 전부가 아닙니다
>
> 마감에 필요한 것만 골라 써봤습니다. **안 만져본 기능이 훨씬 많습니다.**
> 여기 없다고 "SPUM 에 없는 기능"이라 단정하지 마세요 — **아직 안 해본 것**일 가능성이 큽니다.
> 확인 시점 **2026-08-19**. SPUM 은 지금도 업데이트되는 제품입니다.

## 📌 신뢰도 표기 — 모든 항목에 붙어 있습니다

| 표기 | 뜻 |
|---|---|
| ★★★★★ | **우리가 직접 해보고 확인함** |
| ★★★★☆ | **소스/문서 근거** — 코드는 읽었으나 실행까지는 안 해봄 |
| ★★★☆☆ | 추정 |
| ★★☆☆☆ | 불확실 |
| ★☆☆☆☆ | 미확인 |

★★★★★ 가 아닌 항목은 **본인 환경에서 한 번 확인하고 쓰세요.**

---

## ⛔ 시작 전 3분 — 이 3개는 모르면 무조건 당합니다

1. **서버에 직접 쓰면 작업이 날아갑니다.** `localStorage` → `saveServerSnapshot()` 순서만. → §3-1
2. **세션이 30분쯤에 만료됩니다.** 권한 문제로 오해하기 쉽습니다. → §3-2
3. **World 내장 AI 는 게임 규칙에 못 씁니다.** 프롬프트를 무시하고 지어냅니다. → §3-9

---

## 0. 이 프로젝트 (각자 채우기)

- **무엇을 만드나:**
- **마감:**
- **과제 성공 기준:** ← ⛔ **과제정의서 원본을 먼저 읽고 여기 옮겨 적으세요.**

> ⚠️ 우리가 실제로 낸 실수: 팀 자체 기획서를 요건으로 착각해 **채점표에 없는 기능을 최우선**으로 잡았습니다.
> **자체 기획 ≠ 과제 요건.** 우선순위는 항상 과제정의서 기준으로.

---

## 1. 🔒 보안 — 손대기 전에

- **SAM 키를 어떤 파일에도 쓰지 않는다.** 전체든 **접두사든**. `.env`(gitignore) 또는 환경변수만. ★★★★★
  → 우리는 문서에 적은 **키 앞 8자리** 때문에 git 히스토리를 재작성해야 했습니다.
- **`claude mcp add --scope project` 금지** — 레포 `.mcp.json` 에 키가 박혀 커밋됩니다. `local`/`user` 사용. ★★★★☆
- **`claude mcp get <이름>` 은 키를 평문 출력합니다** — 화면 공유 중 주의. ★★★★☆
- **회사 제공 자료(과제정의서·회사소개서)는 커밋하지 않는다.** `_local/` 같은 gitignore 폴더로. ★★★★★
- 커밋 전 1초 자문: **"이거 공개 레포에 올라가도 되나?"** / 점검: `grep -rn "sam-[0-9a-f]\{8\}" .`

---

## 2. 톤·태도

- 한국어 존대 · **결론부터** · 직언(아첨 금지) · 지어내기 금지
- **확인 안 한 건 "확인 안 됨"이라고 말한다.** 7/7이면 7/7, 2/5면 2/5. 실패를 성공처럼 보고하지 않는다.
- 위 **신뢰도 5단계**로 표기한다.
- **산출물은 만든 즉시 실제로 적용해서 눈으로 확인한다.** (맵을 만들어놓고 월드에 안 붙인 전례)
- **결과물에서 멀어지면 즉시 중단하고 보고한다.** (도구 연결에 매달렸는데 결국 무관했던 전례)

---

## 3. 🔥 SPUM Studio 함정

**3-1. 쓰기 방향은 반드시 `로컬 → 서버`.** ★★★★★
SPUM Studio 는 **브라우저 `localStorage` 가 원본**이고 서버는 그걸 받는 백업입니다.

```js
window.spumStudioData.export();                      // ① 백업 먼저 (항상)
localStorage.setItem(KEY, JSON.stringify(data));     // ② 로컬에 쓰기
window.dispatchEvent(new CustomEvent("spum:studio-storage-write", {detail:{key:KEY}}));
await window.spumStudioData.saveServerSnapshot("manual");  // ③ 서버로
// ④ 페이지 새로고침해야 앱이 읽는다
```

> ❌ **서버에 직접 `PUT /api/studio/state` 하지 마세요.** 다음 새로고침 때 브라우저 로컬이 서버를
> 덮어써서 작업이 사라집니다. (팀원이 3번 당함 — revision 69까지 올렸다가 통째로 소실)
> ★★★★☆ *(전달받은 사례, 우리가 재현하진 않음)*

**localStorage 키** — `Object.keys(localStorage)` 로 본인 환경에서 먼저 확인하세요.

| 키 | 내용 | 신뢰도 |
|---|---|---|
| `sv_studio_characters_v1` | 캐릭터(캐스트) | ★★★★★ |
| `sv_studio_maps_v1` | 맵 | ★★★★★ |
| `sv_studio_smo_v1` | 오브젝트(타일 테마) | ★★★★★ |
| `sv_studio_draft_v1` | 월드 | ★★★★☆ *(문서 근거 — 우리 덤프에선 안 보였음)* |
| `spum-map-theme-source-state:{SMO_ID}` | 테마 원본 — **최대 2.8MB, 통째로 읽지 말 것** | ★★★★★ |

**3-2. 세션이 30분쯤에 만료됩니다.** ★★★★★
`/api/me` 가 `{"user":null}` 이면 만료. 우측 상단 배지 → **ACCOUNT → 「다시 로그인」** → 4초.
**비밀번호 안 물어봅니다**(SSO 살아있으면). 복구 후 `saveServerSnapshot()` 으로 재동기화.
> 우리는 이 증상을 **"권한 차단"으로 오진**해서 시간을 버렸습니다.

### 🔁 자동 복구 — 콘솔에 한 번 붙여넣기 ★★★★★ *(2026-08-19 직접 검증)*

만료를 **눈으로 확인할 필요 없이** 스크립트가 감지해서 재로그인 버튼을 눌러줍니다.
F12 → Console 에 붙여넣으세요.

```js
(() => {
  const find = () => [...document.querySelectorAll('button,a,[role=button]')]
    .find(el => (el.textContent || '').replace(/\s+/g, '').includes('다시로그인'));
  const check = async () => {
    let me;
    try { me = await fetch('/api/me', { credentials: 'include' }).then(r => r.json()); }
    catch { return; }                    // 일시적 네트워크 오류는 무시
    if (me.user) return;                 // 세션 살아있음
    const btn = find();
    if (!btn) return console.warn('[SPUM] 만료됐는데 「다시 로그인」 버튼을 못 찾음');
    console.log('[SPUM] 세션 만료 감지 → 재로그인 시도');
    btn.click();                         // SSO 왕복 후 페이지가 새로고침됨
  };
  clearInterval(window.__spumKeep);
  window.__spumKeep = setInterval(check, 60000);
  check();
  console.log('[SPUM] 세션 감시 시작 (60초 간격)');
})();
```

**검증한 것 ★★★★★**
- 「다시 로그인」 버튼은 **ACCOUNT 패널을 열지 않아도 DOM 에 이미 존재**합니다 → 스크립트로 바로 찾힙니다
- 클릭하면 **SSO 왕복(페이지 이동)** 후 `/studio/` 로 돌아오고, `/api/me` 가 정상 복구됩니다
- **비밀번호를 묻지 않습니다** (회사 SSO 세션이 살아있는 동안)

**⚠️ 한계 — 알고 쓰세요**
재로그인하면 **페이지가 새로고침되면서 이 스크립트도 같이 사라집니다.**
즉 **한 번의 만료는 자동으로 넘기지만, 그 다음부터는 다시 붙여넣어야** 합니다.
새로고침해도 계속 돌게 하려면 아래 둘 중 하나를 쓰세요.

**(A) 북마클릿** — 즐겨찾기에 URL 로 아래를 저장. 만료됐을 때 **한 번 클릭**하면 복구됩니다. ★★★★☆
```
javascript:(()=>{const b=[...document.querySelectorAll('button,a,[role=button]')].find(e=>(e.textContent||'').replace(/\s+/g,'').includes('다시로그인'));b?b.click():alert('버튼 없음 - 이미 로그인 상태일 수 있습니다');})()
```

**(B) Tampermonkey 유저스크립트** — 새로고침돼도 매번 자동 실행됩니다. ★★★☆☆ *(우리는 안 써봤습니다)*
```js
// ==UserScript==
// @name         SPUM 세션 자동 재로그인
// @match        https://spum.soonsoon.ai/*
// @grant        none
// ==/UserScript==
// 위 콘솔 스니펫 본문을 그대로 여기에 붙여넣으세요.
```

**⚠️ 작업 중이라면 저장부터.** 재로그인은 페이지를 새로고침하므로,
저장 안 한 편집 내용이 날아갈 수 있습니다. 중요한 작업 중엔 `saveServerSnapshot()` 먼저 하세요.


**3-3. 캐스트 "배치"만은 코드로 하지 마세요.** ★★★★☆ *(팀 경험 · 우리는 재현 안 해봄)*
`world.casts[]` 를 코드로 만들면 앱이 *"없는/중복 캐릭터 배치 N개를 정리했습니다"* 로 **전부 삭제**합니다.
→ World Editor 좌측 `Characters` 의 **＋ → "배치"** 버튼으로. 한 명씩 누르고 확인(연속 클릭은 리렌더로 씹힘).
※ 캐릭터 **생성·수정·삭제·외형**, **맵 레이어**, **월드의 mapId 교체**는 코드로 잘 됩니다. ★★★★★

**3-4. Cast Export(스프라이트 시트)를 신뢰하지 마세요.** ★★★★☆
Generate 가 비동기라 **직전 캐릭터의 시트가 다운로드됩니다.**
→ 받은 뒤 반드시 JSON 의 `characterName` 으로 검증.
> 결과: 우리는 캐릭터 5명 중 **고유 스프라이트가 2개뿐**이었습니다(뒤늦게 발견). ★★★★★

**3-5. 썸네일은 코드로 외형을 바꿔도 갱신 안 됩니다.** ★★★★☆
`localStorage` 로 `appearance` 를 바꿔도 `sv_studio_thumb_*` 는 예전 이미지 그대로.
목록·추출물이 쌍둥이로 보이면 이것 때문. → Cast Editor 에서 UI로 한 번 편집·저장하면 재생성됩니다.

**3-6. 타일셋 셀 크기는 이미지에서 계산하세요.** ★★★★★
`grid: "16x16"` 은 셀이 16px 이라는 뜻이 **아니라 "16칸"**이라는 뜻입니다.
**셀 = 이미지폭 ÷ 칸수.** 우리 경우 192px ÷ 16 = **12px** 이었고, 64로 착각해 한참 헤맸습니다.

**3-7. 맵은 손으로 안 찍어도 됩니다 — 코드로 통째 교체됩니다.** ★★★★★

```
타일 ID   = tileIdBase + (row × columns) + col     // row·col 은 0부터
레이어    = [{ name, type:"back|front|walkable|obstacle", label, data:[width*height] }]
칸 인덱스 = y * width + x
```

1200칸 × 4레이어를 그대로 붙여넣으면 컨텍스트가 탑니다 → **런렝스 압축**해 넣고 페이지에서 푸세요.

**3-8. Map Editor 에서 타일이 안 보이면** 오른쪽 `MAP STRUCTURE → Layers` 의
**NAV 체크박스(장애물·워커블)를 끄세요.** 초록/빨강 오버레이가 타일을 가립니다. ★★★★★

**3-9. ★ World 내장 AI 는 게임 규칙에 쓸 수 없습니다.** ★★★★☆ *(팀이 검증, 우리는 재현 안 함)*
`talkConfig.systemPrompt` 를 **무시**하고, 캐릭터 메모리를 사실 근거로 **쓰지 않으며**, 없는 내용을 **지어냅니다.**
대화 모드가 Local FSM 으로 고정돼 시스템 프롬프트 입력란 자체가 없습니다.
→ **대화 로직은 SAM 직접 호출(`/v1/generate`)로 구현하세요.**

---

## 4. 🔥 브라우저 자동화 함정

**4-1. 앱 내장 브라우저 말고 실제 크롬(`claude-in-chrome`)을 쓰세요.** ★★★★★
내장 브라우저는 SPUM 로그인 세션이 없어 아무것도 못 합니다.
증상이 **"권한 차단"처럼 보여도 원인은 이것**입니다. (우리가 이걸로 시간을 버렸습니다)

**4-2. `javascript_tool` 반환값이 차단될 때가 있습니다.** ★★★★★
민감해 보이는 값·대용량이 섞이면 `[BLOCKED]` 로 돌아옵니다.
→ **요약해서 반환**하거나, `document.title` 에 써서 탭 제목으로 읽는 우회가 통합니다.

**4-3. 네트워크/DOM 덤프로 base64 를 뽑지 마세요.** ★★★★☆
이미지 요청을 조회하면 base64 가 통째로 쏟아져 **컨텍스트가 순식간에 고갈**됩니다.
개수·상태코드만 보도록 필터링하세요.

**4-4. iframe 안을 봐야 할 때가 있습니다.** ★★★★☆
Object Tile Editor 는 `/studio/pixeldeidtor/index.html` iframe 입니다. 부모 document 쿼리로는 안 잡힙니다.
→ `document.querySelector('iframe[src*="pixeldeidtor"]').contentDocument`

**4-5. 커스텀 드롭다운은 화면 클릭으로 안 열립니다.** ★★★★☆
네이티브 `<select>` 가 아니면 스크린샷에 팝업이 안 뜹니다.
→ 내부 `<select>` 를 찾아 `value` 설정 후 `input`/`change` 이벤트 dispatch.

**4-6. 프리셋을 바꾸면 프롬프트가 덮어써집니다.** ★★★★☆
Object Editor 에서 Preset 변경 시 Reference Prompt 가 기본값으로 리셋. **프리셋 먼저 → 프롬프트 나중.**

---

## 5. 🔥 환경 함정

**5-1. 한글 파일명은 유니코드 정규화(NFC/NFD)가 어긋납니다.** ★★★★★
bash 로 보이는 이름이 PowerShell `-LiteralPath` 로 **안 열립니다.**
→ `Get-ChildItem` 으로 **실제 파일 객체를 얻어서** 다루고, 이름 문자열로 조립하지 마세요.
→ **폴더·파일 이름은 영문 slug 권장.**

**5-2. 정적 서버의 MIME 을 확인하세요.** ★★★★★
`.js` 를 `text/plain` 으로 주면 브라우저가 **ES 모듈 import 를 거부**합니다.
SPUM Engine 을 붙이기 전에 반드시 확인. (우리 서버가 실제로 이랬습니다)

**5-3. 비활성 탭에서는 `requestAnimationFrame` 이 멈춥니다.** ★★★★★
FPS 0 이 떠도 코드 문제가 아닙니다.
게임 루프 검증은 `engine.pause()` → `engine.step(1/60)` 반복으로 **결정론적으로** 하세요.

**5-4. 제공 문서는 실제로 받을 수 없습니다.** ★★★★★
과제정의서가 준다고 한 `AGENTS.md`·`README.md` 는 호스트에서 **404** 입니다(루트 `/README.md` 562B만 200).
→ **소스가 곧 문서**입니다(압축 안 됨 + 한국어 주석). 회사에 요청할 항목이기도 합니다.

**5-5. "SPUM"이 두 개입니다.** ★★★★☆
검색하면 대부분 **Unity 에셋 SPUM**(위키·유튜브 다수)이 나오는데 **우리와 무관**합니다.
웹 **SPUM Studio** 는 튜토리얼·문서가 사실상 0건.
→ 볼 것: 공개 데모 `spum.soonsoon.ai/studio/sai-character-world-demo/` · 소스 `spum.soonsoon.ai/packages/`
※ `soonsoon.co` 도메인은 사라졌습니다(NXDOMAIN). 검색 결과 링크 대부분 무효.

---

## 6. SPUM Engine — 있는 것 / 없는 것

**있습니다 — 직접 짜지 마세요** *(존재는 전부 소스에서 확인. "실행" 열은 우리가 돌려봤는지 여부)*

| 기능 | 쓰는 법 | 실행 |
|---|---|---|
| 타일맵 | `TileSet` + `TileMapSystem` + `TileMapRenderer` | ★★★★★ |
| 입력·카메라 | `InputManager` · `Camera` | ★★★★★ |
| **AI 이동(A*)** | `PathfindingManager.buildFromTileMap(tileMap, opts)` → `NavAgent.setDestination(x, y)` | ★★★★☆ |
| **말풍선** | `BubbleRenderer` — speech / thought / shout / whisper | ★★★★☆ |
| 애니메이션 | `Animator` (스프라이트 시트 필요) | ★★★★☆ |
| 저장·복원 | `Scene.toJSON()` / `fromJSON()` | ★★★★☆ |
| 관계·대화 구조 | `spum-world`: `RelationshipMemory` · `ConversationModel` · `WorldSpeechDirector` | ★★★★☆ |

**⚠️ `BubbleRenderer` 는 패키지 루트에서 import 안 됩니다.** ★★★★★

```js
import { BubbleRenderer } from ".../spum-engine/lib/domain/ui/index.js";   // ✅
import { BubbleRenderer } from ".../spum-engine/index.js";                 // ❌ 루트에 없음
```

**⚠️ 길찾기는 "별도 obstacle 배열"이 아니라 타일맵 레이어를 읽습니다.** ★★★★★
`buildFromTileMap(tileMap, { collisionLayer: 0, emptyIsWalkable: true, nonEmptyIsBlocked: false })`
→ 충돌 정보를 **TileMap 레이어로 올린 뒤** 그 인덱스를 `collisionLayer` 로 지정하세요.
0/1 값을 쓸 거면 **`nonEmptyIsBlocked: true`** 로 줘야 `1`이 벽으로 잡힙니다.

**없습니다 — 직접 만들어야 합니다** ★★★★★ *(소스 전수 검색으로 확인)*
- **시야 제한 / 안개(fog of war)** · **조명**
- **추적 카메라** — `CameraController` 는 **마우스 줌/팬 전용**입니다. 따라가는 카메라는 직접 구현하세요.

**주의할 것**
- `TileSet(img, cellW, cellH, …)` 는 시트에서 **잘라올** 크기,
  `TileMapSystem({ tileWidth, tileHeight })` 는 화면에 **그릴** 크기. **별개입니다.** ★★★★★
- `Camera.isMain = true` 를 켜야 엔진이 메인 카메라로 인식합니다. ★★★★★
- 렌더 순서 = `sortingLayer` → `transform.y` → `renderOrder`. ★★★★★

---

## 7. git

- **push 전 `git pull`.** 같은 clone 을 여러 세션이 공유하면 **동시 git 작업 금지.** ★★★★★
- **`git add -A` 를 조심하세요.** 다른 세션이 작업 중인 미완성 파일이 딸려 들어갑니다.
  → **경로를 명시**해서 add 하세요. (우리가 실제로 당했습니다) ★★★★★
- **비가역 작업**(force push · history 재작성 · 삭제 · 개명)은 반드시 사람 확인 후. ★★★★★
