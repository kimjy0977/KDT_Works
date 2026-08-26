# 설정 화면·오디오 — 레퍼런스 조사와 구현 계획 (2026-08-24)

> 「다른 게임은 설정에 뭘 넣고 어떻게 구성했나」를 **실제로 찾아보고** 적었다.
> 출처는 맨 아래. 우리 코드와 대조해서 **뭘 넣고 뭘 안 넣을지**까지 정한다.

---

## 1. 레퍼런스 — 실제 구성

### 1-1. Terraria (가장 상세)

**오디오는 슬라이더 3개뿐이다. 마스터 볼륨이 없다.**

| 항목 | 형태 | 기본값 |
|---|---|---|
| Music | 0–100% 슬라이더 | 100% (콘솔·모바일 75%) |
| Sound | 0–100% 슬라이더 | 100% |
| Ambient | 0–100% 슬라이더 | 100% (콘솔·모바일 75%) |

> ⭐ **우리에게 주는 교훈:** 마스터를 안 두고 **음악/효과음/환경음 3분할**만 한다.
> 슬라이더가 적을수록 고르기 쉽다. 우리는 환경음이 없으므로 **2개면 충분**하다.

**인터페이스 쪽에 우리가 이미 가진 것과 겹치는 항목이 있다:**

| Terraria | 형태 | 우리 상태 |
|---|---|---|
| **UI Scale** | 50–200% 슬라이더 | ✅ 있음 (`UI배율` 0.8–2.2×) |
| **Zoom** | 100–200% 슬라이더 | ✅ 있음 (드래그 줌) |
| Map Scale | 50–100% | — (미니맵 있음) |
| **Screen Shake** | 켜기/끄기 | ⛔ 없음 — **접근성 항목이다** |
| Blood and Gore | 켜기/끄기 | ⛔ 없음 — 우리 게임엔 살해 연출이 있다 |
| Hover Text Boxes | 켜기/끄기 | — |
| Autopause | Never / Menus / Inventory&Menus | ⚠ 우리는 `#pause` 가 있다 |
| Language | 12개 | — (한국어 전용) |

### 1-2. Among Us (**같은 장르**라 제일 참고할 만하다)

탭 **3개**로 나눈다: `General` · `Graphics` · `Data`

| 항목 | 비고 |
|---|---|
| SFX 볼륨 / Music 볼륨 | 슬라이더 2개 — **여기도 마스터 없음** |
| **Censor Chat** | 채팅 필터 |
| Friend & Lobby Invites | 초대 수신 |
| ⭐ **Colorblind Text** | 캐릭터 위에 **색 이름을 글자로** 띄운다 |
| ⭐ **Streamer Mode** | 방송할 때 민감 정보를 가린다 |
| Language | |

> ⭐ **Colorblind Text 가 우리에게 그대로 필요하다.** 우리 게임은 캐릭터를 **색으로** 구분한다
> (`cast.js` 의 `color`, 지목판 칩, 이름표). 색각이상 플레이어는 지목판에서 누가 누군지 못 가린다.
> **이름을 항상 붙이는 옵션**이면 해결된다.

### 1-3. Core Keeper

설정을 메인 메뉴/일시정지 양쪽에서 연다. 음악 볼륨 조절이 있다.
> ⚠ **위키에서 전체 항목표를 확보하지 못했다**(문서가 패치노트 위주, 상세 페이지는 402 로 막힘).
> 이 항목은 **[미확인]** 으로 둔다. 위 둘로 결론을 내기에 충분하다.

### 1-4. 세 게임의 공통점

1. **마스터 볼륨을 안 둔다.** 음악·효과음 2~3개로 끝낸다.
2. **설정은 메인 메뉴와 일시정지 양쪽**에서 열린다.
3. **접근성이 별도 항목으로 있다** (색각·화면 흔들림·방송 모드).
4. 값은 **즉시 반영**되고 저장된다(적용 버튼이 없다).

---

## 2. 우리 현재 상태 — **절반은 이미 되어 있다**

`proto/src/settings.js` (134줄)

```js
const 항목 = [
  { 키: "글자배율", 이름: "글자 크기", … },
  { 키: "UI배율",   이름: "UI 크기",   … },
];
```

| 이미 있는 것 | |
|---|---|
| 선언형 항목 배열 | 배열에 한 줄 넣으면 슬라이더가 생긴다 |
| `localStorage` 저장·복원 | 판을 새로 시작해도 유지 |
| 범위 가두기(`가두기`) | 깨진 저장값도 안전 |
| 구독(`설정구독`) | 값이 바뀌면 화면이 따라온다 |
| 「기본값으로」 | |

**→ 음량 슬라이더 자체는 항목 배열에 두 줄 추가하면 끝난다.**
진짜 작업은 **소리를 내는 쪽**이다.

---

## 3. 오디오 구현 설계

### 3-1. 버스 구조 (Web Audio API)

```
   음악 소스 ──→ [음악 Gain] ─┐
                              ├─→ [마스터 Gain] ──→ destination
   효과음   ──→ [효과 Gain] ─┘
```

`GainNode.gain` = 1.0 이 원음, 0.0 이 무음. 슬라이더 값을 그대로 꽂으면 된다.
마스터 버스는 **화면에 노출하지 않는다**(레퍼런스 3종 다 없다). 대신 **음소거 토글**에 쓴다.

### 3-2. ⚠ 자동재생 정책 — **이게 제일 큰 함정이다**

브라우저는 **사용자 조작 없이 오디오를 시작하지 못하게 막는다.**
`AudioContext` 가 `suspended` 상태로 시작하므로, **클릭·키 입력 핸들러 안에서**
`audioContext.resume()` 을 불러야 한다.

> ✅ **우리는 이게 공짜다.** 타이틀 화면의 **「게임시작」 버튼**이 그 조작이다.
> 그 핸들러에서 `resume()` 하면 된다. 새 인프라가 필요 없다.

### 3-3. 소리를 어디에 붙일까 (우리 게임 기준)

| 장면 | 소리 | 왜 |
|---|---|---|
| 밤 시작 | 음악 전환(낮 ↔ 밤) | **단계 전환이 게임의 뼈대**다. 소리가 제일 크게 먹는 자리 |
| 살해 | 짧은 효과음 | 이미 대형 안내(`외침`)가 있다 — 거기 얹으면 된다 |
| 지목 칩이 날아가 붙을 때 | 딸깍 | 이미 FLIP 애니메이션이 있다 |
| 처형 발표 | 한 방 | |
| 잠자기 성공 | 부드러운 신호 | |

**낮/밤 2트랙이면 충분하다.** 트랙이 많을수록 용량과 로딩이 늘어난다.

### 3-4. 음원 조달 — **라이선스**

이 레포는 **공개**다. 출처가 불분명한 음원은 올릴 수 없다.

**CC0(퍼블릭 도메인)** 이면 저작자 표시 없이 상업적 사용까지 자유롭다.

| 출처 | 성격 |
|---|---|
| **OpenGameArt — CC0 Dark Music** | 「Oldschool Horror Theme」·「Loaben」·「Derelict」 3곡. mp3/ogg |
| **OpenGameArt — CC0 Background Ambience** | 환경음 |
| **Kenney** | 거의 전 팩이 CC0. 다만 **음악은 `Music Jingles` 뿐**이고 나머지는 효과음 |

> ⚠ **OpenGameArt 는 "자동 생성한 크레딧 파일이 정확하다고 보장하지 않는다"** 고 명시한다.
> 곡마다 **개별 라이선스를 직접 확인**하고, `assets/audio/LICENSE.md` 에 출처·라이선스를 적는다.
> CC0 라도 **출처를 남기는 게 안전하다.**
>
> ⛔ **음원 선택은 내가 단독으로 정하지 않는다** — 주영님이 듣고 고르시는 게 맞다.
> 「으스스하되 무섭지 않게」는 취향 판단이다.

### 3-5. 파일 형식·용량

- **ogg** 우선(용량 대비 품질). 사파리 호환이 필요하면 **m4a/mp3** 를 같이 둔다.
- 음악은 **루프**로 만든다(`loop = true`). 30~60초면 충분하다.
- ⚠ `serve.sh` 의 MIME 을 확인할 것 — `.ogg` 가 잘못 나가면 재생이 안 된다(공통함정 8-5).

---

## 4. 우리가 넣을 항목 — 우선순위

### 지금 넣을 것

| # | 항목 | 형태 | 근거 |
|---|---|---|---|
| 1 | **음악 음량** | 0–100% | 레퍼런스 3종 공통 |
| 2 | **효과음 음량** | 0–100% | 〃 |
| 3 | **음소거** | 켜기/끄기 | 마스터 게인으로 구현. 슬라이더를 0으로 끌 필요 없이 한 번에 |
| 4 | ⭐ **이름 항상 표시**(색각 보조) | 켜기/끄기 | Among Us `Colorblind Text`. **우리는 색으로 사람을 구분한다** |
| 5 | **화면 흔들림** | 켜기/끄기 | Terraria `Screen Shake`. 접근성 + 멀미 |

### 나중에 (필요해지면)

- 살해 연출 완화 (Terraria `Blood and Gore` 자리)
- 타이핑 속도 — 이미 `typing.js` 에 배속(1x/3x/즉시)이 있다. **설정으로 끌어올릴 수 있다**
- 언어

### 안 넣을 것

- **마스터 볼륨 슬라이더** — 레퍼런스 3종 다 없다. 음소거 토글로 대신한다
- 해상도·프레임 스킵 — 브라우저 게임에 해당 없음

---

## 5. 작업 순서

1. `src/audio.js` — 버스 구조 + `resume()` 배선 + 로드/재생 (**음원 없이도 뼈대는 완성 가능**)
2. `settings.js` 항목 배열에 음량 2개 + 토글 3개. **토글은 지금 슬라이더밖에 없어서 형태를 하나 늘려야 한다**
3. 음원 고르기 (**주영님 판단 필요**) → `assets/audio/` + `LICENSE.md`
4. 단계 전환·살해·지목에 소리 연결
5. 색각 보조·화면 흔들림 실제 반영

> **1·2 는 음원이 없어도 지금 할 수 있다.** 3 이 막혀도 나머지가 진행된다.

---

## 출처

- [Settings — Official Terraria Wiki](https://terraria.wiki.gg/wiki/Settings)
- [Settings — Among Us Wiki](https://among-us.fandom.com/wiki/Settings)
- [Among Us 접근성 옵션 — Innersloth Help Center](https://innersloth.zendesk.com/hc/en-us/articles/8531332682004-What-accessibility-options-are-available-in-Among-Us)
- [Settings — Core Keeper Wiki](https://core-keeper.fandom.com/wiki/Settings) *(전체 항목표 확보 실패)*
- [Web Audio API best practices — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Audio for Web games — MDN](https://developer.mozilla.org/en-US/docs/Games/Techniques/Audio_for_Web_Games)
- [CC0 Dark Music — OpenGameArt](https://opengameart.org/content/cc0-dark-music)
- [CC0 Background Ambience — OpenGameArt](https://opengameart.org/content/cc0-background-ambience)
- [All CC0 — Kenney, OpenGameArt](https://opengameart.org/content/all-cc0-uploader-kenney)
