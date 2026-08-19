# 세션 인계 — 「누가 내 케이크 먹었어?」

> 작성 2026-08-19 (세션 1 종료 시점) · 다음 세션은 **이 문서 → `work-rules.md` → `game-spec.md`** 순서로 읽는다.

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
| **게임 런타임** | ⚠️ **재작업 필요** — v1을 캔버스로 만들었으나 **SPUM Engine 기반으로 다시 만들기로 결정** |

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
├─ sam-connection-guide.md   팀 배포용 연결 가이드
├─ smo-map-placement.md      SMO/맵 구조 회신 문서
└─ proto/
   ├─ engine.mjs         캐릭터 데이터 + 프롬프트 빌더 + SAM 호출 (재사용)
   ├─ server.mjs         로컬 서버 + SAM 프록시 (키 미노출)
   ├─ run.mjs            자동 검증 시나리오 (7/7)
   ├─ index.html         v1 게임 화면(캔버스) — 엔진판으로 교체 예정
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
※ `mirror.mjs`는 스크래치에만 있으니 필요하면 다시 작성 (재귀 fetch + 상대 import 따라가기).

## 4. SPUM 리소스 ID (실계정)

| 항목 | ID |
|---|---|
| 월드 | `WORLD_mr0ou29f_P5XI47` (누가 내 케이크 먹었어?) |
| 맵 | `MAP_msysua8z_CKYO` (셰어하우스 40×30) |
| 타일 테마 | `SMO_msysgdda_X079` (셰어하우스 인테리어, 173타일) |
| 캐릭터 | 오물오물 `CHAR_msyjmqx3_UOXG` · 새침이 `CHAR_msyjkgad_61WB` · 살살이 `CHAR_msyjmqx4_HK5E` · 꾸벅이 `CHAR_msyjmqx4_258C` · 폴짝이 `CHAR_msyjmqx4_BSQ0` |

**방 좌표(맵 기준)**: 오물오물 `6,5` · 폴짝이 `19,4` · 새침이 `33,5` · 살살이 `6,24` · 꾸벅이 `33,24` · 거실 `19,14` · 부엌 `19,25`

## 5. 알려진 이슈

1. **캐릭터 스프라이트 3/5만 고유** — Cast Export가 직전 캐릭터 시트를 내려받고(A-4), 썸네일은 외형 수정이 반영 안 됨(A-5). 해결책: Cast Editor에서 각 캐릭터를 UI로 한 번씩 편집→저장해 썸네일 재생성 후 추출.
2. **타일 원본이 192×192(셀 12px)** — 확대 시 거칠다. 필요하면 Object Editor에서 고해상도 재생성.
3. **월드 캐스트 spawn 좌표가 옛 맵 기준** — 코드로 바꿔도 앱이 되돌린다(A-2). World Editor에서 드래그로 옮길 것.
4. **SPUM 세션 30분 만료** — 자동 복구 절차는 `work-rules.md` A-3.

## 6. 계정/비용

- SPUM/SAM 계정: `yy0977@naver.com` · 플랜 `creator_pro` / SAM `builder`
- SSAM 잔량: 약 **44,220 / 45,000** (이번 달 $0.70 사용) — 넉넉함
- SAM MCP(`/mcp`)는 **연결 성공했으나 SPUM 조작 툴이 아님**(웹검색·페이지열기·사용량). 게임과 무관 — 더 파지 말 것.
