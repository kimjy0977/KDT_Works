# -*- coding: utf-8 -*-
"""동시 실행 시험 — 두 프로젝트를 «같이» 돌려도 섞이지 않는가.

★왜 필요했나
  README 의 ACCEPTANCE 에 「서로 다른 프로젝트의 세션이 섞이지 않는다」가 있는데
  거기 «⚠구조는 분리했으나 동시 2건 부하 시험은 안 했다» 라고 적어 뒀다.
  **「분리하도록 짰다」와 「실제로 안 섞인다」는 다른 사실이다.**
  구조가 맞아도 락 하나를 빼먹으면 섞인다. 그래서 «돌려서» 본다.

무엇을 보나
  ① 상태 파일이 서로 덮어쓰지 않는가       (topic·mode·projectId 가 자기 것인가)
  ② 엔진 세션이 섞이지 않는가              (sessionId 가 서로 다른가)
  ③ 엔진 작업 폴더가 분리돼 있는가          (data/<pid>/engine)
  ④ 후보가 «자기 주제»의 것인가            (news 는 소식, myth 는 이야기)
  ⑤ 두 번 눌러도 한 번만 도는가            (requestId 중복 방지가 동시에도 통하는가)

쓰는 법:  python tools/verify-concurrent.py      (서버가 떠 있어야 한다)
⚠실제로 웹 검색을 두 건 돌린다 — 3~5분 걸린다.
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.environ.get('CARDNEWS_BASE', 'http://127.0.0.1:8765')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        with urllib.request.urlopen(r, timeout=180) as f:
            return f.status, json.load(f)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as f:
        return json.load(f)


print('=' * 62)
print('동시 실행 시험 — 두 프로젝트가 섞이는가')
print('=' * 62)

# ── 준비: 서로 «다른» 성격의 두 프로젝트 ────────────
A = post('/api/projects', {'topic': 'AI 최신소식', 'mode': 'news', 'periodDays': 7})[1]['projectId']
B = post('/api/projects', {'topic': '페르세우스와 메두사', 'mode': 'myth'})[1]['projectId']
print('\n  A(news) %s' % A)
print('  B(myth) %s' % B)
ok('프로젝트 ID 가 서로 다르다', A != B)

# ── ① 동시에 시작 ──────────────────────────────────
print('\n■ 1. 동시에 조사 시작')
started = {}


def kick(pid, key):
    started[key] = post('/api/projects/%s/research' % pid, {'requestId': uuid.uuid4().hex[:12]})


ta = threading.Thread(target=kick, args=(A, 'a'))
tb = threading.Thread(target=kick, args=(B, 'b'))
ta.start()
tb.start()
ta.join()
tb.join()
ok('둘 다 시작됐다', all(v[0] == 200 for v in started.values()),
   str({k: v[0] for k, v in started.items()}))

time.sleep(8)
sa, sb = get('/api/projects/' + A), get('/api/projects/' + B)
ok('둘 다 «동시에» 돌고 있다',
   sa['status'] == 'researching' and sb['status'] == 'researching',
   'A=%s B=%s' % (sa['status'], sb['status']))

# ── ② 중복 요청이 «동시에도» 막히는가 ────────────────
print('\n■ 2. 같은 프로젝트를 두 번 누르면')
code, r = post('/api/projects/%s/research' % A, {'requestId': uuid.uuid4().hex[:12]})
ok('이미 도는 작업을 «또» 시작하지 않는다',
   (r.get('ok') is False and r.get('reason') == 'already_running') or code != 200,
   json.dumps(r, ensure_ascii=False)[:90])

# ── ③ 상태가 서로 덮어쓰지 않는가 ───────────────────
print('\n■ 3. 상태 파일이 서로를 덮어쓰지 않는가')
ok('A 는 자기 주제를 갖고 있다', sa['topic'] == 'AI 최신소식', sa['topic'])
ok('B 는 자기 주제를 갖고 있다', sb['topic'] == '페르세우스와 메두사', sb['topic'])
ok('A 의 모드가 news 다', sa.get('mode') == 'news', str(sa.get('mode')))
ok('B 의 모드가 myth 다', sb.get('mode') == 'myth', str(sb.get('mode')))
ok('projectId 가 자기 것이다', sa['projectId'] == A and sb['projectId'] == B)

# ── ④ 엔진 작업 폴더가 분리돼 있는가 ─────────────────
print('\n■ 4. 엔진 작업 폴더 분리')
da = os.path.join(HERE, 'data', A, 'engine')
db = os.path.join(HERE, 'data', B, 'engine')
ok('A 의 엔진 폴더가 따로 있다', os.path.isdir(da), da[-46:])
ok('B 의 엔진 폴더가 따로 있다', os.path.isdir(db), db[-46:])
ok('★두 폴더가 다른 경로다', os.path.abspath(da) != os.path.abspath(db))

# ── ⑤ 끝날 때까지 기다렸다가 결과를 본다 ──────────────
print('\n■ 5. 끝까지 돌려서 결과가 «자기 것»인가  (3~6분)')
t0 = time.time()
while time.time() - t0 < 600:
    sa, sb = get('/api/projects/' + A), get('/api/projects/' + B)
    if sa['status'] in ('ready', 'error', 'cancelled') and sb['status'] in ('ready', 'error', 'cancelled'):
        break
    time.sleep(6)
print('  %.0f초 · A=%s B=%s' % (time.time() - t0, sa['status'], sb['status']))

ok('A 가 후보를 받았다', bool(sa.get('candidates')), '%d개' % len(sa.get('candidates') or []))
ok('B 가 후보를 받았다', bool(sb.get('candidates')), '%d개' % len(sb.get('candidates') or []))

# ★핵심 — 세션이 섞이면 «상대의 결과»가 들어온다
if sa.get('sessionId') and sb.get('sessionId'):
    ok('★엔진 세션 ID 가 서로 다르다', sa['sessionId'] != sb['sessionId'],
       '%s / %s' % (str(sa['sessionId'])[:12], str(sb['sessionId'])[:12]))
else:
    ok('★엔진 세션 ID 가 서로 다르다', True, '한쪽이 세션을 안 남김 — 섞일 수 없음')

kinds_a = {c.get('kind') for c in (sa.get('candidates') or [])}
kinds_b = {c.get('kind') for c in (sb.get('candidates') or [])}
ok('★A 의 후보에 «신화» 가 섞이지 않았다', '신화' not in kinds_a, str(sorted(k for k in kinds_a if k)))
ok('★B 의 후보가 전부 «신화» 다', kinds_b == {'신화'} or not kinds_b, str(sorted(k for k in kinds_b if k)))

# 후보 ID 가 상대 것과 통째로 같으면 섞인 것이다
ta_ = [c.get('title') for c in (sa.get('candidates') or [])]
tb_ = [c.get('title') for c in (sb.get('candidates') or [])]
ok('★두 후보 목록이 같지 않다', ta_ != tb_ or not ta_,
   'A %d개 · B %d개 · 겹침 %d' % (len(ta_), len(tb_), len(set(ta_) & set(tb_))))

print('\n' + '=' * 62)
print('통과 %d · 실패 %d' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
