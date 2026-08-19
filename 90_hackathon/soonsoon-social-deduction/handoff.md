# 세션 인계 — 「누가 내 케이크 먹었어?」

> 작성 2026-08-19 (세션 1 종료 시점) · 다음 세션은 **이 문서 → `work-rules.md` → `game-spec.md`** 순서로 읽는다.

---

## 0. 세션 2 (2026-08-19) 갱신 — 맵을 다시 만들었다

**진단:** 월드가 휑했던 진짜 원인은 맵 데이터였다. 173타일 테마 중 **4개만** 쓰고 있었고,
가구 레이어 `front_1` 은 **1200칸 전부 0**(빈 값)이었다. 게다가
거실 바닥엔 **옷장 타일**(시트 1,1)이, 부엌 바닥엔 **화분 타일**(시트 4,1)이 깔려 있었다.
→ 타일이 없어서가 아니라 **배치를 안 해서** 휑했던 것.

**해결 기법 — "스탬프":** 테마 시트는 낱개 타일 모음이 아니라 **완성된 인테리어 도면**이다.
가구가 여러 셀에 걸쳐 그려져 있어(침대 1x2, 조리대 4x1, 라운지 5x4) 한 셀만 반복하면 무늬가 깨진다.
그래서 시트의 **직사각 영역을 통째로** 맵에 찍는다. 원본 도면의 완성도가 그대로 옮겨진다.

| 산출물 | 내용 |
|---|---|
| `proto/tools/build-map.mjs` | 맵 생성기. 스탬프 8종 + **자체 연결성 검증**(스폰 7곳이 서로 도달 가능한지, 실패 시 빌드 중단) |
| `proto/tools/png.mjs` | 의존성 없는 PNG 디코더/인코더 — 브라우저 없이 맵·타일을 눈으로 검증 |
| `proto/tools/atlas.html` | 타일 시트 격자 뷰어 |
| `proto/assets/map.json` | 재생성. **사용 타일 4종 → 81종**, 침실 5 · 부엌 · 욕실 · 라운지 가구 배치 |

**검증한 것 (★★★★★ 직접 확인):** 미리보기 렌더로 눈 확인 · 스폰 7곳 연결성 통과.
연결성 검사가 실제로 버그 3건을 잡았다 — 조리대가 부엌 문을, 소파가 폴짝이 방을 봉인, 거실 스폰이 탁자 위.

**같이 고친 것:** `server.mjs` 가 모든 정적 파일을 `text/plain` 으로 주고 있었다
→ **`.js` MIME 이 틀리면 브라우저가 ES 모듈 import 를 거부**하므로 SPUM Engine 붙이기 전에 필수였다. 확장자별 MIME 로 수정.
`index.html` 타일 좌표 off-by-one(1-based 를 0-based 로 읽음)도 수정.

**SPUM 반영 완료 (★★★★★ 눈으로 확인):** A-1 절차대로 `sv_studio_maps_v1` 의
`MAP_msysua8z_CKYO` 4개 레이어를 교체 → `saveServerSnapshot("manual")` → 새로고침.
**서버 rev 77** 로 저장됨. Map Editor·World Play 양쪽에서 가구가 보이는 것 확인.
SPUM 저장 구조가 로컬 `map.json` 과 동일했다(레이어 4개·1200칸·`tileIdBase 2049`·`columns 16`)
→ 로컬에서 만들어 그대로 밀어넣으면 된다.

> 세션 시작 시 `/api/me` 가 `{"user":null}` 이었다(A-3 만료).
> ACCOUNT → 「다시 로그인」 으로 복구됨(비밀번호 안 물어봄). **SPUM 작업 전 로그인 상태부터 확인할 것.**

---

## 0-b. 세션 2 후반 — P0(게임 셸) 완료

`proto/game.html` 신규. SPUM Engine 위에서 **부팅 → 타일맵 → 캐릭터 → 이동 → 충돌 → 카메라 추적** 동작.
`index.html`(v1)은 비교용으로 남겨 뒀다(폐기된 "외부 탐정" 기획 화면).

**엔진 소스를 읽고 확인한 사실 (문서가 없어 직접 확인함):**
- `SpumEngine.createEngine(canvas, opts)` → `Engine`. 기본 `targetFPS: 30`.
- `TileSet(img, 12, 12, {firstId: 2049})` — 시트에서 **잘라올 크기(12px)**.
  `TileMapSystem({tileWidth: 32})` — **화면에 그릴 크기(32px)**. 둘은 별개다.
  `firstId` 는 SPUM 테마의 `tileIdBase` 와 같은 값(2049).
- `Camera.isMain = true` 를 켜야 `Engine._getMainCamera()` 가 찾는다.
- 렌더 순서 = `sortingLayer` → `transform.y` → `renderOrder`. 타일맵 -100, 캐릭터 10, 이름표 20.
- ⚠ **`CameraController` 는 추적 카메라가 아니다** — 마우스 줌/팬 전용.
  따라가는 카메라는 `FollowCamera` 로 직접 만들었다(`Camera.clampPosition` 으로 맵 밖 안 보이게).
- ⚠ **캐릭터 초상 PNG 에 알파가 없다(100% 불투명).** 그대로 얹으면 검은 사각형이 깔린다.
  → `tools/cut-chars.mjs` 로 테두리 flood-fill 배경 제거 → `assets/chars/cut/*.png`.
    (색 전역 제거는 안 된다 — 머리카락이 배경만큼 어둡다.)
- ⚠ **스프라이트 고유 개수는 3/5 가 아니라 2/5 였다.**
  꾸벅이=폴짝이=새침이, 오물오물=살살이. 일단 색 원판+이름표로 구분한다. (§5-1 해결책 필요)
- `SpriteRenderer` 사용(엔진 `Character` 는 슬롯 파츠 JSON 이 필요한데 우리에겐 없다). 걷기 애니메이션 없음.

**검증 (★★★★★ 직접 확인):** 탭이 비활성이면 `requestAnimationFrame` 이 멈춰 FPS 0 이 된다(코드 문제 아님).
`engine.pause()` 후 `engine.step(1/60)` 으로 결정론적 검증함 —
이동 정상 · **벽으로 400프레임 밀어붙여도 관통 없음**(방 경계에서 정확히 정지) · 카메라 추적/클램프 정상.

## 0-c. 다음 세션 시작점 — P1

1. **시야 제한** — 내 주변/같은 방만 보이게 (기획의 핵심, `game-spec.md` §1)
2. **근접 대화** — 가까이 가서 말 걸기 → 기존 `/api/ask`(SAM) 재사용
3. **AI 4명 이동** — `Walker` 는 이미 5명 전원에게 붙어 있다(`isPlayer` 만 false). 여기에 AI 조종을 얹으면 된다.

---

## 1. 지금 어디까지 왔나

| 영역 | 상태 |
|---|---|
| **기획** | ✅ 확정 (`game-spec.md`) — 플레이어도 거주자 1명, 어몽어스식. 결정: 범인 랜덤(플레이어 포함) / 밤에 직접 조작 / 토론 후 투표 |
| **밤 시뮬 근거 엔진** | ✅ **검증 7/7** (`proto/run.mjs`) — 거짓말·목격증언·3연타 자백·지어내기 방지 |
| **SAM 대화 연동** | ✅ 작동 (`proto/engine.mjs`, `/v1/generate`, 턴당 SSAM ~1.7) |
| **타일 테마** | ✅ `셰어하우스 인테리어` 173타일 (SPUM Object, AI 생성) |
| **맵** | ✅ `셰어하우스` 40×30 — 방5 + 부엌 + 중앙 거실 (SPUM Map) |
| **캐릭터 5명** | ✅ 성격·기억·역할 주입 + 외형 5인 차별화 (SPUM Cast) |
| **월드** | ✅ 캐스트 5명 배치 + **맵을 셰어하우스로 교체 완료** |
| **게임 런타임** | ✅ **P0 완료** — `proto/game.html` (SPUM Engine: 타일맵·이동·충돌·카메라 추적). 다음은 P1(시야 제한·근접 대화) |

## 2. 다음 세션이 할 일 (우선순위)

**P0 — SPUM Engine으로 게임 셸 세우기**
1. `proto/vendor/packages/spum-engine/index.js` 를 import 해서 `SpumEngine.createEngine("canvas")` 부팅
2. `TileMap`으로 `assets/map.json`(40×30) 렌더
3. `Character` 1명 배치 → `InputManager`로 이동 → `CameraController`로 추적
4. `Collider`/walkable 레이어로 벽 충돌
> 문서가 없으므로 **소스를 읽어가며** 붙인다. 최소 부팅부터 확인하고 하나씩 늘릴 것.

**P1 — 플레이어 관점 구현 (기획의 핵심)**
5. 내 캐릭터 지정 + **시야 제한**(내 주변/같은 방만 보임)
6. 근접 대화(가까이 가서 말 걸기) — 기존 SAM 호출 재사용
7. 밤: 플레이어 직접 이동, 범인이면 몰래 부엌行

**P2 — 루프 완성**
8. 저녁 → 밤 → 아침 → 토론 → **투표** → 판정
9. 매 판 범인 랜덤 배정(플레이어 포함) + 밤 시뮬 생성

**P3 — 마감 정리**
10. 기술문서 마무리, 리허설, 커밋

## 3. 자산 위치

```
90_hackathon/soonsoon-social-deduction/
├─ game-spec.md          기획/작업정의서 ← 먼저 읽기
├─ work-rules.md         작업 규칙서(함정 모음) ← 반드시 읽기
├─ handoff.md            이 문서
├─ reference/            ★회사 원본 자료 (과제정의서 docx · 조사노트) — reference/README.md 참조
├─ sam-connection-guide.md   팀 배포용 연결 가이드
├─ smo-map-placement.md      SMO/맵 구조 회신 문서
└─ proto/
   ├─ engine.mjs         캐릭터 데이터 + 프롬프트 빌더 + SAM 호출 (재사용)
   ├─ server.mjs         로컬 서버 + SAM 프록시 (키 미노출)
   ├─ run.mjs            자동 검증 시나리오 (7/7)
   ├─ game.html          ★현재 게임 (SPUM Engine)
   ├─ index.html         v1 캔버스 화면 — 폐기된 기획, 비교용으로만 보관
   ├─ tools/             build-map · png · cut-chars · atlas (개발 도구)
   ├─ chat.html          v0 채팅 프로토타입
   ├─ assets/
   │   ├─ map.json               40×30 레이어 + 타일좌표 매핑 (셀 12px)
   │   ├─ tileset_source.png     192×192, 16×16 그리드
   │   └─ chars/*.png            ⚠️ 3/5만 고유(썸네일 캐시 문제)
   └─ vendor/            spum-engine 65파일 (미러링, .gitignore로 커밋 제외)
```

**vendor 복구 방법** (새 환경에서):
```bash
cd proto && node mirror.mjs   # spum.soonsoon.ai/packages/spum-engine 재귀 다운로드
```
※ `mirror.mjs` 는 세션 2에서 **레포에 넣어 뒀다** (`proto/mirror.mjs`). vendor 65파일도 복구됨.

## 4. SPUM 리소스 ID (실계정)

| 항목 | ID |
|---|---|
| 월드 | `WORLD_mr0ou29f_P5XI47` (누가 내 케이크 먹었어?) |
| 맵 | `MAP_msysua8z_CKYO` (셰어하우스 40×30) |
| 타일 테마 | `SMO_msysgdda_X079` (셰어하우스 인테리어, 173타일) |
| 캐릭터 | 오물오물 `CHAR_msyjmqx3_UOXG` · 새침이 `CHAR_msyjkgad_61WB` · 살살이 `CHAR_msyjmqx4_HK5E` · 꾸벅이 `CHAR_msyjmqx4_258C` · 폴짝이 `CHAR_msyjmqx4_BSQ0` |

**방 좌표(맵 기준)**: 오물오물 `6,5` · 폴짝이 `19,4` · 새침이 `33,5` · 살살이 `6,24` · 꾸벅이 `33,24` · 거실 `19,14` · 부엌 `19,25`

## 5. 알려진 이슈

1. **캐릭터 스프라이트 2/5만 고유** (세션 2에서 재확인 — 3/5가 아니었다) — Cast Export가 직전 캐릭터 시트를 내려받고(A-4), 썸네일은 외형 수정이 반영 안 됨(A-5). 해결책: Cast Editor에서 각 캐릭터를 UI로 한 번씩 편집→저장해 썸네일 재생성 후 추출.
2. **타일 원본이 192×192(셀 12px)** — 확대 시 거칠다. 필요하면 Object Editor에서 고해상도 재생성.
3. **월드 캐스트 spawn 좌표가 옛 맵 기준** — 코드로 바꿔도 앱이 되돌린다(A-2). World Editor에서 드래그로 옮길 것.
4. **SPUM 세션 30분 만료** — 자동 복구 절차는 `work-rules.md` A-3.

## 6. 계정/비용

- SPUM/SAM 계정: `yy0977@naver.com` · 플랜 `creator_pro` / SAM `builder`
- SSAM 잔량: 약 **44,220 / 45,000** (이번 달 $0.70 사용) — 넉넉함
- SAM MCP(`/mcp`)는 **연결 성공했으나 SPUM 조작 툴이 아님**(웹검색·페이지열기·사용량). 게임과 무관 — 더 파지 말 것.
