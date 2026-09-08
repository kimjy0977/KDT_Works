# -*- coding: utf-8 -*-
"""제출용 «사본»을 만든다 (12강 제출 규칙).

원본 실행 폴더는 «그대로 둔다». 여기서 만드는 것은 재배포 가능한 사본이다.

제외
  · `.benchmark-cache/`                       내려받은 원본 캐시
  · `jobs/*/source/benchmark/upstream/`       원본 문제·자료·«풀이»·테스트
  · 시행 workspace 의 «원본 fixture 파일»     result.json 의 fixture_sha256 목록으로 «정확히» 식별
  · `verifier/test_outputs.py`                원본 채점 코드
  · `__pycache__/`                            생성물
  · `.harness/`                               내 CLI 세션(실습 fixture 내용 포함)

보존
  · 내 구현과 변경 내용 · 시행별 result.json · 하네스 이벤트 기록
  · 채점 결과 XML·stdout·stderr · run-metadata.json · 집계 보고서

⛔ **원문을 제외한다는 이유로 실패 시행이나 불리한 점수 행을 삭제하지 않는다.**
   result.json 은 «전부» 그대로 옮긴다.

사용: uv run python package_submission.py
"""
import hashlib
import io
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / '_제출용_m4n6'
KIT = ROOT.parent / 'm4n6-하네스설계키트'

EXCLUDED = []          # (경로, 이유)
KEPT_TRIALS = []


def note(rel, why):
    EXCLUDED.append((str(rel).replace('\\', '/'), why))


def fixture_names(trial: Path) -> set:
    """result.json 의 fixture_sha256 = 이 시행에 «넣어 준» 원본 파일 목록."""
    p = trial / 'result.json'
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return set()
    return set((data.get('fixture_sha256') or {}).keys())


MASK_NOTE = (
    "[제출용 사본에서 가림] 이 자리에는 «원본 벤치마크 문제의 지시문»(%d자)이 있었다. "
    "원본 문제를 재배포하지 않으려고 가렸다. 점수·상태·도구 기록은 «그대로»다. "
    "원문은 benchmark/tasks.json 의 고정 커밋에서 "
    "`uv run python -m harness_lab.benchmark_source --prepare` 로 다시 받을 수 있다."
)


def mask_sessions(root: Path) -> int:
    """세션 로그의 «원본 문제 지시문»만 가린다. 나머지는 손대지 않는다."""
    masked = 0
    for path in sorted(root.rglob('agent/sessions/*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            continue
        messages = data.get('messages')
        if not isinstance(messages, list):
            continue
        touched = False
        for message in messages:
            if not isinstance(message, dict) or message.get('role') != 'user':
                continue
            content = message.get('content')
            if isinstance(content, str) and content.strip():
                message['content'] = MASK_NOTE % len(content)
                touched = True
        if touched:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                            encoding='utf-8', newline='\n')
            masked += 1
            note(str(path.relative_to(root)) + ' (role=user 본문)',
                 '원본 문제 지시문. 가리고 나머지는 보존')
    return masked


def copy_job(job: Path, dest: Path):
    for trial in sorted(job.iterdir()):
        if trial.is_file():
            shutil.copy2(trial, dest / trial.name)     # manifest·설정·메타데이터
            continue
        if trial.name == 'source':
            # 소스 스냅샷 — upstream «원문»만 뺀다
            for item in sorted(trial.rglob('*')):
                rel = item.relative_to(trial)
                parts = rel.parts
                if 'upstream' in parts:
                    continue
                if '__pycache__' in parts:
                    continue
                target = dest / 'source' / rel
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
            note(job.name + '/source/benchmark/upstream/',
                 '원본 문제·자료·풀이(solution)·테스트. 재배포하지 않는다')
            continue

        # scoreboard/ 는 시행이 아니라 집계 폴더다 — «시행 수»에 넣지 않는다.
        if trial.name != 'scoreboard':
            KEPT_TRIALS.append(job.name + '/' + trial.name)
        originals = fixture_names(trial)
        for item in sorted(trial.rglob('*')):
            rel = item.relative_to(trial)
            parts = rel.parts
            if '__pycache__' in parts:
                continue
            if parts[0] == 'verifier' and item.name == 'test_outputs.py':
                note(job.name + '/' + trial.name + '/verifier/test_outputs.py',
                     '원본 채점 코드')
                continue
            if parts[0] == 'workspace':
                inner = '/'.join(parts[1:])
                if inner in originals:
                    note(job.name + '/' + trial.name + '/workspace/' + inner,
                         '이 시행에 넣어 준 «원본 fixture». 에이전트 산출물이 아니다')
                    continue
                if item.is_file() and 'solution' in item.name.lower():
                    note(job.name + '/' + trial.name + '/workspace/' + inner,
                         '★원본 «정답» 파일')
                    continue
            # ★시행 «이름»을 붙여야 한다. 빼면 10개 시행이 서로 덮어써
            #   result.json 이 1개만 남는다 — «불리한 행을 지운 것»과 구별되지 않는다.
            target = dest / trial.name / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)


README = """# 모듈4 노드6 [프로젝트] 나만의 에이전트 하네스 만들기

**김주영** (아이펠 KDT AI 에이전트 1기) · 2026-09-08

> **한 줄** — 로컬 CLI 하네스를 직접 만들고, 고정 10문항을 **세 번**(기준 · 개선 · 내 하네스)
> 실행했다. **점수는 셋 다 0/10**이지만, 개선 가설의 «기전»은 확인했고
> **왜 성과로 이어지지 않았는지**까지 기록했다.

---

## 루브릭 항목이 어디에 있나

| 평가기준 | 위치 |
|---|---|
| ① **좋아진 점과 나빠진 점을 «모두»** 분석 + 후속 개선 방향 | `EXPERIMENT_REPORT.md` → **실패 분석과 개선 가설 · 실제 변화 / 다음 실험** |
| ② 실패 근거와 개선 가설이 **연결**되고, **동일 문항·비교 가능 조건**에서 전후 실험 | `EXPERIMENT_REPORT.md` → **추정 원인과 이를 뒷받침하는 기록 / 동일하게 유지한 조건** |
| ③ **사용자 요구**와 실제 동작을 비교하고 **구체적 실행 근거**로 설명 | `ACCEPTANCE.md` → A01~A12 상태와 증거 · `PRD.md` D01 사용자 이야기 |

## 먼저 볼 파일 셋

1. **`EXPERIMENT_REPORT.md`** — 실험 전체(조건·결과·실패 분석·한계)
2. **`ACCEPTANCE.md`** — 완료 조건 A01~A12 와 «실제 실행 증거»
3. **`EXCLUDED.md`** — 제출본에서 «무엇을 왜 뺐는지»와 원본 재현 방법

## 내가 만든 것 / 참고한 것

| | 내용 |
|---|---|
| **직접 작성** | `myharness/core.py` — 모델·도구 반복, 경로 검사, 도구 4종, 승인, 한도, Ollama 연결부. **표준 라이브러리만** 씁니다(의존성 0) |
| | `myharness/bench.py` — 고정 10문항 평가기와 잇는 연결부 |
| | `run.py` — CLI와 세션 저장 |
| | `fixtures/` — 내 사용자 이야기(D01)를 재현한 가상 자료 |
| **참고·변경** | `harness_lab/` — 9강 제공 구현(v4.0.0). **`local_agent.relative_path()` 1곳**을 고쳐 `improved` 실행에 썼습니다 |

★**모델·도구 반복을 수행하는 주체는 `myharness` 입니다.** 다른 에이전트 제품에 맡기지 않았습니다.

## 세 번의 실행

| 실행 | 무엇 | 통과 | 도구 오류율 |
|---|---|---|---|
| `jobs/baseline` | 제공 구현 그대로 | 0/10 | 61% |
| `jobs/improved` | 제공 구현 + 경로 매핑 1곳 수정 | 0/10 | 47% |
| `jobs/my-baseline` | **내 하네스** | 0/10 | **30%** |

집계 보고서는 `reports/` 에 CSV·JSON·HTML 로 들어 있습니다.
**시행 30개의 `result.json` 을 전부 보존했습니다** — 실패·오류·미완료 행을 지우지 않았습니다.

## 직접 돌려 보려면

```bash
# 내 하네스 (의존성 없음 · Ollama 필요)
python run.py --workspace work --session 시험 --prompt "..."

# 고정 10문항 평가 (원본 자료는 아래 명령으로 다시 준비)
uv sync --locked
uv run python -m harness_lab.benchmark_source --prepare
uv run python -m harness_lab.bench --name 새이름 \\
    --agent myharness.bench:solve_task --provider ollama --model qwen3.5:2b
```

원본 문제·정답은 재배포하지 않으려고 **제외**했습니다. 위 `--prepare` 가 고정 커밋에서
다시 내려받고 **해시를 대조**합니다. 자세한 내용은 `EXCLUDED.md`.

## 솔직하게 적어 둔 것

- **점수는 0/10 입니다.** 2.3B 로컬 모델(`qwen3.5:2b`)로 돌렸고, 높은 점수가 목표가 아니었습니다
- **반복 n=1** 이라 `python-sudoku` 의 점수 하락이 «내 변경 탓인지 실행 변동인지» 가르지 못했습니다
- **Windows 에서만** 실행했습니다. 이번에 고친 결함 자체가 Windows 에서만 드러나는 것이었습니다
- **A09·A10 은 DEFERRED** 입니다(저장 정책 미선택 · OpenAI 크레딧 없음). 결정 ID와 함께 적었습니다
- 토큰·비용은 **「알 수 없음」** 입니다. 0 으로 적지 않았습니다

## 이 폴더의 다른 파일

`README_설계키트-원본.md` 는 제공된 설계 키트의 학생용 안내 원문입니다(참고용).
`package_submission.py` 는 이 제출본을 만든 스크립트입니다 — 무엇을 뺐는지 코드로 확인할 수 있습니다.
"""


def main():
    # Windows 에서 폴더 «자체»에 핸들이 걸려 있으면 rmtree 가 실패한다.
    # 내용만 비우고 폴더는 재사용한다 — 결과물은 같다.
    if OUT.exists():
        for item in sorted(OUT.iterdir(), reverse=True):
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink()
                except OSError:
                    pass
    OUT.mkdir(parents=True, exist_ok=True)

    # 1) 내 설계 문서와 구현 (정본)
    for name in ('PRD.md', 'DECISIONS.md', 'INTERFACES.md', 'ACCEPTANCE.md',
                 'IMPLEMENTATION_PLAN.md', 'TROUBLESHOOTING.md',
                 'AGENTS.md', 'run.py'):
        if (KIT / name).exists():
            shutil.copy2(KIT / name, OUT / name)
    # 키트의 README 는 «학생용 시작 안내»라 제출물 설명이 아니다 — 이름을 바꿔 보존한다.
    if (KIT / 'README.md').exists():
        shutil.copy2(KIT / 'README.md', OUT / 'README_설계키트-원본.md')
    # 채점자가 «처음 보는» 안내를 최상위에 세운다.
    (OUT / 'README.md').write_text(README, encoding='utf-8', newline='\n')
    shutil.copytree(KIT / 'myharness', OUT / 'myharness',
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(KIT / 'fixtures', OUT / 'fixtures',
                    ignore=shutil.ignore_patterns('__pycache__'))

    # 2) 평가 하네스 쪽 — 실험 보고서·설정·의존성
    for name in ('EXPERIMENT_REPORT.md', 'pyproject.toml', 'uv.lock',
                 'package_submission.py'):
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, OUT / ('harness-lab_' + name)
                         if name in ('pyproject.toml', 'uv.lock') else OUT / name)
    (OUT / 'benchmark').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'benchmark' / 'tasks.json', OUT / 'benchmark' / 'tasks.json')

    # 3) 변경한 평가 코드 (기준 대비 무엇을 고쳤는지)
    shutil.copytree(ROOT / 'harness_lab', OUT / 'harness_lab',
                    ignore=shutil.ignore_patterns('__pycache__'))

    # 4) 집계 보고서
    if (ROOT / 'reports').exists():
        shutil.copytree(ROOT / 'reports', OUT / 'reports',
                        ignore=shutil.ignore_patterns('__pycache__'))

    # 5) 실행 결과
    for job in sorted((ROOT / 'jobs').iterdir()):
        if not job.is_dir():
            continue
        dest = OUT / 'jobs' / job.name
        dest.mkdir(parents=True, exist_ok=True)
        copy_job(job, dest)

    masked = mask_sessions(OUT)
    print('세션 로그 %d개에서 원본 지시문을 가렸다' % masked)

    note('.benchmark-cache/', '내려받은 원본 문제 캐시. manifest 로 재생성 가능')
    note('.harness/', '내 CLI 세션·실행 기록. 실습 fixture 내용이 남아 있다')
    note('**/__pycache__/', '생성물')

    # 6) 제외 목록과 재현 방법
    manifest = json.loads((ROOT / 'benchmark' / 'tasks.json').read_text(encoding='utf-8'))
    lines = ['# 제출용 사본에서 «제외한 것»과 그 이유', '',
             '원본 실행 폴더는 그대로 보존했다. 이 목록은 «재배포 사본»에만 적용된다.',
             '', '## 제외 경로', '', '| 경로 | 이유 |', '|---|---|']
    seen = set()
    for path, why in EXCLUDED:
        key = (path.split('/')[0] + '/' + path.split('/')[-1], why)
        if key in seen:
            continue
        seen.add(key)
        lines.append('| `%s` | %s |' % (path, why))
    if len(EXCLUDED) > len(seen):
        lines.append('')
        lines.append('> 같은 이유로 제외한 항목이 **총 %d건**이다(위는 유형별 대표).'
                     % len(EXCLUDED))
    lines += ['', '## 보존한 것', '',
              '- 시행 **%d개** 전부의 `result.json` — **실패·오류·미완료 행을 삭제하지 않았다**'
              % len(KEPT_TRIALS),
              '- 하네스 이벤트 기록 `agent/events.jsonl` · 대화 `agent/sessions/`',
              '- 채점 결과 `verifier/results.xml` · `stdout.txt` · `stderr.txt`',
              '- `run-metadata.json` — **원본을 덮어쓰지 않았다**',
              '- 집계 보고서 `reports/` (CSV·JSON·HTML)',
              '- 내 구현 `myharness/` 와 변경한 `harness_lab/`',
              '', '## 원본 자료를 다시 준비하는 방법', '',
              '```bash', 'uv sync --locked',
              'uv run python -m harness_lab.benchmark_source --prepare', '```', '',
              '- upstream revision: `%s`' % (manifest.get('revision') or '(manifest 참조)'),
              '- 고정 목록과 파일 해시: `benchmark/tasks.json`',
              '- 위 명령이 해시를 대조하므로 **같은 원본인지 확인할 수 있다**',
              '', '## 주의', '',
              '- 제출용 사본의 해시는 **원본 실행 스냅샷의 `source_sha256` 과 다르다.**',
              '  upstream 원문을 뺐기 때문이며, **실행 메타데이터는 원래 값 그대로 두었다.**',
              '- API 키·토큰은 코드·문서·기록 어디에도 넣지 않았다(로컬 Ollama 라 키가 없다).',
              '- 개인 자료를 쓰지 않았다. `fixtures/` 는 이 과제용으로 만든 가상 자료다.']
    (OUT / 'EXCLUDED.md').write_text('\n'.join(lines) + '\n',
                                     encoding='utf-8', newline='\n')

    total = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())
    count = sum(1 for f in OUT.rglob('*') if f.is_file())
    print('제출용 사본: %s' % OUT)
    print('파일 %d개 · %.2f MB' % (count, total / 1024 / 1024))
    print('제외 %d건 · 보존 시행 %d개' % (len(EXCLUDED), len(KEPT_TRIALS)))
    print('★ZIP 5MB 제한: %s' % ('여유 있음' if total < 4.5 * 1024 * 1024
                                 else '초과 위험 — URL 제출을 고려'))
    # 키가 새지 않았는지 실제로 «센다»
    risky = 0
    for f in OUT.rglob('*'):
        if not f.is_file() or f.suffix in ('.png', '.jpg', '.zip'):
            continue
        if f.name == Path(__file__).name:
            continue   # 검사기 «자신»의 탐지 패턴은 세지 않는다
        try:
            t = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        for token in ('sk-', 'OPENAI_API_KEY=', 'ANTHROPIC_API_KEY='):
            if token in t:
                risky += 1
                print('  ⚠ 키 형태 문자열 발견: %s (%s)' % (f.relative_to(OUT), token))
    print('키 형태 문자열 %d건' % risky)


main()
