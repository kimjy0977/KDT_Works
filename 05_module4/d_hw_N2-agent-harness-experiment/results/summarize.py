# -*- coding: utf-8 -*-
"""results/*.md 를 읽어 README 의 결과 표와 사전 판정식 대조를 만든다.

파일 이름 규칙
    T1-A-1.md      1차 실험(작은 저장소 7파일) · 과업 T1 · 조건 A · 1회차
    L-T1-B-1.md    2차 실험(큰 저장소 282파일) · 과업 T1 · 조건 B · 1회차

조건
    A  대조 — 아무것도 넣지 않는다
    B  처치 — 경로 목록을 프롬프트 앞에 그대로 주입한다
    C  처치 — "탐색 범위를 임의로 좁히지 마라" 한 줄을 더한다 (2차 실험에서 신설)

사용: python3 results/summarize.py
"""
import glob
import io
import os
import re
import statistics
import sys

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = re.compile(r'^(L-)?(T\d)-([ABC])-(\d)\.md$')

# exp -> {(task, cond): [row, ...]}
ROWS = {1: {}, 2: {}}


def val(text, label):
    m = re.search(r'\|\s*%s\s*\|\s*([^|]*)\|' % re.escape(label), text)
    return (m.group(1).strip() if m else '')


for path in sorted(glob.glob(os.path.join(HERE, '*.md'))):
    name = os.path.basename(path)
    if name == 'template.md':
        continue
    m = NAME.match(name)
    if not m:
        print('건너뜀 (이름 규칙 불일치): %s' % name)
        continue
    exp = 2 if m.group(1) else 1
    task, cond, rep = m.group(2), m.group(3), int(m.group(4))
    t = io.open(path, encoding='utf-8').read()
    ROWS[exp].setdefault((task, cond), []).append({
        'rep': rep,
        'miss': val(t, '존재 부정 오류'),
        'search': val(t, '탐색 호출'),
        'ok': val(t, '정답'),
        'sec': val(t, '시간(초)'),
        'turn': val(t, '턴'),
    })


def med(vals):
    nums = []
    for v in vals:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            pass
    if not nums:
        return ''
    return '%g' % statistics.median(nums)


def table(exp, tasks, conds):
    print('| 과업 | 조건 | n | 존재 부정 오류(중앙값) | 탐색 호출(중앙값) | 정답 | 시간 | 턴 |')
    print('|---|---|---|---|---|---|---|---|')
    for task in tasks:
        for cond in conds:
            rs = sorted(ROWS[exp].get((task, cond), []), key=lambda r: r['rep'])
            if not rs:
                continue
            oks = ''.join(r['ok'][:1].upper() for r in rs)
            print('| %s | %s | %d | %s | %s | %s | %s | %s |' % (
                task, cond, len(rs),
                med([r['miss'] for r in rs]), med([r['search'] for r in rs]),
                oks, med([r['sec'] for r in rs]), med([r['turn'] for r in rs])))


def judge(exp, tasks, treat):
    """사전 판정식 (README §5) — 오류 처치<대조 AND 탐색 처치 <= 대조-2."""
    hit = 0
    seen = 0
    for task in tasks:
        a = ROWS[exp].get((task, 'A'), [])
        b = ROWS[exp].get((task, treat), [])
        if not a or not b:
            continue
        seen += 1
        ma, mb = med([r['miss'] for r in a]), med([r['miss'] for r in b])
        sa, sb = med([r['search'] for r in a]), med([r['search'] for r in b])
        try:
            c1 = float(mb) < float(ma)
            c2 = float(sb) <= float(sa) - 2
        except ValueError:
            print('  %s : 수치 누락' % task)
            continue
        ok = c1 and c2
        hit += 1 if ok else 0
        print('  %s : 오류 %s→%s %s · 탐색 %s→%s %s  ⇒ %s'
              % (task, ma, mb, 'OK' if c1 else 'NO',
                 sa, sb, 'OK' if c2 else 'NO', '충족' if ok else '미충족'))
    need = 2 if seen >= 3 else seen
    print('  충족 과업 %d개 / %d개 중 · 지지 기준 %d개' % (hit, seen, need))
    print('  ⇒ %s' % ('지지' if seen and hit >= need
                      else '기각 (또는 판정 불가 — README §5 참조)'))


if not any(ROWS.values()):
    print('기록이 없습니다. results/template.md 를 복사해 T1-A-1.md 처럼 저장하세요.')
    raise SystemExit(0)

if ROWS[1]:
    print('■ 1차 실험 — 작은 저장소 (fixtures/repo · 7파일)')
    table(1, ('T1', 'T2', 'T3'), ('A', 'B'))
    print()
    print('  사전 판정식 대조 — A(대조) vs B(목록 주입)')
    judge(1, ('T1', 'T2', 'T3'), 'B')
    print()

if ROWS[2]:
    print('■ 2차 실험 — 큰 저장소 (fixtures-large/repo · 282파일 · 최대 깊이 7)')
    table(2, ('T1', 'T2'), ('A', 'B', 'C'))
    print()
    print('  사전 판정식 대조 — A(대조) vs B(목록 주입)')
    judge(2, ('T1', 'T2'), 'B')
    print()
    print('  사전 판정식 대조 — A(대조) vs C(탐색 지시 한 줄)')
    judge(2, ('T1', 'T2'), 'C')
