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

## 취소 — **미구현**

PRD 의 `POST /api/runs/{id}/cancel` 은 만들지 못했다. README 의 「아직 못 한 것」에 적었다.
