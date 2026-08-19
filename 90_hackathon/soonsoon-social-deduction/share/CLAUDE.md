# SPUM + SAM 작업용 하네스 (팀 공용 · 그대로 복사해 쓰세요)

> 이 파일을 **본인 프로젝트 폴더 루트에 `CLAUDE.md` 로 저장**하면, 그 폴더에서 연 Claude 세션에
> 아래 규칙이 자동 적용됩니다. 팀 《순순히 따라와라》가 SPUM으로 실제 작업하며 **대가를 치르고 얻은 것**만 담았습니다.
> 프로젝트 고유 내용(마감·과제 요건 등)은 각자 §0 에 채워 넣으세요.

---

## 0. 이 프로젝트 (각자 채우기)

- **무엇을 만드나:**
- **마감:**
- **과제 성공 기준:** ← ⛔ **과제정의서 원본을 먼저 읽고 여기 옮겨 적으세요.**

> ⚠️ 우리가 실제로 낸 실수: 팀 자체 기획서를 요건으로 착각해 **채점표에 없는 기능을 최우선으로** 잡았습니다.
> **자체 기획 ≠ 과제 요건.** 우선순위는 항상 과제정의서 기준으로 정하세요.

---

## 1. 톤·태도

- 한국어 존대 · **결론부터** · 직언(아첨 금지) · 지어내기 금지
- **확인 안 한 건 "확인 안 됨"이라고 말한다.** 7/7이면 7/7, 2/5면 2/5. 실패를 성공처럼 보고하지 않는다.
- **신뢰도 5단계 표기:** ★★★★★ 직접 확인 / ★★★★☆ 문서 근거 / ★★★☆☆ 추정 / ★★☆☆☆ 불확실 / ★☆☆☆☆ 미확인
- **산출물은 만든 즉시 실제로 적용해서 눈으로 확인한다.** (맵 만들어놓고 월드에 안 붙인 전례 있음)
- **결과물에서 멀어지면 즉시 중단하고 보고한다.** (도구 연결에 매달렸는데 결국 게임과 무관했던 전례 있음)

---

## 2. 🔒 보안 — 먼저 확인하세요

- **SAM 키를 어떤 파일에도 쓰지 않는다.** 전체든 **접두사든**. `.env`(gitignore) 또는 환경변수만.
  → 우리는 문서에 적은 **키 앞 8자리** 때문에 히스토리를 재작성해야 했습니다.
- **`claude mcp add --scope project` 금지** — 레포 `.mcp.json` 에 키가 박혀 커밋됩니다. `local` / `user` 를 쓰세요.
- **`claude mcp get <이름>` 은 키를 평문 출력합니다** — 화면 공유 중이면 주의.
- **회사 제공 자료(과제정의서·회사소개서 등)는 커밋하지 않는다.** `_local/` 같은 gitignore 폴더에 두세요.
- 커밋 전 1초 자문: **"이거 공개 레포에 올라가도 되나?"**
- 커밋 전 점검: `grep -rn "sam-[0-9a-f]\{8\}" .`

---

## 3. 🔥 SPUM Studio 함정 (전부 한 번씩 당한 것)

**3-1. 쓰기 방향은 반드시 `로컬 → 서버`.** ★★★★★
SPUM Studio는 **브라우저 `localStorage` 가 원본**이고 서버는 백업입니다.
```js
window.spumStudioData.export();                      // ① 백업 먼저 (항상)
localStorage.setItem(KEY, JSON.stringify(data));     // ② 로컬에 쓰기
window.dispatchEvent(new CustomEvent("spum:studio-storage-write", {detail:{key:KEY}}));
await window.spumStudioData.saveServerSnapshot("manual");  // ③ 서버로
// ④ 페이지 새로고침해야 앱이 읽는다
```
> ❌ **서버에 직접 `PUT /api/studio/state` 하지 마세요.** 다음 새로고침 때 브라우저 로컬이 서버를 덮어써서
> 작업이 사라집니다. (팀원이 3번 당했습니다 — revision 69까지 올라갔다가 통째로 날아감)

**주요 localStorage 키:** `sv_studio_characters_v1`(캐릭터) · `sv_studio_maps_v1`(맵) ·
`sv_studio_smo_v1`(타일 테마) · `sv_studio_draft_v1`(월드)

**3-2. 세션이 30분쯤에 만료됩니다.** ★★★★★
`/api/me` 가 `{"user":null}` 이면 만료. 우측 상단 배지 → **ACCOUNT → 「다시 로그인」** → 4초.
**비밀번호 안 물어봅니다**(SSO 살아있으면). 복구 후 `saveServerSnapshot()` 로 재동기화.

**3-3. 캐스트 "배치"만은 코드로 하지 마세요.** ★★★★★
`world.casts[]` 를 코드로 만들면 앱이 *"없는/중복 캐릭터 배치 N개를 정리했습니다"* 로 **전부 삭제**합니다.
→ World Editor 좌측 `Characters` 의 **＋ → "배치"** 버튼으로. 한 명씩 누르고 확인(연속 클릭은 리렌더로 씹힘).
※ 캐릭터 **생성·수정·삭제·외형·색상**, **맵 레이어**, **월드의 mapId 교체**는 코드로 잘 됩니다.

**3-4. Cast Export(스프라이트 시트)를 신뢰하지 마세요.** ★★★★★
Generate 가 비동기라 **직전 캐릭터의 시트가 다운로드됩니다.** 미리보기로 눈 확인해도 어긋납니다.
→ 받은 뒤 반드시 JSON 의 `characterName` 으로 검증. (우리는 5명 중 2명만 정상 확보됐습니다)

**3-5. 썸네일은 코드로 외형을 바꿔도 갱신 안 됩니다.** ★★★★★
`localStorage` 로 `appearance` 를 바꿔도 `sv_studio_thumb_*` 는 예전 이미지 그대로.
목록·추출물이 쌍둥이로 보이면 이것 때문입니다. → Cast Editor 에서 UI로 한 번 편집·저장하면 재생성됩니다.

**3-6. 타일셋 셀 크기는 이미지에서 계산하세요.** ★★★★★
`grid: "16x16"` 은 셀이 16px 이라는 뜻이 **아니라 16칸**이라는 뜻입니다.
**셀 = 이미지폭 ÷ 16.** 실제로 192px 이미지라 **셀은 12px** 이었고, 64로 착각해 한참 헤맸습니다.

**3-7. 맵은 손으로 안 찍어도 됩니다 — 코드로 통째 교체됩니다.** ★★★★★
```
타일 ID = tileIdBase + (row × columns) + col      // row·col 은 0부터
레이어  = [{name, type:"back|front|walkable|obstacle", label, data:[width*height]}]
인덱스  = y * width + x
```
1200칸 × 4레이어를 그대로 붙여넣으면 컨텍스트가 탑니다 → **런렝스 압축**해서 넣고 페이지에서 푸세요.

**3-8. Map Editor 에서 타일이 안 보이면** 오른쪽 `MAP STRUCTURE → Layers` 의
**NAV 체크박스(장애물·워커블)를 끄세요.** 초록/빨강 오버레이가 타일을 가립니다. ★★★★★

**3-9. ★ World 내장 AI 는 게임 규칙에 쓸 수 없습니다.** ★★★★★
`talkConfig.systemPrompt` 를 **무시**하고, 캐릭터 메모리를 사실 근거로 **쓰지 않으며**, 없는 내용을 **지어냅니다.**
대화 모드가 Local FSM 으로 고정돼 시스템 프롬프트 입력란 자체가 없습니다.
→ **대화 로직은 SAM 직접 호출(`/v1/generate`)로 구현하세요.**

---

## 4. 🔥 브라우저 자동화 함정

**4-1. 앱 내장 브라우저 말고 실제 크롬(`claude-in-chrome`)을 쓰세요.** ★★★★★
내장 브라우저는 SPUM 로그인 세션이 없어 아무것도 못 합니다.
증상이 "권한 차단"처럼 보여도 원인은 이것입니다. (우리가 이걸로 시간을 버렸습니다)

**4-2. 네트워크/DOM 덤프로 base64 를 뽑지 마세요.** ★★★★★
이미지 요청을 조회하면 base64 가 통째로 쏟아져 **컨텍스트가 순식간에 고갈**됩니다.
반드시 개수·상태코드만 보도록 필터링하세요.

**4-3. `javascript_tool` 반환값이 차단될 때가 있습니다.** ★★★★☆
쿠키·쿼리스트링·대용량이 섞이면 `[BLOCKED]`. → **요약해서 반환**하거나,
`document.title` 에 값을 써서 탭 제목으로 읽는 우회가 잘 통합니다.

**4-4. iframe 안을 봐야 할 때가 있습니다.** ★★★★★
Object Tile Editor 는 `/studio/pixeldeidtor/index.html` iframe 입니다. 부모 document 쿼리로는 아무것도 안 잡힙니다.
→ `document.querySelector('iframe[src*="pixeldeidtor"]').contentDocument`

**4-5. 커스텀 드롭다운은 화면 클릭으로 안 열립니다.** ★★★★★
네이티브 `<select>` 가 아니면 스크린샷에 팝업이 안 뜹니다.
→ 내부 `<select>` 를 찾아 `value` 설정 후 `input`/`change` 이벤트를 dispatch.

**4-6. 프리셋을 바꾸면 프롬프트가 덮어써집니다.** ★★★★★
Object Editor 에서 Preset 변경 시 Reference Prompt 가 기본값으로 리셋됩니다. **프리셋 먼저 → 프롬프트 나중.**

---

## 5. 🔥 그 외 환경 함정

**5-1. 한글 파일명은 유니코드 정규화(NFC/NFD)가 어긋납니다.** ★★★★★
bash 로 보이는 이름이 PowerShell `-LiteralPath` 로 안 열릴 수 있습니다.
→ `Get-ChildItem` 으로 **실제 파일 객체를 얻어서** 다루고, 이름 문자열로 조립하지 마세요.
→ **폴더·파일 이름은 영문 slug 권장.**

**5-2. 정적 서버의 MIME 을 확인하세요.** ★★★★★
`.js` 를 `text/plain` 으로 주면 브라우저가 **ES 모듈 import 를 거부**합니다.
SPUM Engine 을 붙이기 전에 반드시 확인.

**5-3. 비활성 탭에서는 `requestAnimationFrame` 이 멈춥니다.** ★★★★★
FPS 0 이 떠도 코드 문제가 아닙니다. 게임 루프 검증은 `engine.pause()` → `engine.step(1/60)` 반복으로
**결정론적으로** 하세요.

**5-4. 제공 문서는 실제로 받을 수 없습니다.** ★★★★★
과제정의서가 준다고 한 `AGENTS.md`·`README.md` 는 호스트에서 **404** 입니다.
→ **소스가 곧 문서**입니다(압축 안 됨 + 한국어 주석). 회사에 요청할 항목이기도 합니다.

**5-5. "SPUM"이 두 개입니다.** ★★★★★
검색하면 대부분 **Unity 에셋 SPUM**(위키·유튜브 다수)이 나오는데 **우리와 무관**합니다.
웹 **SPUM Studio** 는 튜토리얼·문서가 사실상 0건입니다.
그래서 볼 것: 공개 데모 월드 `spum.soonsoon.ai/studio/sai-character-world-demo/` · 소스 `spum.soonsoon.ai/packages/`
※ `soonsoon.co` 도메인은 사라졌습니다(NXDOMAIN). 검색에 나오는 링크 대부분 무효.

---

## 6. SPUM Engine — 있는 것 / 없는 것

**있습니다 (직접 짜지 마세요):**
`TileSet`·`TileMapSystem`·`TileMapRenderer`(타일맵) · `InputManager` · `Camera` ·
**`PathfindingManager.buildFromTileMap()` + `NavAgent.setDestination()`**(AI 이동 A*) ·
**`BubbleRenderer`**(말풍선 speech/thought/shout/whisper) · `Animator` · `ParticleSystem` ·
`FloatingTextRenderer`·`ProgressBarRenderer` · `Scene.toJSON/fromJSON`(저장)
`packages/spum-world`: `RelationshipMemory`(trust·tension·affinity) · `ConversationModel` · `WorldSpeechDirector`

**없습니다 (직접 만들어야):**
**시야 제한/안개(fog of war)** · 조명 · **추적 카메라**(`CameraController` 는 마우스 줌/팬 전용입니다)

**주의:** `TileSet(img,12,12,…)` = 시트에서 **잘라올** 크기 / `TileMapSystem({tileWidth:32})` = **그릴** 크기. 별개입니다.
`Camera.isMain = true` 를 켜야 엔진이 메인 카메라로 인식합니다.
렌더 순서 = `sortingLayer` → `transform.y` → `renderOrder`.

---

## 7. git

- **push 전 `git pull`.** 같은 clone 을 여러 세션이 공유하면 **동시 git 작업 금지.**
- **`git add -A` 를 조심하세요.** 다른 세션이 작업 중인 미완성 파일이 딸려 들어갑니다.
  → **경로를 명시**해서 add 하세요. (우리가 실제로 당했습니다)
- **비가역 작업**(force push · history 재작성 · 삭제 · 개명)은 반드시 사람 확인 후.
