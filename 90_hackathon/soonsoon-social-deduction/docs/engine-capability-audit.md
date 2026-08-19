# SPUM 제공자료 기능 감사 — "엔진으로 뭐가 되고 뭐가 안 되나"

> 2026-08-19 세션 2. **소스를 직접 열어서 확인한 것만** 적었다. 추측은 `[추정]` 표기.
> 목적: 기획한 기능을 SPUM으로 얼마나 덮을 수 있는지 확정해 헛수고를 막는다.

---

## 0. 결론 3줄

1. **시야 제한(fog of war)은 엔진에 없다.** 만들려면 직접 짜야 한다.
2. 대신 **AI NPC 이동(A* 길찾기) · 말풍선 · 관계기억 · 대화 세션 모델은 이미 제공된다.** 우리가 짤 필요 없다.
3. **`packages/spum-world` 를 그동안 안 쓰고 있었다.** 과제 제공자료의 "개발 트랙 필수" 항목인데 미러링조차 안 돼 있었다 → 이번에 받아 뒀다(23파일).

---

## 1. 제공 패키지 두 개

| 패키지 | 정체 | 우리 상태 |
|---|---|---|
| `packages/spum-engine` | 2D 렌더링 SDK (Unity식 Entity-Component) · 65파일 | ✅ 미러 + P0에서 사용 중 |
| `packages/spum-world` | 월드 런타임 — 대화·관계·발화연출 모듈 · 23파일 | ✅ 이번에 미러 (아직 미사용) |

---

## 2. 기획 요구사항 ↔ 엔진 지원 여부

| 우리가 필요한 것 | SPUM이 주는가 | 근거 (직접 확인) |
|---|---|---|
| 타일맵 렌더 | ✅ 있음 | `TileSet` · `TileMapSystem` · `TileMapRenderer` (청크 캐싱·뷰포트 컬링) |
| 캐릭터 이동 | ✅ 있음 | `InputManager` (document 바인딩, `isKeyDown(code)`) |
| 벽 충돌 | ⚠️ 반쪽 | `Collider`/`CollisionSystem` 은 **엔티티끼리** 충돌용. 타일 벽은 `obstacle` 레이어를 직접 보는 게 맞다(P0에서 그렇게 함) |
| **AI NPC 자동 이동** | ✅ **있음 (큰 이득)** | `PathfindingManager.buildFromTileMap()` → **타일맵에서 길찾기 격자를 자동 생성**. `NavAgent.setDestination(x,y)` 로 A* 이동. `astarFindPath` |
| **말풍선** | ✅ **있음** | `BubbleRenderer` — speech/thought/shout/whisper 4종 + 감정별 색 + 타이핑 애니메이션. `bubble.show('speech','...',4)` |
| 발화 연출(겹침 방지·타이밍) | ✅ 있음 | spum-world `WorldSpeechDirector` + `BubbleLayout` (풍선 겹침 자동 배치, 표시시간 1.8~5.6초) |
| **대화 맥락/관계 기억** | ✅ 있음 | spum-world `RelationshipMemory` (trust·familiarity·tension·affinity + 요약) · `ConversationModel` (세션 opening→active→closing→closed, 제안 수락/거절/보류) · `ConversationStorage` |
| 머리 위 수치 표시 | ✅ 있음 | `FloatingTextRenderer` · `ProgressBarRenderer` |
| 파티클·이펙트 | ✅ 있음 | `ParticleSystem` · `EffectManager` |
| 카메라 | ⚠️ 반쪽 | `Camera`(줌·클램프·좌표변환)는 있으나 **`CameraController` 는 마우스 줌/팬 전용 — 추적 기능 없음.** 추적은 직접 구현(P0에서 `FollowCamera` 작성) |
| **시야 제한 / 안개** | ❌ **없음** | `fog`·`vision`·`sight`·`reveal`·`occlusion` 전수 검색 → **실질 0건**. 유일한 `_hasLineOfSight` 는 `PathfindingManager` 내부의 경로 다듬기용 private 함수 |
| 걷기 애니메이션 | ⚠️ 조건부 | `Animator`·`CharacterRenderer` 는 있으나 **SPUM 캐릭터 슬롯 파츠 JSON**이 필요. 우리가 가진 건 단일 초상 PNG뿐 → 현재 `SpriteRenderer` 정지 이미지 |
| 밤/낮 조명 | ❌ 없음 | 조명 시스템 없음. 화면 위에 어두운 사각형 덮기로 충분(v1이 그렇게 했음) |
| 저장/재개 | ✅ 있음 | `Scene.toJSON()/fromJSON()` · `Project` · spum-world `ConversationStorage` |

### 시야 제한을 굳이 만든다면 (엔진 기능 없음 → 자작)
`Renderer` 를 상속한 컴포넌트를 `sortingLayer` 높게 두고 화면 전체를 어둡게 덮은 뒤,
플레이어 주변만 `globalCompositeOperation='destination-out'` 로 뚫는 방식이면 된다. **[추정] 반나절.**
같은 방 판정은 `map.json` 에 방 ID 레이어를 추가하면 정확해진다.

---

## 3. ⚠️ 그런데 — 시야 제한은 과제 요건이 아니다

`tabs.html`(과제정의서·발표 원문에서 도출한 팀 정리본)을 확인한 결과:

- **성공기준 4개**: 브라우저 즉시 실행 · NPC 3명+ 성격 대화 · **대화 맥락 유지** · 기술문서 1편
- **보너스 목록**: 플레이어가 도둑일 때 / 관전 맵+시점 카메라 전환 / 긴급회의(NPC 대질) / 표정·외형 변화
- 원문: **"기능 수보다 대화의 질 우선. 데모는 3~5명이면 요건 충족"**

→ **시야 제한은 성공기준에도 보너스에도 없다.** `game-spec.md` §1이 "핵심"이라 쓴 건 우리 팀 자체 기획이다.
채점 기여도로 보면 **대화의 질 > 시야 제한**.

---

## 4. ❌ 요건 대비 빠진 것 (감점 포인트 — 코드와 무관하게 깎인다)

| 요건 | 현재 | 조치 |
|---|---|---|
| `bash serve.sh` 로 구동 | ❌ 없음 | 실행 스크립트 추가 |
| MIT `LICENSE` 파일 | ❌ 없음 | 추가 |
| `README.md` (루트) | ❌ 없음 | 추가 (`proto/README.md`만 있음) |
| SAM 키 `.env` · 커밋 금지 | ⚠️ 절반 | 키는 커밋 안 됨(✅)이나 `~/.claude.json` 에서 읽는다. 요건 문구는 `.env` → `.env` 지원 + `.env.example` 추가 권장 |

---

## 5. 이 감사로 바뀌는 계획

- **버릴 것:** 시야 제한 최우선 순위. (하려면 나중에, 여유 있을 때)
- **가져올 것:** `PathfindingManager` + `NavAgent` 로 AI 4명 이동 — 직접 짜려던 걸 엔진이 준다.
  `BubbleRenderer` 로 말풍선 — 직접 짜려던 걸 엔진이 준다.
- **유지:** 대화 로직은 **SAM 직접 호출**. spum-world 의 대화 모듈은 *구조*(관계·세션)만 빌려 쓰고,
  생성은 SAM 이 한다. (World 내장 AI는 `systemPrompt` 무시 — `game-spec.md` §6에서 검증됨)

---

## 6. 세션 3 추가 조사 (2026-08-19) — 스프라이트·프롭

> 스프라이트 애니메이션과 맵 완성도를 올리려고 다시 팠다. **소스를 직접 열어 확인한 것만** 적는다.

### 6-1. ❌ `Animator` 로는 스프라이트 시트를 못 돌린다 ★★★★★

`Animator` 는 **스켈레톤 파트 애니메이터**다 — `_animParts`, 쿼터니언 회전, 파트 경로(`_buildPartPath`)
기반이라 **SPUM 캐릭터 슬롯 파츠 JSON** 을 요구한다. 우리가 가진 것은 프레임 스프라이트 시트다.

```
새침이_idle.json / 폴짝이_idle.json
  frameWidth 128 · columns 8 × rows 2 · totalFrames 15 · fps 30 · background "transparent"
```

### 6-2. ❌ `SpriteRenderer` 는 이미지 일부만 그릴 수 없다 ★★★★★

`SpriteRenderer.js:164` 가 `ctx.drawImage(image, dx, dy, dw, dh)` — **source rect 인자가 없다.**
`ImageRenderer` 도 같다. 즉 시트에서 한 프레임만 잘라 그리는 기능이 엔진에 **없다.**

→ **결론: 시트 재생 컴포넌트를 직접 만들어야 한다.**
`Renderer` 를 상속해 `drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh)` 9인자 형태를 쓰면 된다.
프레임 인덱스 = `floor(t * fps) % totalFrames`, `sx = (i % columns) * frameWidth`,
`sy = floor(i / columns) * frameHeight`. **[실측] 30줄 안쪽.**

> 이건 엔진 결함이 아니라 **설계 방향**이다. SPUM 은 스켈레톤 파츠 캐릭터가 정공법이고,
> 시트는 Cast Editor 의 **추출물**(외부 반출용)이다. 다만 추출물을 다시 엔진에 넣는
> 경로가 비어 있다 — **회사에 전할 만한 피드백.**

### 6-3. ✅ SPUM 맵은 오브젝트(프롭)를 담을 수 있다 ★★★★★

`spum-world/core/WorldCastSync.js:328 runtimeObjectsForMap()` · `WorldObjectModel.js:135`
확인 결과, 맵 데이터에 **`objects[]` 배열**이 있다.

```
map.objects[] = { id, name, rect:{ x, y, w, h }, collider?:boolean, radius?:number }
   → mapObjectToWorldObject() 가 Transform + Collider 컴포넌트를 붙여 GameObject 로 만든다
   → 배치 좌표는 rect 의 중심 타일 (col + floor(w/2), row + floor(h/2))
```

**우리 `assets/map.json` 에는 이 배열이 아예 없다.** 냉장고·케이크 접시 같은 프롭을 여기에
정의하면 상호작용 지점을 데이터로 관리할 수 있다(지금은 부엌 F 키가 보이지 않는 좌표 판정).
※ Map Editor 에 오브젝트 배치 UI 가 있는지는 **아직 미확인** — Studio 조사 항목.

### 6-4. `spum-world` 는 장르 킷을 갖고 있다 ★★★★☆

`GenreKit.js` — `village-sim` · `rpg` · `platformer` 3종. 각 킷이 컴포넌트 스키마와
`castToGameObject` 를 제공한다. 컴포넌트 종류(`WorldComponentModel.js`):
`Transform · Renderer · MapData · MapRenderer · Collider · PhysicsBody · NavAgent ·
Motion · FSM · Brain · Memory · Dialog · Effects · ObjectInfo · StateInfo`

우리 게임은 이 중 Transform·Renderer·Collider·NavAgent 에 해당하는 것을 **직접 구현**했다.
`village-sim` 킷을 쓰면 겹치는 부분이 있다 — **다만 Dialog/Brain 은 §5 한계로 못 쓴다.**

### 6-5. `TileMapRenderer` 는 sortingLayer 를 하나만 가진다 ★★★★★

타일맵 하나에 레이어를 여러 장 넣어도 **렌더러가 한 덩어리로 그린다.** 즉 캐릭터를
레이어 사이에 끼울 수 없다. 캐릭터 앞에 덮개(front)를 그리려면
**타일맵 GameObject 를 앞/뒤 두 개로 갈라야 한다.**

```js
buildTileMap("tilemap-back",  backLayers,  -100);   // 바닥·러그·가구
// 캐릭터 sortingLayer 10 · 이름표 20
buildTileMap("tilemap-front", frontLayers,   15);   // 캐릭터 앞, 이름표 뒤
```

### 6-6. ⚠ 우리 타일 시트로는 `front_1` 을 채울 수 없다 (한계 · 정직 기록)

깊이감이 나오려면 **캐릭터가 지나갈 수 있는 칸 위에 걸치는 그림**이 필요하다.
그런데 우리 시트의 가구는 **불투명한 완성 도면**이고, 가구가 놓인 칸은 전부 `obstacle` 이라
캐릭터가 애초에 들어가지 못한다 → front 로 올려도 가려질 캐릭터가 없다.

**front_1 이 실제로 효과를 내려면 새 타일이 필요하다** — 문틀 상인방(lintel), 아치,
키 큰 가구의 윗부분처럼 **반투명하거나 위쪽만 잘린** 조각. 이건 Object Editor 작업이다.
→ 지금은 레이어 자리만 만들어 두고 비워 뒀다(`front_1` 이 비면 렌더러를 아예 안 만든다).
