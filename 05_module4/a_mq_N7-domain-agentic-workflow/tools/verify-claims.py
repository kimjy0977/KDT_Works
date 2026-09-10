# -*- coding: utf-8 -*-
"""verify-claims.py — 과제요건.md 가 «말한 숫자»를 실물에서 다시 센다.

★왜 audit.py 로 안 되나
   audit.py 는 「문서↔구현」을 보지만 «제출 문서»(과제요건.md)의
   평가문항 대조표는 안 본다. 제출 직전에 필요한 건 바로 그 표다.
   ⇒ 「채점자가 이 표를 들고 확인하러 갔을 때 그대로인가」를 잰다.

★규율
   · 세는 게 목적이면 «집계 명령»을 쓴다 (§F-8-A ⑧)
   · 링크는 «닿는지»로 판정한다 (§F-8-B ④)
   · 못 세는 것은 「못 셈」이라 적는다. 통과로 넘기지 않는다

쓰는 법:  python tools/verify-claims.py
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)

OK, BAD, WARN = [], [], []


def read(p):
    try:
        return io.open(p, encoding='utf-8').read()
    except OSError:
        return ''


def claim(name, want, got, note=''):
    """want 와 got 을 대조. want 가 None 이면 «참고»만."""
    if want is None:
        WARN.append((name, str(got), note))
        return
    good = str(want) == str(got)
    (OK if good else BAD).append((name, '주장 %s / 실측 %s' % (want, got), note))


REQ = read('과제요건.md')
print('=' * 66)
print('제출 전 정밀 검토 — 과제요건.md 의 주장을 «실물»에서 다시 센다')
print('=' * 66)

# ══ 1. 도구 ═══════════════════════════════════════════════
print('\n■ 1. 도구 — 「8종」·「reason 12종」·「쓰기는 워크플로마다 하나」')
tools = read('app/tools.js')
names = re.findall(r"name:\s*'([a-z_0-9]+)'", tools)
writes = re.findall(r'writes:\s*true', tools)
claim('도구 개수', 8, len(names), ' · '.join(names))
# ★도구가 내는 reason 과 루프의 «종료 사유»는 다른 것이다.
# 섞어 세면 12 가 18 로 보인다 (실측으로 오탐을 냈다).
reasons = set(re.findall(r"reason:\s*'([a-z_0-9]+)'", tools))
claim('도구 reason 종류', 12, len(reasons), ' '.join(sorted(reasons)) or '못 셈')
stop_reasons = set(re.findall(r"reason:\s*'([a-z_0-9]+)'", read('app/agent.js')))
claim('루프 종료 사유', None, len(stop_reasons), ' '.join(sorted(stop_reasons)))
claim('쓰기 도구', 2, len(writes), 'intake·curate 각 1개면 2')

# ══ 2. 루프·종료조건·사람개입 ══════════════════════════════
print('\n■ 2. 루프 — 종료 조건 4 · 사람 개입 3지점')
ag = read('app/agent.js')
stops = set(re.findall(r"stopReason[^\n]*?'([a-z_]+)'", ag)) | \
        set(re.findall(r"kind:\s*'(max_steps|max_tools|wall_clock|repeat|budget)'", ag))
claim('종료 조건', None, len(stops) or '못 셈', ' '.join(sorted(stops)))
prd = read('PRD.md')
claim('PRD 에 「사람 개입」 절이 있나', 'True', str('사람 개입' in prd or '개입 지점' in prd))

# ══ 3. 시험 개수 — ★문서가 두 숫자를 말한다 ═════════════════
print('\n■ 3. 시험 — 문서가 「31+12+18=61」과 「70」을 «둘 다» 말한다')
# ★이 폴더의 시험은 넷이다. 취소·동시실행 시험은 «실습» 폴더 것이라
#   메인 퀘스트 조건표에 세면 안 된다 (2026-09-10 제출 전 검토에서 잡음).
for f in ['tools/verify-loop.mjs', 'tools/verify-tools.mjs',
          'tools/verify-mcp.mjs', 'tools/verify-ui.mjs']:
    print('   %-26s %s' % (f, '있음' if os.path.exists(f) else '★없음'))
claim('조건표가 실습 시험을 세지 않는가', 'True',
      str('취소 12' not in REQ and '동시실행 18' not in REQ))

# ══ 4. 평가 ═══════════════════════════════════════════════
print('\n■ 4. 평가 — 「40문항」·「5세팅」·「실패 7유형」')
try:
    ev = json.load(io.open('data/evalset.json', encoding='utf-8'))
    n = len(ev if isinstance(ev, list) else ev.get('cases', ev.get('items', [])))
except Exception as e:
    n = '못 읽음 (%s)' % e
claim('평가 문항 수', 40, n)
try:
    su = json.load(io.open('results/summary.json', encoding='utf-8'))
    settings = su.get('settings') or su.get('S') or []
    claim('세팅 수', 5, len(settings),
          ' · '.join(str((s.get('setting') or {}).get('name', '?')) for s in settings))
    ftypes = set()
    for s in settings:
        ftypes |= set((s.get('failures') or {}).keys())
    # ★EVALUATION.md 정의표는 «7유형 + 기타 버킷 2» = 9 다.
    #   기타 버킷(backend_error:* · other:*)을 정의에서 빼면
    #   「분류가 못 따라간 자리」가 문서에서 사라진다. 그건 숨기는 것이다.
    claim('실패 유형(기타 버킷 포함)', 9, len(ftypes), ' '.join(sorted(ftypes)) or '못 셈')
    unclassified = sum(v for s2 in settings for k, v in (s2.get('failures') or {}).items()
                       if k.split(':')[0] in ('backend_error', 'other'))
    total_f = sum(v for s2 in settings for v in (s2.get('failures') or {}).values())
    claim('EVALUATION.md 가 미분류 비율을 «적었는가»', 'True',
          str('12%' in read('EVALUATION.md')),
          '실측 %d/%d = %.1f%%' % (unclassified, total_f, 100.0*unclassified/total_f))
except Exception as e:
    BAD.append(('평가 요약', 'results/summary.json 을 못 읽음: %s' % e, ''))

# ══ 5. MCP ════════════════════════════════════════════════
print('\n■ 5. MCP — 「읽기 6종만 노출」·「의존성 0」')
mcp = read('mcp/server.mjs')
# ★도구 «정의»는 app/tools.js 에 있고 server.mjs 는 거기서 «고른다».
#   server.mjs 안에서 name: 을 찾으면 0 이 나온다 (실측으로 오탐을 냈다).
#   설명·스키마를 두 벌 두지 않으려는 «설계»이므로, 그 설계대로 센다.
exposed_rule = "TOOLS.filter((t) => !t.writes)" in mcp
claim('MCP 가 쓰기 도구를 «거른다»', 'True', str(exposed_rule), 'TOOLS.filter(t => !t.writes)')
claim('MCP 노출 도구', 6, len(names) - len(writes) if exposed_rule else '못 셈',
      '도구 %d종 - 쓰기 %d종' % (len(names), len(writes)))
# ★「의존성 0」은 npm 패키지 0을 말한다. 자기 프로젝트 파일은 의존성이 아니다.
pkgs = [m for m in re.findall(r"from\s+'([^']+)'", mcp)
        if not m.startswith('node:') and not m.startswith('.')]
claim('외부 npm 패키지', 0, len(pkgs), ' '.join(pkgs) or '없음 (node: 내장 + 자기 파일만)')

# ══ 6. ★링크가 «닿는가» ═══════════════════════════════════
print('\n■ 6. 과제요건.md 의 링크가 «실제로» 닿는가')
links = re.findall(r'\]\((?!https?:)([^)#]+)', REQ)
miss = []
for p in sorted(set(links)):
    tgt = os.path.normpath(os.path.join(HERE, p))
    if not os.path.exists(tgt):
        miss.append(p)
claim('내부 링크', 0, len(miss), '★닿지 않음: ' + ' '.join(miss) if miss
      else '%d개 전부 닿음' % len(set(links)))

# ★폴더 «밖»을 가리키는 링크 — 채점자를 내보낸다
# ★«평가문항 표» 안에서만 본다. 실습을 소개하는 표·캡처본 행은 밖을 가리켜도 된다
#   (6강이 실습을 요구했다는 증거이므로 지우면 사실이 사라진다).
i0 = REQ.find('## 평가 문항')
i1 = REQ.find('## 조건별 대조')
rubric = REQ[i0:i1] if i0 >= 0 < i1 else ''
out_rubric = sorted(set(re.findall(r'\]\((\.\./[^)]+)\)', rubric)))
claim('평가문항 근거가 폴더 안에 있는가', 0, len(out_rubric),
      '★밖: ' + ' '.join(out_rubric) if out_rubric else '전부 이 폴더 안')
out_all = sorted(set(p for p in links if p.startswith('..')))
WARN.append(('문서 다른 곳의 실습 참조', '%d곳' % len(out_all),
             '의도한 것 — 실습을 했다는 증거'))

# ══ 7. 배포가 «실제로» 열리는가 ════════════════════════════
print('\n■ 7. 제출에 적은 주소가 실제로 열리는가')
URLS = [
    ('저장소', 'https://github.com/kimjy0977/KDT_Works/tree/main/05_module4/a_mq_N7-domain-agentic-workflow'),
    ('배포 CURATOR', 'https://kimjy0977.github.io/KDT_Works/05_module4/a_mq_N7-domain-agentic-workflow/'),
    ('배포 — 새 캡처', 'https://kimjy0977.github.io/KDT_Works/05_module4/a_mq_N7-domain-agentic-workflow/docs/screens/INDEX.json'),
    ('배포 — 딥링크 ui.js', 'https://kimjy0977.github.io/KDT_Works/05_module4/a_mq_N7-domain-agentic-workflow/app/ui.js'),
]
for label, u in URLS:
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, method='GET'), timeout=25)
        code, size = r.status, len(r.read())
    except urllib.error.HTTPError as e:
        code, size = e.code, 0
    except Exception as e:
        code, size = 'ERR(%s)' % type(e).__name__, 0
    good = code == 200
    (OK if good else BAD).append((label, 'HTTP %s' % code, '%d bytes' % size))
    print('   %-20s HTTP %-6s %d bytes' % (label, code, size))

# ══ 결과 ══════════════════════════════════════════════════
print('\n' + '=' * 66)
for n_, v, note in OK:
    print('  ✅ %-26s %s%s' % (n_, v, ('  — ' + note) if note else ''))
for n_, v, note in WARN:
    print('  ⚠ %-26s %s%s' % (n_, v, ('  — ' + note) if note else ''))
for n_, v, note in BAD:
    print('  ❌ %-26s %s%s' % (n_, v, ('  — ' + note) if note else ''))
print('=' * 66)
print('통과 %d · 확인필요 %d · ★어긋남 %d' % (len(OK), len(WARN), len(BAD)))
sys.exit(1 if BAD else 0)
