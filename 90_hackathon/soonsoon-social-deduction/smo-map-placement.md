# 회신 — "SMO를 맵에 배치하는 방법" (METHOD.md 6번 항목)

> 최종우님 METHOD.md 잘 봤습니다. 정확도 높고, 제가 따로 파악한 내용과 거의 다 일치합니다.
> 막히신 **"라이브러리엔 있는데 맵에 안 보임"** 원인을 실제 계정 데이터를 뜯어서 확인했습니다.
> 2026-08-18 · 신뢰도: ★★★★★ 직접 확인 / ★★★☆☆ 추정 / ★☆☆☆☆ 미확인

---

## 1. 결론부터

**맵은 "라이브러리에 있는 SMO"를 그리지 못합니다.**
맵이 그릴 수 있는 건 **그 맵의 `tilesets[]`에 등록된 타일**뿐이고, 레이어에는 **숫자 타일 ID**만 들어갑니다.

```
SMO 라이브러리(sv_studio_smo_v1)  ──❌ 직접 연결 없음 ──▶  맵
                                   │
                                   └─ map.tilesets[]에 "map-theme"으로 등록되어야 함
                                      + tileProperties에 타일별 packed ID 부여
                                      + layers[].data[]에 그 ID를 써야 화면에 나옴
```

냉장고를 `category:"furniture"` 로 라이브러리에만 넣으면 **어떤 맵에도 등록된 적이 없으므로** 영원히 안 보입니다. 버그가 아니라 구조입니다.

---

## 2. 실제 데이터 (제 계정 `기본맵` 40×30) ★★★★★

### 2-1. `map.tilesets[]` — 맵이 쓸 수 있는 타일 출처 목록

| id | kind | source | themeId | **tileIdBase** | tiles | columns |
|---|---|---|---|---|---|---|
| `builtin_tp_tile01` | builtin | — | — | **1** | 0 | 0 |
| `theme_SMO_BUILTIN_STONE_WALL` | custom | `map-theme` | `SMO_BUILTIN_STONE_WALL` | **2049** | 118 | 16 |
| `theme_SMO_msydcapt_6LLF` | custom | `map-theme` | `SMO_msydcapt_6LLF` | **4097** | 256 | 16 |

- **`tileIdBase`는 2048 단위 블록으로 할당됩니다** — `1, 2049, 4097, …` (다음은 6145로 추정 ★★★☆☆)
- `source:"map-theme"`, `themeId` = **SMO의 id**. 이게 SMO ↔ 맵을 잇는 유일한 고리입니다.

### 2-2. `tileset.tileProperties` — 타일 ID → 의미

키가 **packed 타일 ID 문자열**입니다.

```json
"2050": {
  "smoThemeId": "SMO_BUILTIN_STONE_WALL",
  "smoThemeName": "기본 맵 데이터",
  "smoTileId": "1",
  "name": "floor 01",
  "category": "floor",
  "movement": "passable",
  "interaction": "none",
  "blocksMovement": false,
  "blocksVision": false,
  "moveSpeed": 1,
  "sourceCell": { "column": 2, "row": 1 },
  "sourceCells": [ ... ]
}
```

> 즉 **ID 계산을 직접 할 필요가 없습니다.** `tileProperties`를 읽으면 "이 숫자가 어느 타일인지"가 다 적혀 있습니다.

### 2-3. `map.layers[]` — 실제 그림

| name | type | data |
|---|---|---|
| `back_1` | back | **Array(1200)** — `[4097, 4098, 4099, …]` (사용 중, 고유값 237종) |
| `back_2` | back | Array(1200) — 전부 0 |
| `front_1` | front | Array(1200) — 전부 0 |
| `walkable` | walkable | Array(1200) — 전부 1 |

- **길이 = width × height** (40×30 = 1200), **평탄 배열**입니다.
- 인덱스 = `row * width + col`
- **`0` = 빈 칸**
- `walkable` 레이어는 `1` = 걸을 수 있음 (이동 판정 별도 레이어)

### 2-4. `map.objects[]` — 이건 SMO가 아님

최종우님 문서대로 맞습니다. `{id, name, tags, description, rect{col,row,width,height}, color}` 형태의 **단순 사각형 주석**이고, 제 맵에선 `[]` 비어 있습니다. SMO 배치와 무관합니다.

---

## 3. 그래서 어떻게 해야 하나

### ✅ 권장 — 지원되는 경로 (Object → Map 파이프라인) ★★★★☆

**냉장고를 "독립 가구 SMO"가 아니라 "맵 테마 안의 한 타일"로 만드세요.**

1. **Object Editor**에서 인테리어 테마 생성 (바닥/벽/가구가 한 시트에 들어간 타일셋)
2. Slice → 타일별 속성 지정 (냉장고 타일은 `TYPE=Wall`, `MOVE=Block` 등)
3. **Map Editor** → 우측 `MAP THEME TILES` → 그 테마 선택
   → 이 시점에 앱이 **`tilesets[]` 등록 · `tileIdBase` 할당 · `tileProperties` 생성**을 전부 해줍니다
4. 붓으로 칠하면 `layers[].data[]`에 ID가 들어가고 화면에 보입니다

이게 "왜 굳이"처럼 보여도, 위 2번 표의 모든 배선을 **앱이 대신 해주는 유일한 길**입니다.

### ⚠️ 비권장 — 코드로 강행 ★★★☆☆ (미검증, 취약)

이론상 가능은 합니다:
1. `map.tilesets[]`에 `{kind:"custom", source:"map-theme", themeId:"SMO_FRIDGE_KITCHEN01", tileIdBase:6145, columns, tiles[], tileProperties{"6145":{...}}}` 추가
2. `layers.back_1.data[row*40+col] = 6145`
3. 저장

**다만 렌더링에 필요한 "구운(baked) 테마 이미지"가 따로 있습니다.** localStorage에 이런 키들이 있어요:

```
spum-map-theme-source-state:SMO_msydcapt_6LLF   (215 KB)
spum-map-theme-export-seed:SMO_msydcapt_6LLF    (133 KB)
spum-map-theme-export-seed:SMO_BUILTIN_STONE_WALL (20 KB)
```

`tilesets`만 손으로 넣고 이 bake 산출물이 없으면 **화면에 안 뜰 가능성이 높습니다(★★★☆☆ 추정)**. 캐스트 배치와 같은 "정합성 정리" 로직이 맵에도 있는지는 **미확인 ★☆☆☆☆** 입니다. 시간 아끼시려면 3-1 경로를 권합니다.

### ❓ 미확인 — World Editor의 `Props` 슬롯 ★☆☆☆☆

World Editor 좌측 트리에 `Map / Characters / **Props** / Events / Spawn Points` 가 있습니다. 가구는 맵 타일이 아니라 **월드의 Prop**으로 배치하는 경로일 가능성이 있습니다. 제가 `+`를 눌러봤지만 다이얼로그가 안 떠서 **확인 못 했습니다.** (참고: 제 월드 draft에는 `mapObjects`/`propMeta` 필드가 아예 없었습니다 — 문서에 적으신 것과 차이가 있어 버전/상태 차이로 보입니다.)

**여기가 제일 먼저 찔러볼 만한 지점입니다.** 되면 tilesets 손댈 필요 자체가 없어집니다.

---

## 4. METHOD.md 검토 의견

### 확인 일치 ✅
- **`PUT /api/studio/state` 직접 쓰기 → 로컬이 덮어씀**: 완전히 동일하게 확인했습니다. 제 가이드에도 이 경고를 추가했습니다.
- **`cast[]` 직접 조작 금지**: 저도 당했습니다. 코드로 배치 ID를 만들었더니 *"없는/중복 캐릭터 배치 5개를 정리했습니다"* 로 전부 삭제되더군요. UI `+` 버튼이 정답입니다.
- **`talkConfig.systemPrompt` 런타임 무시**: 실제 심문 테스트로 확인했습니다. 아래 5번 참고.

### 유용했던 것 (제가 몰랐던 것) 👍
- **`saveServerSnapshot`의 dirty 체크 → `spum:studio-storage-write` 이벤트 dispatch**
  좋은 발견입니다. 참고로 제 환경에선 이벤트 없이 `saveServerSnapshot("커스텀사유")`만으로도 저장됐습니다(revision 51→52 증가 확인). 다만 **안전장치로 넣는 게 맞다**고 봅니다.

### 작은 정정 🔧
- `appearance.colors`는 `{eye, helmet}`가 아니라 **슬롯 전체**입니다:
  `eye, hair, armor, clothing, pants, facehair, weapon_right, helmet, weapon_left, body, back` (전부 hex)
  → 캐릭터 외형을 코드로 구분할 때 `hair`/`clothing`/`pants` 색만 바꿔도 확 달라집니다.
- 제 월드 `draft.world` 키는 `sceneCharacterIds, unitPixelScale, ai, mapId, mapResourceId, bakeBuilder, casts` 였습니다. `mapObjects`/`propMeta`는 없었습니다.

---

## 5. 공유 — World 내장 AI는 심문에 못 씁니다 (실측) ★★★★★

`talkConfig.systemPrompt` 무시 건, 저희가 실제로 심문을 돌려봤습니다.

- 범인 캐릭터에게 *"방에 있었다고 거짓말해라"* 지시 → 오히려 **"부엌 근처 돌며 냄새 맡고 수상한 발자국까지 봤지요"**
- 목격자는 기억에 있는 *"살살이를 봤다"* 대신 **"수상한 그림자 하나"**
- **기억에 없는 내용을 지어냅니다** (발자국·그림자)
- 캐스트 AI 패널은 **`Local FSM` 고정**, 설정이 `model / quality / 역할 / 목표` **4개뿐 — 시스템 프롬프트 입력란 자체가 없음**

**→ SPUM 내장 대화 = 앰비언트 NPC 애드립용.** 규칙 기반 심문(거짓말·모순·자백)은 **SAM `/v1/generate` 직접 호출**로 구현해야 합니다.

저희는 그렇게 구현해서 **검증 7/7 통과**했습니다. 코드는 레포에 있습니다:

```
90_hackathon/soonsoon-social-deduction/proto/
  engine.mjs    캐릭터 데이터 + 프롬프트 빌더 + SAM 호출
  server.mjs    로컬 서버(키를 클라이언트로 안 보냄)
  index.html    플레이 화면
  run.mjs       자동 검증 시나리오
```

실제로 이렇게 나옵니다:

```
[압박3] 꾸벅이도 자정쯤 냉장고 문 닫히는 소리를 들었대. 이래도 방에 있었다고 할 거야?
  살살이: *얼굴이 굳어지고 손이 떨린다*   내가... 내가 먹었어.
```

비용은 9턴에 SSAM 약 15 (턴당 ~1.7)로 저렴합니다.

---

## 6. 요약

1. **원인**: SMO는 `map.tilesets[]`에 `map-theme`으로 등록되어야만 맵이 그릴 수 있음. 라이브러리에만 있으면 안 보이는 게 정상.
2. **가장 빠른 해결**: 냉장고를 독립 SMO 말고 **맵 테마의 타일**로 만들어 Map Editor에서 칠하기.
3. **그다음 확인할 것**: World Editor의 **Props** 슬롯 (되면 제일 깔끔)
4. **하지 말 것**: `tilesets`/`layers` 손으로 조립 (bake 산출물 없이는 안 뜰 가능성 높음), `cast[]` 직접 조작, 서버 직접 PUT
5. **심문 로직은 SPUM 밖에서** — 이미 검증된 코드 있으니 가져다 쓰셔도 됩니다.
