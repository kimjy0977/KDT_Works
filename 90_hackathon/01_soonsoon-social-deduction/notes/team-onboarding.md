# 팀원 인수인계 — 이 환경 그대로 쓰는 법

> 이 문서 하나만 따라가면 같은 환경이 팀원 PC 에서 그대로 돌아간다.
>
> **사람은** §0(30초 요약)부터, **AI 세션은 §0-A 부터** 읽는다.

---

## 0-A. ⛔ AI 에이전트에게 — 먼저 읽을 것

> 이 문서는 사람과 **AI 세션이 함께** 읽는다. 아래는 AI 가 지켜야 할 규칙이다.
> 사람이 읽을 때는 "내 AI 에게 이걸 시키면 안 되는구나"로 읽으면 된다.

### 읽는 순서

1. `../CLAUDE.md` (과제 하네스) → 2. `notes/work-rules.md` (함정) → 3. 이 문서 §4 (SPUM 조작)
4. 그다음 필요한 것만 `docs/README.md` 문서 지도로 찾는다

### 💸 돈이 나가는 동작 — **사용자 확인 후에만**

SAM/SSAM 크레딧은 **로그인한 사람의 실제 계정**에서 빠진다. 다음은 묻고 하라.

| 동작 | 대략 비용 |
|---|---|
| Object Editor 평면도 생성 | **약 130 크레딧/장** |
| Cast Editor 시트 생성 | 장당 소량 (12장에 수백) |
| World 시뮬레이션 `Play` | 디렉터가 주기적으로 돈다 — **켜 두면 계속 나간다** |
| NPC 대사 1줄 | 1.5~2 |

- **루프로 생성하지 말 것.** 실패하면 원인을 찾고, 재시도는 사용자에게 알린 뒤 한 번씩.
- World 시뮬레이션은 확인이 끝나면 **`Pause` 로 반드시 끈다.**

### 🚫 비가역 — 사용자 승인 없이 하지 말 것

- SPUM **캐릭터·테마·맵·월드 삭제**, 이름 변경
- `localStorage` / `IndexedDB` **키 삭제** (그림이 거기 들어 있다 — 실제로 맵을 한 번 잃었다)
- 서버 스냅샷 **롤백**(옛 리비전 로드)
- git `force push` · history 재작성 · 브랜치 삭제
- `.env`, `_local/` 건드리기

> 일상 `commit`·`push` 는 자율이다. **되돌리기 어려운 것만** 승인을 받는다.

### 🔑 키 취급

- `SAM_API_KEY` 를 **출력·로그·커밋 메시지에 절대 쓰지 않는다.** 접두사도 안 된다.
- 값 확인이 필요하면 **길이나 존재 여부만** 확인한다 (`echo ${#SAM_API_KEY}`).
- 이 레포는 **PUBLIC** 이다. 커밋 전에 "공개돼도 되나" 1초 자문.

### ✅ 검증 규율

- **"코드를 고쳤다"와 "효과가 있다"는 다르다.** 화면·수치로 확인하고 보고한다.
- 확인 안 한 건 "확인 안 됨"이라고 말한다. 7/7 이면 7/7, 2/5 면 2/5.
- 검증은 가능하면 **결정론적으로.** 우연히 마주치길 기다리지 말고 좌표를 옮겨서 확인한다.

### 🖥 환경 전제

- 브라우저는 **`claude-in-chrome`(실제 크롬)** 을 쓴다. 앱 내장 브라우저는 로그인 세션이 없다.
- **크롬 창이 화면 앞에 있어야** 하는 작업이 있다(시트 생성). 작업 중 창을 덮지 않게 사용자에게 미리 알린다.
- SPUM 세션은 **30분에 만료**된다. `/api/me` 가 `{"user":null}` 이면 만료 — §4-4 표의 4번대로 복구한다.


---

## 0. 30초 요약

```bash
git clone <이 레포> && cd 90_hackathon/01_soonsoon-social-deduction
cp .env.example .env          # SAM_API_KEY 를 넣는다
bash serve.sh
```

**이 폴더에는 게임이 둘이다.** 서버가 뜨면 세 주소를 다 찍어 준다.

| | 주소 | 무엇 |
|---|---|---|
| **마피아 판** | `localhost:5173/mafia.html` | **발표·배포작.** 회사에 보이는 것은 이쪽 |
| 케이크 판 | `localhost:5173/game.html` | 과제 제출본 |
| 다시보기 | `localhost:5173/replay.html` | 지난 판 재생 · **AI 호출 0회** |

게임만 돌리려면 여기까지면 끝이다. **SPUM Studio 로 에셋을 만들려면 §4 를 읽는다.**

---

## 1. 무엇이 레포에 있고 무엇이 없나

**레포는 PUBLIC 이다.** 공개돼도 되는 것만 들어 있다.

| | 레포에 | 로컬에만 |
|---|---|---|
| 게임 코드 · 에셋 · 문서 | ✅ 전부 | |
| 세션 하네스(`CLAUDE.md` 2개) | ✅ | |
| SAM API 키 | ❌ **절대 금지** | `.env` (gitignore) |
| 회사 제공 원본(과제정의서 등) | ❌ | `_local/` (gitignore) |
| SPUM Studio 데이터 | ❌ | 브라우저 + SPUM 서버 계정 |

> `.env.example` 과 `README` 의 `sam-...` 은 **플레이스홀더**다. 진짜 키가 아니다.

---

## 2. 준비물

| | 필요한 것 | 확인 |
|---|---|---|
| Node.js | 18+ | `node -v` |
| SAM API 키 | 대화 기능에 필수 | 키가 없으면 맵·이동·캐릭터만 동작 |
| SPUM 계정 | **에셋을 만들 때만** | 게임 실행에는 불필요 |

키 넣는 법 — 둘 중 하나:
```bash
# ① .env (권장)
cp .env.example .env
# SAM_API_KEY=sam-... 를 채운다

# ② 환경변수
export SAM_API_KEY=sam-...
```

⚠ **`.env` 를 커밋하지 말 것.** 과제정의서 §8 제약이고, 레포가 공개다.

---

## 3. 세션 하네스 — Claude 에게 규칙을 주는 방식

이 프로젝트는 **하네스 2단 구조**다. Claude Code 로 폴더를 열면 자동으로 읽힌다.

```
90_hackathon/CLAUDE.md                       ← 공통 (페르소나·보안·git·도구 함정)
90_hackathon/01_soonsoon-social-deduction/
  CLAUDE.md                                  ← 이 과제 전용 (성공기준·아키텍처·함정)
```

**팀원이 할 일은 없다.** 폴더를 열기만 하면 된다. 다만 두 가지는 알아 둘 것:

- **작업 디렉터리를 `90_hackathon/` 안으로 둔다.** 밖으로 나가면 다른 세션(튜터·매니저)의 스코프다.
- **하네스를 고치면 팀 전체에 적용된다.** 새 함정을 배웠으면 `notes/work-rules.md` 에 적고,
  하네스에는 요약 + 포인터만 남긴다(문서 지도 = `docs/README.md`).

---

## 4. SPUM Studio 를 쓰는 실제 방식 ★

**여기가 이 프로젝트의 특이점이다.** SPUM 은 공개 API 도 MCP 도 없다.
그래서 **브라우저 안에서 코드를 실행**해서 다룬다. 손으로 클릭하는 건 최소한이다.

### 4-1. 도구 구성

| 방식 | 무엇에 쓰나 | 비중 |
|---|---|---|
| **페이지 내 JS 실행** | `localStorage`/`IndexedDB` 직접 조작, 버튼 호출, 루틴 심기 | **대부분** |
| **SPUM 내부 HTTP API** | `/api/me` · `/api/studio/state` · `/api/studio/revisions` | 진단·저장 |
| 실제 마우스 클릭 | 좌표로만 잡히는 것 (탭 전환, refs 카드) | 필요할 때만 |
| 번들 리버스 | `studio/main.js` 를 받아 내부 함수·엔드포인트 파악 | 막힐 때 |

> **브라우저는 `claude-in-chrome`(실제 크롬)을 쓴다.** 앱 내장 브라우저는 로그인 세션이
> 없어서 SPUM 에서 아무것도 못 한다. 증상이 "권한 차단"처럼 보여도 원인은 이것이다.

### 4-2. React 입력에 값을 넣는 법

SPUM UI 는 React 다. `el.value = x` 는 **무시된다.** 네이티브 setter 를 써야 한다.

```js
const w = document.querySelector("iframe").contentWindow;   // Object Editor 는 iframe 안
const setV = (el, v, proto) => {
  Object.getOwnPropertyDescriptor(proto, "value").set.call(el, v);
  el.dispatchEvent(new (w.Event)("input",  { bubbles: true }));
  el.dispatchEvent(new (w.Event)("change", { bubbles: true }));
};
setV(textarea, 프롬프트, w.HTMLTextAreaElement.prototype);
setV(input,    "우주선",  w.HTMLInputElement.prototype);
```

### 4-3. 반복 작업은 페이지에 함수를 심는다

스프라이트 12장을 뽑을 때 쓴 방식이다. 손으로 12번 클릭하지 않는다.

```js
window.__뽑기 = async function (이름, anim) {
  캐릭터_행.click();                        // 목록에서 선택
  setV(select, anim, ...);                  // IDLE / MOVE
  Generate.click();
  while (!/Sheet ready/.test(문서텍스트)) await 대기(700);
  PNG_JSON.click();                         // 다운로드
};
await __뽑기("오물오물", "idle");
await __뽑기("살살이",   "move");
```

### 4-4. 반드시 알아야 할 함정 5개

| # | 함정 | 대응 |
|---|---|---|
| **1** | **숨은 탭에서 시트 생성이 멈춘다** (`4/15` 에서 정지) | 크롬 창을 **화면 앞으로**. `document.visibilityState === "visible"` 이어야 한다. rAF 를 setTimeout 으로 바꿔도 안 된다 |
| **2** | **Export 파일명과 내용이 다른 캐릭터다** | 파일명 = 다운로드 시점 선택, 내용 = 생성 시점 캐릭터. **JSON 의 `characterName` 을 읽어 저장**할 것 |
| **3** | **refs 썸네일 클릭이 슬라이스 기준을 바꾼다** | 읽기 전용이 아니다. 클릭 전에 `sliceBaseAssetId` 를 적어 둘 것 |
| **4** | **세션이 30분에 만료된다** | 배지 → ACCOUNT → 「다시 로그인」. **페이지가 리로드된다**(약 10~25초). 화면에 심어둔 것은 다 날아간다 |
| **5** | **img2img 출력은 항상 1024×1024** | 격자는 1024 를 정수로 나누는 값만(16·32·64·128). 60×40 같은 건 그대로 안 된다 |

전체 목록은 `notes/work-rules.md`(A~K절)과 `notes/sam-connection-guide.md`(§4-1~4-21).

### 4-5. 계정·비용 주의

- **로그인한 사람의 실제 SPUM 계정으로 돌아간다.** SSAM 크레딧이 실제로 소모된다.
- 평면도 1장 생성 ≈ 130 크레딧 · 캐릭터 시트 1장 ≈ 소량 · NPC 대사 1줄 ≈ 1.5~2 크레딧
- **각자 계정을 쓰려면** SPUM Studio 에 로그인만 바꾸면 된다. 게임 코드는 계정과 무관하다.

---

## 5. 서버 저장이 막혔을 때

`studio_state_object_missing` 으로 저장이 안 되면 **`notes/work-rules.md` J-4** 를 따른다.

원인은 서버가 아니라 **클라이언트 교착**이다 — 읽기가 500 이면 쓰기가 영영 안 켜진다.
실제로 이 방법으로 세 세션 동안 막혀 있던 저장을 풀었다.

⚠ **안전 조건 3개를 반드시 지킬 것.** 어기면 로컬 작업이 서버 것으로 덮여 사라진다.

1. **먼저 백업**한다 — ACCOUNT → 「내 Studio 데이터 다운로드」
2. 가로채는 응답의 `state.keys` 는 **반드시 비워 둔다**(`{}`). 서버에 데이터가 있는 것처럼
   꾸미면 `_replaceStudioData()` 가 발동해 **로컬을 서버 것으로 덮어쓴다.**
3. **`PUT` 은 절대 가로채지 않는다.** 실제로 올라가는 건 로컬 원본이어야 한다.

**무거운 작업 전후로 ACCOUNT → 「내 Studio 데이터 다운로드」를 눌러 둘 것.**

---

## 6. 문서 지도 — 무엇을 어디서 찾나

| 알고 싶은 것 | 볼 곳 |
|---|---|
| 이 게임이 뭘 하려는 건가 | `notes/game-spec.md` |
| 지금 어디까지 됐나 | `notes/handoff.md` (맨 위 절이 최신) |
| SPUM/SAM 조작법·스키마 | `notes/sam-connection-guide.md` |
| 밟으면 안 되는 함정 | `notes/work-rules.md` |
| 엔진으로 뭐가 되고 안 되나 | `notes/engine-capability-audit.md` |
| 외부에 보여줄 구현기 | `docs/tutorial.md` |
| 회사에 전달할 제품 피드백 | `notes/spum-feedback.md` |

**새로 알게 된 건 한 곳에만 적고 나머지는 링크한다**(`docs/README.md` 의 규칙).

---

## 7. 팀원이 바로 해볼 것 (체크리스트)

- [ ] `bash serve.sh` 로 게임이 뜨는가
- [ ] 시작 화면에서 **참여 / 관전** 둘 다 눌러 보기
- [ ] 캐릭터를 고르고 역할 카드가 뜨는가
- [ ] `M` 으로 전체맵이 열리는가
- [ ] NPC 두 명이 가까워졌을 때 말풍선이 뜨고 **우하단 「엿들은 말」에 쌓이는가**
      (멀면 안 쌓이는 게 정상 — 가까이 가야 들린다)
- [ ] 토론 단계에서 전체 채팅이 열리고 NPC 들이 답하는가
- [ ] 투표 → 판정까지 가는가

여기까지 되면 환경이 제대로 선 것이다. 안 되면 브라우저 콘솔을 먼저 볼 것 —
부팅 실패는 화면 하단에 빨간 상자로 전문이 찍힌다.
