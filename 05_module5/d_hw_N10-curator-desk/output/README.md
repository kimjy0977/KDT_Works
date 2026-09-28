# output/ — 무엇이 무엇인가

> ⛔**손으로 적지 않습니다.** 여기 있는 것은 전부 스크립트가 **돌면서 남긴 것**입니다.
> 어느 명령이 만드는지 같이 적습니다 — **다시 만들 수 있어야 증거입니다.**

| 파일 | 무엇 | 만드는 명령 |
|---|---|---|
| `threads.json` | ★**색인** — 어떤 thread 가 있고 무엇이 끝났나 | `python graph.py --올린다` |
| `published.jsonl` | 바깥으로 «나간» 기록 (DRY_RUN 포함) | `graph.py` · `app.py` |
| `catalog.json` | ★카탈로그 등재본 — **다음 주 큐레이션이 읽는 것** | `graph.py` · `app.py` |
| `compare.json` | ★비교표 — 개입률·놓침·헛멈춤 (「하나 빼기」 포함) | `python compare.py` |
| `e2e.json` | 전 과정 실행 기록 (단계·초·종료코드) | `python e2e.py` |

## ⛔여기 «없는» 것 — `checkpoints.sqlite`

승인 대기 상태는 `SqliteSaver` 가 **이 폴더의 sqlite 파일**에 적습니다.
그 파일은 **저장소에 올리지 않습니다**(`.gitignore`).

```
① 「돌리면 생기는 것」이다 — 소스가 아니다
② ⛔크다. 상태에서 작품 실물을 뺀 뒤에도 2.5MB 다
   (빼기 «전»에는 ★29.4MB 였다 — REPORT §6 참조)
```

대신 **`threads.json` 을 올립니다** — 작고, 무엇이 대기이고 무엇이 끝났는지 읽힙니다.
**대기 여부의 «판정»은 언제나 `snapshot.next`** 가 합니다 — 이 색인이 아닙니다.

### 다시 만들려면

```bash
python normalize.py && python enrich.py && python write.py
python graph.py --올린다
```
