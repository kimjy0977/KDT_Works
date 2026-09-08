# 2차 실험 · 과업 문장 (글자까지 고정)

저장소: `fixtures-large/repo/` — **282파일 · 최대 깊이 7**
`python3 fixtures-large/make.py` 로 만든다. 난수를 쓰지 않으므로 매번 같은 저장소가 나온다.

---

## L-T1 — 있는 것을 찾는가

```
이 저장소에 핸드오프 문서가 있는지 확인하고, 있으면 경로를 알려 줘.
```

**정답:** `docs/internal/team/ops/handoff/2026/HANDOFF-tutor.md` — **깊이 7**

**미끼 3개** (이름은 비슷하지만 본문이 "미끼 — 실제 인계 문서가 아니다"):

| 경로 | 깊이 |
|---|---|
| `docs/archive/handoff-template.md` | 3 |
| `docs/internal/team/onboarding/handoff-checklist.md` | 5 |
| `services/notify/docs/HANDOFF.md.bak` | 4 |

미끼를 정답으로 답하면 **오답(정답 X)**. 미끼 3건을 함께 보고하는 것 자체는 오답이 아니다.

---

## L-T2 — 깊이에 흩어진 것을 빠짐없이 세는가

```
이 저장소에 설정 파일이 몇 개인지 세어 줘.
```

**정답: 5개** — 서로 다른 깊이 다섯 곳에 흩어 두었다.

| 경로 | 깊이 |
|---|---|
| `settings.toml` | 1 |
| `src/config/settings.toml` | 3 |
| `services/api/config/settings.toml` | 4 |
| `services/billing/deploy/config/settings.toml` | 5 |
| `services/search/internal/engine/config/settings.toml` | 6 |

루트와 `src/config` 만 보면 2개로 답하게 되어 있다.

---

## 조건별로 앞에 붙이는 것

| 조건 | 과업 문장 앞에 붙이는 것 |
|---|---|
| **A** (대조) | 아무것도 붙이지 않는다 |
| **B** (처치 · 목록) | `fixtures-large/tree.txt` 282줄을 그대로 + 빈 줄 하나 |
| **C** (처치 · 지시) | 아래 한 줄 + 빈 줄 하나 |

조건 C의 문장 — **글자까지 이것으로 고정한다.**

```
탐색 범위를 임의로 좁히지 마라. 저장소 전체를 확인해라.
```

> **주의** — 목록에도 지시에도 설명을 덧붙이지 않는다.
> "이건 파일 목록이야" 같은 문장을 더하면 조작 항목이 **「목록」이 아니라 「목록 + 안내」**가 된다.
