# -*- coding: utf-8 -*-
"""취소 시험 — 「취소했다」가 «사실인지» 확인한다.

★무엇을 재는가
  「요청을 보냈다」와 「실제로 끊겼다」는 다른 사실이다(5강).
  그래서 상태 문자열만 보지 않고 **자식 프로세스가 정말 사라졌는지**를 센다.

  ⛔Windows 에서 `p.kill()` 은 `claude.CMD`(cmd.exe) 만 죽이고
    그 아래 `node` 는 «살아남는다». 그러면 「취소했습니다」라고 적어 놓고
    실제로는 계속 돈다 — 이 시험은 그 거짓말을 잡으려고 있다.

쓰는 법:  python tools/verify-cancel.py            (서버가 떠 있어야 한다)
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.environ.get('CARDNEWS_BASE', 'http://127.0.0.1:8765')
PASS = FAIL = 0


def ok(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print('  ok   %s%s' % (name, (' — ' + detail) if detail else ''))
    else:
        FAIL += 1
        print('  FAIL %s%s' % (name, (' — ' + detail) if detail else ''))


def post(path, body):
    r = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                               headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=120) as f:
            return f.status, json.load(f)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as f:
        return json.load(f)


def claude_procs():
    """살아 있는 자식들의 **PID 집합**을 돌려준다.

    ★«개수»로 재면 못 잡는다. 실측 2026-09-10 —
      시험 전부터 node.exe 가 1개 떠 있어서 before 1 → during 1 이 됐고,
      after 1 도 「사라졌다」로 통과해 버렸다. **아무것도 검증하지 못한 시험**이다.
      → 「새로 생긴 PID 가 사라졌는가」를 봐야 한다. 집합으로 잰다.
    """
    if os.name != 'nt':
        out = subprocess.run(['bash', '-lc', "pgrep -f claude || true"],
                             capture_output=True, text=True).stdout
        return {int(x) for x in out.split() if x.isdigit()}
    # ★이미지 «이름»을 찍어서 거르지 않는다. 실측 2026-09-10 —
    #   node.exe 로 걸렀는데 실제 자식은 **claude.exe** 였다.
    #   이름을 «추측»해서 필터를 박으면, 이름이 다른 순간 시험이 조용히 통과한다.
    #   → 전부 찍어 오고 claude/node 를 «포함»하는 것만 본다.
    out = subprocess.run(['tasklist', '/NH', '/FO', 'CSV'],
                         capture_output=True, text=True, errors='replace').stdout
    pids = set()
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            name = parts[0].lower()
            if 'claude' in name or 'node' in name:
                pids.add(int(parts[1]))
    return pids


print('=' * 60)
print('취소 시험 — 「끊었다」가 사실인가')
print('=' * 60)

# ── ① 안 돌고 있을 때 취소하면? ─────────────────────
print('\n■ 1. 돌지 않는 작업을 취소하면')
st = post('/api/projects', {'topic': '취소 시험', 'mode': 'news'})[1]
pid = st['projectId']
code, r = post('/api/projects/%s/cancel' % pid, {'requestId': uuid.uuid4().hex[:12]})
ok('없는 작업을 «있었다»고 하지 않는다', r.get('ok') is False and r.get('reason') == 'not_running',
   json.dumps(r, ensure_ascii=False)[:80])

# ── ② 돌고 있는 것을 끊는다 ─────────────────────────
print('\n■ 2. 돌고 있는 작업을 끊는다')
before = claude_procs()
post('/api/projects/%s/research' % pid, {'requestId': uuid.uuid4().hex[:12]})
time.sleep(12)                                   # 자식이 실제로 뜰 시간
during = claude_procs()
spawned = during - before                        # ★«새로 생긴» PID 만 본다
s = get('/api/projects/' + pid)
ok('작업이 돌기 시작했다', s['status'] == 'researching', '상태 %s' % s['status'])
ok('★새 자식 프로세스가 생겼다', bool(spawned), 'PID %s' % (sorted(spawned) or '없음'))

code, r = post('/api/projects/%s/cancel' % pid, {'requestId': uuid.uuid4().hex[:12]})
ok('취소가 받아들여졌다', r.get('ok') is True, json.dumps(r, ensure_ascii=False)[:100])
ok('자식 프로세스를 «실제로» 죽였다고 말한다', r.get('processKilled') is True)

time.sleep(6)
after = claude_procs()
survivors = spawned & after                      # ★새로 생긴 것 중 «살아남은» 것
ok('★새로 생긴 자식이 «정말» 사라졌다', not survivors,
   '생김 %s → 살아남음 %s' % (sorted(spawned) or '없음', sorted(survivors) or '없음'))

s = get('/api/projects/' + pid)
ok('상태가 cancelled — «실패»가 아니다', s['status'] == 'cancelled', '상태 %s' % s['status'])
ok('트레이스에 사람이 끊었다고 남는다',
   any(r0.get('step') == 'cancel' and r0.get('kind') == 'human' for r0 in s.get('runs', [])))
ok('오류로 적지 않았다', not any(e.get('reason') == 'cancelled' for e in s.get('errors', [])))

# ── ③ 취소 뒤 다시 시작할 수 있는가 ─────────────────
print('\n■ 3. 끊은 뒤 다시 시작할 수 있는가')
code, r = post('/api/projects/%s/research' % pid, {'requestId': uuid.uuid4().hex[:12]})
time.sleep(4)
s = get('/api/projects/' + pid)
ok('★지난 취소 신호가 새 작업을 죽이지 않는다', s['status'] in ('researching', 'ready'),
   '상태 %s' % s['status'])
post('/api/projects/%s/cancel' % pid, {'requestId': uuid.uuid4().hex[:12]})

# ── ④ 결과물을 지우지 않는가 ────────────────────────
print('\n■ 4. 취소는 «되돌리기»가 아니다')
s = get('/api/projects/' + pid)
ok('프로젝트가 남아 있다', bool(s.get('projectId')))
ok('실행 기록이 지워지지 않았다', len(s.get('runs') or []) > 0, '%d건' % len(s.get('runs') or []))

print('\n' + '=' * 60)
print('통과 %d · 실패 %d' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
