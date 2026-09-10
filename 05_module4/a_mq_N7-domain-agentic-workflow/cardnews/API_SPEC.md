# API_SPEC — 카드뉴스 에이전트

> PRD 의 「웹 API 계약 초안」을 구현에 맞춰 확정한 것. 김주영 · 2026-09-09
> 서버는 `127.0.0.1` 에만 바인딩합니다. 기본 포트 **8765**(사용 중이면 +1씩 올려 안내).

## 규칙 — 모든 엔드포인트에 공통

- **긴 요청 하나로 끝내지 않는다.** 오래 걸리는 일은 `{ok, runId, status:"running"}` 을 «즉시» 돌려주고
  화면이 `GET /api/projects/{id}` 로 폴링한다.
- **변경 요청은 `requestId` 로 중복을 막는다.**
  같은 ID·같은 입력 → **저장한 결과를 그대로** 반환 · 같은 ID·다른 입력 → `409 request_conflict`
- **버전 검사.** 선택은 `selectionVersion`, 답변은 `questionId`+`version`, 승인은 스토리보드 `version`.
  어긋나면 `409` 로 거절하고 **현재 작업을 덮어쓰지 않는다.**
- 오류는 `{error, message}` 와 함께 **다음에 할 수 있는 것**(`retry`)을 상태에 남긴다.

## 엔드포인트

| 요청 | 입력 | 결과 | 실패 |
|---|---|---|---|
| `GET /api/health` | — | `{engine, font, antigravity, port}` | — |
| `GET /api/projects` | — | `{projects:[…]}` | — |
| `POST /api/projects` | `{topic, periodDays}` | `{projectId}` | `400 topic_required` |
| `GET /api/projects/{id}` | — | **상태 전부**(아래) | `404 not_found` · `400 bad_id` |
| `POST …/research` | `{widen?, requestId}` | `{ok, runId, status}` | `409 already_running` |
| `POST …/selection` | `{candidateIds[1..3], version}` | `{ok, selection, version}` | `409 stale_version` · `400 bad_count` · `400 unknown_candidate` |
| `POST …/deep` | `{requestId}` | `{ok, runId}` | `400 no_selection` |
| `POST …/answers` | `{questionId, version, answer, requestId}` | `{ok, accepted}` | `409 no_question` · `409 stale_question` · `400 empty_answer` |
| `POST …/storyboard` | `{cards:3..8, requestId}` | `{ok, runId}` | — |
| `POST …/approve` | `{stage:"storyboard"\|"final", version, requestId}` | `{ok, producing}` 또는 `{ok, exports}` | `409 stale_version` · `400 no_storyboard` · `400 no_cards` |
| `POST …/revisions` | `{cardNo, title?, body?}` | `{ok, render, backgroundUnchanged, otherCardsUnchanged}` | `400 card_required` |
| `GET …/exports` | — | `{zip, zipBytes, cards[], manifest}` | **`409 not_approved`** |
| `GET /files/{id}/…` | — | 카드 PNG · ZIP · manifest | `400 bad_path`(경로 탈출 차단) |

## 상태 객체

```
{ projectId, topic, periodDays, searchedAt,
  status: created|researching|waiting_for_user|ready|done|error,
  stage:  research|select|deep|storyboard|produce|review|export,
  engine, sessionId,                 // 엔진 세션 — --resume 에 쓴다
  candidates[], selection[], selectionVersion,
  question: {id, version, question, options[], why} | null,
  answers[], research{}, editorial{},
  storyboard: {version, approved, title, cards[]},
  cards[], runs[], requests{}, errors[], exports }
```

**`waiting_for_user` 는 실패가 아니다.** 답하기 전에는 다음 단계로 넘어가지 않는다.

## 엔진 결과 정규화 — 이 앱이 «정하는» 규약

CLI 에 내장된 공통 규격이 아니다. 엔진 출력에서 필요한 것을 꺼내 아래로 «해석»한다.

| 종류 | 언제 |
|---|---|
| `result` | 정상 산출 |
| `need_input` | `status:"need_input"` 이거나 `question`+`options` 가 있을 때 → 화면 질문으로 |
| `error` | 엔진이 error 라 했거나 JSON 을 못 팔 때 |

## 취소 — `POST /api/projects/{id}/cancel`  ✅ 2026-09-10 구현

**⚠경로가 PRD 와 다르다.** PRD 는 `POST /api/runs/{id}/cancel` 이라 적었지만
이 앱의 자원은 «실행(run)» 이 아니라 «프로젝트» 다. 한 프로젝트에 한 번에 한 작업만 돈다.
없는 자원을 만들기보다 **있는 자원에 붙이고 그 차이를 여기 적는다.**

### 무엇을 «정리» 하는가 — 넷을 정했다

| | 무엇 | 왜 |
|---|---|---|
| ① | 자식 프로세스를 **트리째** 죽인다 | Windows 에서 `p.kill()` 은 `claude.CMD`(cmd.exe) 만 죽이고 그 아래가 «살아남는다» → `taskkill /T` |
| ② | 스레드가 **다음 단계로 안 넘어간다** | 취소 뒤에도 apply 가 stage 를 올려 버리면 「끊었는데 진행됨」이 된다 |
| ③ | 상태를 `cancelled` 로 적는다 | ⛔**실패가 아니다.** 오류 목록에 넣지 않는다 |
| ④ | **결과물은 지우지 않는다** | 취소는 «되돌리기»가 아니다. 후보 10개를 받고 검증을 끊었다면 후보는 남는다 |

### 응답

```json
{ "ok": true, "runId": "run-…",
  "processKilled": true,
  "note": "이미 만들어진 결과물은 «지우지 않았습니다» — 취소는 되돌리기가 아닙니다" }
```

돌고 있는 것이 없으면 — **「있었다」고 하지 않는다**:

```json
{ "ok": false, "reason": "not_running", "detail": "돌고 있는 작업이 없습니다" }
```

### 시험 — `tools/verify-cancel.py` (12항목, 전부 통과)

★**상태 문자열만 보지 않는다.** 「취소했다」가 사실인지 확인하려면
**자식 프로세스가 정말 사라졌는지**를 세야 한다 — `tasklist` 로 PID 집합을 재고,
**«새로 생긴» PID 가 사라졌는가**를 본다.

> ⚠**측정기가 두 번 틀렸다.**
> ① 처음엔 «개수»로 쟀다 — 시험 전부터 node.exe 가 1개 떠 있어서
>    `before 1 → during 1 → after 1` 이 되고 **아무것도 검증 못 하면서 통과**했다.
> ② PID 집합으로 바꿨더니 이번엔 «없음» 이 나왔다 — 실제 자식은
>    `node.exe` 가 아니라 **`claude.exe`** 였다. **이름을 추측해 필터를 박은 게 원인.**
> → 전부 찍어 오고 `claude`/`node` 를 «포함»하는 것만 본다.
