# -*- coding: utf-8 -*-
"""results/*.md 를 읽어 README §6 표와 중앙값을 만든다.

사용: python3 results/summarize.py
"""
import glob, io, os, re, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = {}

def val(text, label):
    m = re.search(r'\|\s*%s\s*\|\s*([^|]*)\|' % re.escape(label), text)
    return (m.group(1).strip() if m else '')

for path in sorted(glob.glob(os.path.join(HERE, '*.md'))):
    name = os.path.basename(path)
    if name == 'template.md':
        continue
    m = re.match(r'(T\d)-([AB])-(\d)\.md$', name)
    if not m:
        print('건너뜀 (이름 규칙 불일치): %s' % name)
        continue
    task, cond, rep = m.group(1), m.group(2), int(m.group(3))
    t = io.open(path, encoding='utf-8').read()
    ROWS.setdefault((task, cond), []).append({
        'rep': rep,
        'miss': val(t, '존재 부정 오류'),
        'search': val(t, '탐색 호출'),
        'ok': val(t, '정답'),
        'sec': val(t, '시간(초)'),
        'turn': val(t, '턴'),
    })

if not ROWS:
    print('기록이 없습니다. results/template.md 를 복사해 T1-A-1.md 처럼 저장하세요.')
    raise SystemExit(0)

def med(vals):
    nums = []
    for v in vals:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            pass
    if not nums:
        return ''
    m = statistics.median(nums)
    return '%g' % m

print('| 과업 | 조건 | n | 존재 부정 오류(중앙값) | 탐색 호출(중앙값) | 정답 | 시간 | 턴 |')
print('|---|---|---|---|---|---|---|---|')
for task in ('T1', 'T2', 'T3'):
    for cond in ('A', 'B'):
        rs = sorted(ROWS.get((task, cond), []), key=lambda r: r['rep'])
        if not rs:
            print('| %s | %s | 0 | — | — | — | — | — |' % (task, cond))
            continue
        oks = ''.join(r['ok'][:1].upper() for r in rs)
        print('| %s | %s | %d | %s | %s | %s | %s | %s |' % (
            task, cond, len(rs),
            med([r['miss'] for r in rs]), med([r['search'] for r in rs]),
            oks, med([r['sec'] for r in rs]), med([r['turn'] for r in rs])))

print()
print('■ 사전 판정식 대조 (README §5)')
hit = 0
for task in ('T1', 'T2', 'T3'):
    a = ROWS.get((task, 'A'), []); b = ROWS.get((task, 'B'), [])
    if not a or not b:
        print('  %s : 기록 부족' % task); continue
    ma, mb = med([r['miss'] for r in a]), med([r['miss'] for r in b])
    sa, sb = med([r['search'] for r in a]), med([r['search'] for r in b])
    try:
        cond1 = float(mb) < float(ma)
        cond2 = float(sb) <= float(sa) - 2
    except ValueError:
        print('  %s : 수치 누락' % task); continue
    ok = cond1 and cond2
    hit += 1 if ok else 0
    print('  %s : 오류 %s→%s %s · 탐색 %s→%s %s  ⇒ %s'
          % (task, ma, mb, 'OK' if cond1 else 'NO', sa, sb, 'OK' if cond2 else 'NO',
             '충족' if ok else '미충족'))
print('  충족 과업 %d개 / 지지 기준 2개' % hit)
print('  ⇒ %s' % ('지지' if hit >= 2 else '기각 (또는 판정 불가 — README §5 참조)'))
