# 「누가 내 케이크 먹었어?」 — 순순팩토리 기업연계

> **공통 규율(페르소나·보안·git·폴더규약·도구함정)은 상위 `90_hackathon/CLAUDE.md` 에 있다.**
> 이 문서는 **이 과제에만** 해당하는 것.
> 마감 **2026-08-21** · 팀 《순순히 따라와라》 · 주식회사 순순팩토리.

**한 줄:** 셰어하우스 거주자 5명 중 한 명이 되어, 밤 사이 냉장고의 케이크를 훔쳐 먹은 범인을 찾는 AI 소셜 추리 게임.

---

## 1. ⛔ 읽는 순서 (건너뛰지 말 것)

| 순서 | 파일 | 왜 |
|---|---|---|
| 1 | `_local/회사자료/과제정의서_순순팩토리.docx` | **채점 기준 원본.** ⛔ 비커밋 — 로컬에만 있다 |
| 2 | `docs/work-rules.md` | SPUM 조작 함정 모음 |
| 3 | `docs/handoff.md` | 지금 어디까지 왔나 |
| 4 | `docs/engine-capability-audit.md` | 엔진으로 뭐가 되고 뭐가 안 되나 |
| 5 | `docs/game-spec.md` | 기획 확정본 |
| 6 | `docs/sam-connection-guide.md` | **SPUM/SAM 정본 레퍼런스** — 스키마·localStorage 키·맵 코드작성 절차(§4-5)·스프라이트 시트 스키마(§4-6)·자료 현황(§8). SPUM 만질 때 여기부터 |

> 전체 작업 이력(실패 포함) = `docs/worklog.md`. 요건 분석·내부 자료 = `_local/내부자료/`.

---

## 2. 과제 성공 기준 (과제정의서 §7 — 이게 채점표다)

1. **브라우저에서 바로 실행** — 설치 없이 `bash serve.sh` → localhost
2. **NPC 3명 이상**과 자연어 대화, 각 응답이 **설정된 성격에 맞을 것**
3. **대화 맥락 유지** — 이전 대화 참조 가능
4. **기술 문서** — README 또는 블로그 1편 분량

§4 추가: "간단한 퀘스트/이벤트 시스템으로 게임적 재미" · "완벽한 상용 제품 아니어도 됨"

**제약(§8) — 코드와 무관하게 깎인다:**
SAM 키 커밋 금지(환경변수) · `bash serve.sh` 구동 · **MIT 라이선스** · 상용 데이터 사용 금지

### ⚠️ 요건에 **없는** 것
**시야 제한(fog of war)** — 성공기준에도 보너스에도 없다. `game-spec.md` §1이 "핵심"이라 부르지만
과제 원문은 **"기능 수보다 대화의 질 우선"**. 만들지 말라는 게 아니라 **순위를 알고 결정하라**는 뜻.

---

## 3. 아키텍처

**SPUM Engine 을 구동하는 로컬 페이지(`proto/game.html`)** 가 게임이다.
SPUM Studio 의 World 런타임이 **아니다.** SPUM 은 에셋 저작소(맵·캐릭터·타일) 역할.

**대화는 SAM 직접 호출**(`proto/server.mjs` → `/v1/generate`).
World 내장 AI는 `systemPrompt`를 무시하고 기억을 근거로 안 쓰고 지어낸다 — 검증 완료(`game-spec.md` §6).

**핵심 설계:** 시스템이 정답(ground truth)을 먼저 고정하고, 각 캐릭터에겐 **자기 기억만** 준다.
그래서 추리가 성립한다. 근거 엔진 검증 **7/7**(`proto/run.mjs`).

---

## 4. 🔥 SPUM 함정

**4-1. SPUM 쓰기는 반드시 `로컬 → 서버` 순서.**
`export()` 백업 → `localStorage.setItem` → `dispatchEvent('spum:studio-storage-write')`
→ `saveServerSnapshot('manual')` → **새로고침**. 서버에 직접 PUT 하면 다음 새로고침에 날아간다.

**4-2. SPUM 세션은 30분쯤에 만료된다.**
`/api/me` 가 `{"user":null}` 이면 만료. 우측 상단 배지 → ACCOUNT → **「다시 로그인」** → 4초.
**비밀번호 안 물어본다.** 묻지 말고 바로 복구할 것.

**4-3. 캐스트 "배치"만은 코드 금지.** `world.casts[]` 를 코드로 만들면 앱이 전부 지운다.
World Editor 에서 `+` → "배치" 버튼으로. (생성·수정·외형·맵레이어·mapId 교체는 코드로 잘 된다.)

**4-4. Cast Export 는 신뢰하지 말 것.** Generate 가 비동기라 **직전 캐릭터 시트가 다운로드된다.**
받은 뒤 반드시 JSON 의 `characterName` 으로 검증.

**4-5. 타일셋 셀 크기는 이미지에서 계산.** `grid: "16x16"` 은 셀이 16px 이라는 뜻이 아니다.
**셀 = 이미지폭 ÷ 16.** 실제로 192px ÷ 16 = **12px**.

**4-6. SPUM 맵 저장구조 = 로컬 `map.json` 과 동일.** (상세 스키마·절차 = `docs/sam-connection-guide.md` §4-5)
레이어 4개(`back_1`/`front_1`/`walkable`/`obstacle`) · 각 1200칸 · `tileIdBase 2049` · `columns 16`.
→ 맵은 **로컬에서 만들어 스크립트로 밀어넣는다.** 에디터 수작업 불필요.

## 5. 🔥 엔진 함정

**5-1. `CameraController` 는 추적 카메라가 아니다** — 마우스 줌/팬 전용.
따라가는 카메라는 `FollowCamera`(직접 작성, `game.html`)를 쓴다.

**5-2. `TileSet` 크기와 `TileMapSystem` 크기는 별개.**
`TileSet(img,12,12,{firstId:2049})` = 시트에서 **잘라올** 크기 / `TileMapSystem({tileWidth:32})` = **그릴** 크기.

**5-3. `Camera.isMain = true`** 를 켜야 `Engine._getMainCamera()` 가 찾는다.
렌더 순서 = `sortingLayer` → `transform.y` → `renderOrder`.

**5-4. 캐릭터 초상 PNG 에 알파가 없다(100% 불투명).** 그대로 얹으면 검은 사각형.
→ `tools/cut-chars.mjs` 로 **테두리 flood-fill** 제거. 색 전역 제거는 안 됨(머리카락이 배경만큼 어둡다).

**5-5. 엔진이 이미 주는 것 — 직접 짜지 말 것:**
`PathfindingManager` + `NavAgent.setDestination()` (AI 이동) ·
`BubbleRenderer` (말풍선 4종) · spum-world `RelationshipMemory`·`ConversationModel` (관계·대화세션).
**없는 것:** 시야/안개 시스템, 조명. 자세히는 `docs/engine-capability-audit.md`.

**5-6. ⚠ `update()` 에서 예외가 나면 엔진이 그 컴포넌트를 조용히 끈다.**
`GameObject._executeUpdate` 가 `catch → c.enabled = false` 한다. 게다가 경고를
`engine._frameWarnings` 에만 담고 **콘솔에 안 찍는다** → NPC 하나가 말없이 멈춘다.
증상이 "로직 오류"처럼 보여도 원인은 이것일 수 있다. 의심되면 `comp.enabled` 와
`engine._frameWarnings` 를 먼저 볼 것.

**5-7. `BubbleRenderer` 는 루트 `index.js` 에서 export 되지 않는다.**
`lib/domain/ui/index.js` 에서 직접 import 해야 한다. (UI 3종 중 2종만 루트에 노출돼 있다.)

**5-8. `PathfindingManager.buildFromTileMap()` 은 우리 맵에 안 맞는다.**
타일 속성 `walkable` 을 읽는데 우리 테마엔 그 속성이 없다.
→ `map.json` 의 `obstacle` 레이어를 `setGrid()` 로 직접 넘긴다(`src/world.js`).
`NavAgent` 는 `PathfindingManager.getOrCreate(scene)` 으로 **씬을 훑어** 인스턴스를 찾으므로
씬 어딘가에 하나만 만들어 두면 전원이 공유한다.

---

## 6. 실행

```bash
bash serve.sh            # → http://localhost:5173/game.html
```

| 도구 | 용도 |
|---|---|
| `proto/tools/build-map.mjs` | 맵 생성 + **자체 연결성 검증**(실패 시 빌드 중단) |
| `proto/tools/png.mjs` | 의존성 없는 PNG 디코더/인코더 — 브라우저 없이 눈으로 검증 |
| `proto/tools/cut-chars.mjs` | 캐릭터 초상 배경 제거 |
| `proto/tools/atlas.html` | 타일 시트 격자 뷰어 |
| `proto/mirror.mjs` | SPUM 패키지 미러링 (`spum-engine` · `spum-world`) |

---

## 7. 코드 지도 (`proto/`)

| 파일 | 역할 |
|---|---|
| `game.html` | 화면 껍데기(캔버스·HUD·대화창 마크업/CSS)만. 로직 없음 |
| `src/main.js` | 부팅 — 월드 생성 → 대화 시스템 연결 → 루프 시작 → HUD |
| `src/world.js` | 엔진·타일맵·캐릭터·카메라·길찾기 그리드. `Walker`/`FollowCamera`/`NameTag` |
| `src/ai.js` | `Wander` — NPC 가 어디로 갈지만 정한다. 이동 자체는 `NavAgent` |
| `src/cast.js` | 거주자 5명 표시정보 + 배회 목적지(`PLACES`) + 예시 질문 |
| `src/talk.js` | 근접 감지 → E → 대화창 → `/api/ask` → 말풍선. **캐릭터별 history 로 맥락 유지** |
| `server.mjs` | 정적 서버 + SAM 프록시(키 미노출). `/api/ask` `/api/cast` `/api/verdict` |
| `engine.mjs` | 캐릭터 원본 데이터 · 프롬프트 빌더 · `cleanLine` · SAM 호출 |

> **정답(범인·기억)은 서버에만 둔다.** 클라이언트에 넣으면 개발자도구로 다 보여 추리가 성립하지 않는다.

---

## 8. 다음 — 과제 요건 기준 우선순위

1. ~~근접 대화~~ ✅ 완료 (성공기준 §2·§3)
2. ~~AI 4명 이동~~ ✅ 완료
3. **게임 루프** — 저녁→밤→아침→토론→투표→판정 (과제 §4). `/api/verdict` 는 이미 있다
4. **기술 문서** — 성공기준 §4. 1급 산출물
5. 스프라이트 3명 추가 추출 — 현재 5명 중 고유 2종뿐. 소셜 추리인데 구분이 안 된다
   (`assets/chars/sheets/` 에 새침이·폴짝이 idle 시트 있음 → `Animator` 사용 가능)
6. 시야 제한 — **요건 아님.** 여유 있으면
