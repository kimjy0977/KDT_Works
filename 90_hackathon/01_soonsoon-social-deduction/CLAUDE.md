# 「누가 내 케이크 먹었어?」 — 순순팩토리 기업연계

> **공통 규율(페르소나·보안·git·폴더규약·도구함정)은 상위 `90_hackathon/CLAUDE.md` 에 있다.**
> 이 문서는 **이 과제에만** 해당하는 것.
> 마감 **2026-08-21** · 팀 《순순히 따라와라》 · 주식회사 순순팩토리.

> ## 🔒 게임 코드는 이 저장소에 없다 (2026-08-27)
>
> 회사가 **SPUM 은 자사 라이선스 상품이라 공개는 곤란하다**고 요청했다
> (퍼실 조해창 전달 · 대표님 통화). `KDT_Works` 는 학습 아카이브라 **공개를 유지**하고,
> 게임만 **비공개 저장소 `KDT_MafiaGame`** 으로 히스토리째 옮겼다.
>
> | | 어디 |
> |---|---|
> | `proto/**` · `serve.sh` · `docs/tutorial.md` | 🔒 `github.com/kimjy0977/KDT_MafiaGame` |
> | 보고서 · `notes/` · `index.html` · `pitch/` | 🌐 여기 (`KDT_Works`) |
>
> **아래 문서의 `proto/…` 경로는 전부 비공개 저장소 기준이다.** 그쪽도 `serve.sh` 가
> 루트, `proto/` 가 그 아래라 **구조가 같다** — `bash serve.sh` 가 그대로 동작한다.
>
> ⚠ **지운 게 아니라 옮긴 것이다.** 커밋 192개가 08-18 첫 커밋부터 보존돼 있다.
>
> ⚠ **실제로 새던 것은 코드가 아니라 에셋이었다.** `vendor/`(회사 엔진)는 애초에
> 커밋하지 않았고 그 규칙은 지켜졌다. 그런데 **`proto/assets/` 의 SPUM 스프라이트
> 67개·13MB 가 그 규칙에 없어서** 공개 저장소에 올라가 있었다. **규칙의 구멍이었다.**
>
> ⚠ **배포본은 살아 있으나 주소를 비공개 취급한다**(주영님 결정 2026-08-28).
> 공개 문서(README·보고서·기획서)에서 배포 주소를 전부 걷어냈고
> 「플레이는 김주영에게 문의」로 대체했다. 잠금(비밀번호)은 유료라 안 달았다 —
> **주소를 아는 사람에게는 소스·에셋이 여전히 HTTP 200 으로 나간다.**
> 공개 문서에 배포 주소를 다시 적지 말 것.

**한 줄:** 셰어하우스 거주자 5명 중 한 명이 되어, 밤 사이 냉장고의 케이크를 훔쳐 먹은 범인을 찾는 AI 소셜 추리 게임.

> ## ⚠ 이 폴더에는 **게임이 두 개** 있다 (2026-08-23 추가)
>
> | | 무엇 | 왜 |
> |---|---|---|
> | **케이크 판** `game.html` | 냉장고 범인 찾기 | **과제 제출물.** 성공기준 §1~§4 를 이걸로 충족했다 |
> | **마피아 판** `mafia.html` | 「누가 마피아지?」 밤·살해·유령·투표 | **발표 시연작(2026-08-21).** SPUM 한계를 확인한 뒤 만든 것 |
>
> 아래 §3·§7 은 오래 **케이크 판 기준**으로만 쓰여 있었다. 마피아 판을 만지려면
> **§7-b 마피아 코드 지도**를 본다. 두 판은 `world.js`·`groupchat.js`·`settings.js`·
> `typing.js`·`similar.js` 등을 **공유**하므로, 공유 파일을 고치면 **양쪽을 다 확인**한다.

---

## 0. 용어

- 이 프로젝트의 작업 세션은 **「해커톤 세션」** 이라 부른다. 회차는 `해커톤 세션 N차`.
  (튜터 세션·매니저 세션과 구분하기 위함 — 그냥 "세션 2" 라고 쓰면 어느 세션인지 모른다.)
- **⚠ 「SPUM 세션」은 다른 뜻이다** — Studio 로그인 세션(30분 만료, `work-rules.md` A-3).
  문서에서 치환할 때 이 둘을 섞지 말 것.
- 문서를 어디에 적을지는 **`docs/README.md` 문서 지도**를 따른다.
- **폴더가 둘이다(2026-08-26).** `docs/` = **밖으로 나가는 것만**(회사 보고서·그림·공개 기술문서),
  `notes/` = **우리 작업 기록**(함정·인계·기획·이력). 새 문서를 만들 때 어느 쪽인지 먼저 정한다.
  ⛔ `docs/soonsoon-hackathon.html` 주소는 바꾸지 않는다 — 이미 팀원들에게 보냈다.

---

## 1. ⛔ 읽는 순서 (건너뛰지 말 것)

| 순서 | 파일 | 왜 |
|---|---|---|
| 1 | `_local/회사자료/과제정의서_순순팩토리.docx` | **채점 기준 원본.** ⛔ 비커밋 — 로컬에만 있다 |
| 2 | `notes/work-rules.md` | SPUM 조작 함정 모음 |
| 3 | `notes/handoff.md` | 지금 어디까지 왔나 |
| 3-b | `notes/team-onboarding.md` | **팀원이 새로 합류하면 이것부터.** 환경 세팅 + SPUM 을 코드로 다루는 법 |
| 4 | `notes/engine-capability-audit.md` | 엔진으로 뭐가 되고 뭐가 안 되나 |
| 5 | `notes/game-spec.md` | 기획 확정본 |
| 5-b | `notes/multiplayer-design.md` | 멀티(사람3+AI3) 설계안 — 규칙 엔진 계약. **구현 전** |
| 6 | `notes/sam-connection-guide.md` | **SPUM/SAM 정본 레퍼런스** — 스키마·localStorage 키·맵 코드작성 절차(§4-5)·스프라이트 시트 스키마(§4-6)·자료 현황(§8). SPUM 만질 때 여기부터 |

> 전체 작업 이력(실패 포함) **정본 = `notes/handoff.md`**(세션별 §0-최신). `notes/worklog.md`는 2차(08-19)에서 멈춘 초기 기록 — 이중관리 드리프트 방지로 채우지 않는다. 요건 분석·내부 자료 = `_local/내부자료/`.

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
**셀 = 이미지폭 ÷ 격자수.** 옛 테마는 192px ÷ 16 = **12px**, 현재 평면도는 1024px ÷ 32 = **32px**.
맵의 `tilesets[]` 가 시트마다 `cell` 과 `tileIdBase` 를 알려 준다 — 코드에 박지 말 것.

**4-6. SPUM 맵 저장구조 = 로컬 `map.json` 과 동일.** (상세 스키마·절차 = `notes/sam-connection-guide.md` §4-5)
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
**없는 것:** 시야/안개 시스템, 조명. 자세히는 `notes/engine-capability-audit.md`.

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
| `proto/tools/map-rooms.mjs` | **무대 4개의 방 안쪽 열기 + 침대 좌표**(설산은 `lodge-walls.mjs`). 멱등 · `--write` |
| `proto/tools/map-grid.mjs` | 무대 그림에 **좌표를 찍은 격자**를 얹어 확대 — 벽·문·침대를 손으로 읽는 눈 |
| `proto/tools/map-overlay.mjs` | 통행 판정을 그림 위에 **빨갛게** 겹쳐 보기 — 맵을 고친 뒤 눈으로 확인하는 자리 |
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
| `src/phase.js` | 게임 루프(저녁→밤→아침→토론→투표→판정) · 밤 시야 · 목격 기록 · 조사(josa) |
| `src/typing.js` | 대사를 **사람 타자 속도로** 한 글자씩 출력 · 「입력 중…」 · 배속(1x/3x/즉시) · 스킵 |
| `src/action.js` | **「지금 할 수 있는 것」을 한 곳에서 결정** — Space 로 실행 · 하단 도움말에 표시 |
| `src/moves.js` | **발언 행동**(캐묻기·모순 짚기·의심·감싸기·목격 공개·침묵) → 자연어 문장으로 번역 |
| `src/settings.js` | **설정**(O) — 글자 크기·UI 크기. 글자는 줌으로 나눠 화면상 크기를 고정 |
| `src/notebook.js` | **단서 수첩**(N) — 들은 말에서 「누가·언제·어디」를 뽑아 표로 · 모순 자동 표시 |
| `server.mjs` | 정적 서버 + SAM 프록시(키 미노출). `/api/ask` `/api/cast` `/api/verdict` |
| `engine.mjs` | 캐릭터 원본 데이터 · 프롬프트 빌더 · `cleanLine` · SAM 호출 |

> **정답(범인·기억)은 서버에만 둔다.** 클라이언트에 넣으면 개발자도구로 다 보여 추리가 성립하지 않는다.
> ⚠ **마피아 판은 이 원칙을 안 지킨다** — 역할·투표·승패가 전부 클라이언트에 있다.
> 싱글 전용이라 지금은 문제가 없지만, **멀티로 가면 제일 먼저 고쳐야 할 곳**이다
> (`notes/multiplayer-design.md` §1).

---

## 7-b. 마피아 판 코드 지도 (2026-08-21 발표 시연작)

| 파일 | 역할 |
|---|---|
| `mafia.html` | 화면 껍데기. 지목판·대형 안내(`#shout`)·참여자 바 마크업/CSS |
| `src/mafia/main.js` | 부팅 · 키 배선(`T` 토론 · `V` 밤 전체보기 · `[ ]` 글자 크기) |
| `src/mafia/round.js` | **게임 루프** 저녁→밤→아침→토론→투표. 배너·대형 안내·NPC 몰기 |
| `src/mafia/roles.js` | 역할 배정 · 승패 판정 |
| `src/mafia/sleep.js` | 밤 장막(시야) · 페이드 · 취침 집계 · 발밑 「Space 잠자기」 안내 |
| `src/mafia/ghost.js` | 유령 가시성(매 프레임) · 사망 흑백 화면 · **밤 입막음** |
| `src/mafia/roster.js` | 참여자 얼굴 바 · 취침 카운터 |
| `src/mafia/attitudes.js` | **발언 태도** 목록·굴리는 규칙. 게임과 측정기가 **같이 쓴다** |
| `src/votescreen.js` | 지목판 — 「아직 정하지 못했다」에서 대상에게 표가 날아간다 |
| `src/similar.js` | **되풀이 판정**(글자 2-gram). 게임과 측정기가 **같이 쓴다** |
| `src/groupchat.js` | 전체 토론 UI. **두 판이 공유** — `api`·`문맥`·`참석`·`키단축` 을 갈아 끼운다 |
| `tools/eval.mjs` | **평가 하네스**(CLI). 대사 품질·지목 캘리브레이션. `--go` 없이는 SAM 안 부름 |
| `tools/regress.mjs` | **한 판 회귀** — 규칙·배선을 SAM 없이 37항목 확인. 고치고 나면 이걸 먼저 돌린다 |
| `tools/balance.mjs` | 역할 구성별 시민 승률 (규칙만 4만 판) |
| `tools/bias-probe.mjs` | 지목 편향 분리 측정 · `--swap`/`--human`/`--saw` 대조군 |
| `tools/walls.html` | **벽 편집기** — obstacle 레이어를 눌러서 고친다. 저장 전 연결성 검사 |
| `src/audio.js` | 소리 — 음악·효과음을 **오실레이터로 만든다**(음원 파일 0장) |
| `src/backoff.js` | 재시도 정책 — 게임과 측정기가 같이 쓴다(N-4) |

**마피아 판 함정 — 고치기 전에 읽을 것 (`notes/work-rules.md` N·O 절이 정본):**

- **N-1** 값을 옮기면 **끝까지 따라가서** 확인한다. 태도가 `server.mjs` 에서 누락돼
  프롬프트에 한 번도 안 들어갔다 — 프롬프트를 고쳐도 안 낫던 이유가 그것이었다.
- **N-2** 되풀이는 프롬프트로 못 막는다 → `similar.js` 로 **받은 뒤에 거른다.**
- **N-3** 다음 요청은 **앞사람 말이 대화록에 들어간 뒤**에 쏜다. 먼저 쏘면 같은 문맥 → 같은 대사.
- **N-4** 측정기는 게임과 **같은 부품·같은 호출 방식**(재시도 포함)을 써야 한다.
- `wander.goTo()` / `wander.release()` 로만 NPC 를 움직인다. `wander.enabled=false` 로 끄면
  **아무도 안 걷는다**(§5 아래 `round.js` 주석에 자세히).

---

## 8. 과제 요건 대응 현황 (2026-08-20 기준 · **발표·채점 완료 2026-08-21**)

**성공기준 4개 전부 충족했다.** 아래는 무엇으로 충족했는지의 대조표다.

| 성공기준 | 대응 | 상태 |
|---|---|---|
| §1 브라우저에서 바로 실행 | `bash serve.sh` → `localhost:5173` · Node 외 의존성 없음 | ✅ |
| §2 NPC 3명 이상 · 성격 반영 | 거주자 **6명** · 근접 `E` · 전체 토론 `T` | ✅ |
| §3 대화 맥락 유지 | 캐릭터별 history 누적 전송 · 전체 토론은 공개 대화록 | ✅ |
| §4 기술 문서 | `README.md` + **`docs/tutorial.md`(626줄)** | ✅ |
| §8 키 커밋 금지 · MIT | 서버에서만 읽음 · `.env` gitignore · `LICENSE` | ✅ |

**§4 추가(게임적 재미)** — 시작화면·무대 2개·참여/관전·캐릭터 선택·역할 공개·
단계 타이머·밤 시야·목격·미니맵·다수결 지목·승패 4분기·**타이핑 연출**.

### 완료된 것 (예전 목록의 잔재를 지운다)

- ~~기술 문서~~ ✅ `docs/tutorial.md` + `README.md`
- ~~밤 시뮬 랜덤 배정~~ ✅ `proto/night.mjs` → `/api/newgame` · **플레이어 포함 매 판 랜덤**
- ~~스프라이트 추가 추출~~ ✅ **12/12**(6명 × idle+move) · 전부 SPUM 제작본
- ~~시야 제한~~ ✅ 밤 단계에 들어감 (요건은 아니었다)

### 검증 상태 — 과장하지 말 것

`proto/run.mjs` 7항목. **실측 2회: 7/7 · 6/7.**
흔들리는 항목은 레드헤링 하나이고 원인은 **LLM 응답 변동**이다.
문서에 "7/7 통과"라고만 쓰면 과장이다 — 실측값을 그대로 적는다(§7).

### 발표 후 상태 (2026-08-23)

- **발표·채점 끝났다.** 진행 현황·다음 할 일은 `notes/handoff.md` **§0-최신(9차)** 가 정본이다.
- **`proto/vendor/` 는 커밋하지 않는다**(회사 코드). `serve.sh` 가 없으면 **알아서 내려받는다** —
  새로 클론해도 `bash serve.sh` 한 번이면 된다. 수동: `node mirror.mjs spum-engine` / `spum-world`.
- 로스터 **10명 전원 사용 가능**(2026-08-24). 곰곰이 시트를 SPUM 에서 뽑아 넣었고,
  게이트(`{slug}-idle.json` 존재 여부)가 **코드 수정 없이** 자동 해제했다.
  같이 고친 것: 딴청이 `move` 확보 · **주춤이 idle/move 가 같은 PNG 였던 것**(A-4 사고).
- **폴더 개명 `01_` 완료**(2026-08-23 매니저) — 참조 19곳 갱신·tools 절대경로 해소 포함.

### 남은 것 (요건 밖 · 여유 있을 때만)

1. 로컬 게임 **한 판 완주 회귀 검증** — 2026-08-20 에 단계 시간을 바꿨다(저녁 130·토론 200)
2. 우주선 무대의 플레이 밸런스 — 64×64 라 이동이 길다
3. 세 번째 무대 — **하지 않기로 했다**(마감 대비 효용 낮음)
