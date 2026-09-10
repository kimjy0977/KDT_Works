# -*- coding: utf-8 -*-
"""MQ4 전수 감사 — 「문서가 말하는 것」과 「실제」를 대조한다.

★왜 기계로 하나
  §F-8-D — «자라는 것을 고정 목록으로 다루지 마라».
  「어디가 빠졌지?」를 «기억»으로 답하면 눈에 띄는 것만 넣고 나머지를 또 빠뜨린다.
  실제로 2026-09-02 에 검사 범위를 16→53→420 으로 두 번 넓히면서
  매번 «안 본 범위»에서 오염이 나왔다.
  ⇒ 범위를 기억하지 말고 «센다».

무엇을 보나
  A 문서 ↔ 구현    API_SPEC 의 엔드포인트가 실제로 있는가 / 도구 수가 맞는가
  B 문서 내부 링크  상대 링크가 «실제로 닿는가»
  C 배포 자산      화면이 부르는 파일이 저장소에 있는가
  D 숫자 주장      「도구 8종」「982점」「70항목」이 사실인가
  E 미구현 선언    문서가 ❌·미구현·안 함 이라고 «스스로 적은» 것
  F 위생          제어문자 · 태그 균형
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

FINDINGS = []           # (심각도, 갈래, 내용)
def note(sev, kind, msg):
    FINDINGS.append((sev, kind, msg))


def read(p):
    try:
        return io.open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''


def walk(exts, skip_dirs=('node_modules', '.git', '__pycache__', 'engine')):
    for r, ds, fs in os.walk('.'):
        ds[:] = [d for d in ds if d not in skip_dirs and not d.startswith('p-')]
        if '/data/p-' in r.replace(os.sep, '/'):
            continue
        for f in fs:
            if f.endswith(exts):
                yield os.path.join(r, f).replace(os.sep, '/').lstrip('./')


# ═══════════ A. 문서 ↔ 구현 ═══════════
print('=' * 62)
print('A. 문서 ↔ 구현')
print('=' * 62)

spec = read('cardnews/API_SPEC.md')
app = read('cardnews/app.py')
# API_SPEC 이 표에 적은 엔드포인트를 뽑는다
declared = set(re.findall(r'`(?:GET|POST|DELETE|PUT)\s+(/api/[^`]+)`', spec))
declared |= set(re.findall(r'\|\s*(?:GET|POST|DELETE|PUT)\s*\|\s*`([^`]+)`', spec))
print('  API_SPEC 이 선언한 엔드포인트 %d개' % len(declared))
for d in sorted(declared):
    tail = d.rstrip('/').split('/')[-1].split('?')[0]
    if tail.startswith('{') or tail.startswith(':'):
        tail = d.rstrip('/').split('/')[-2]
    hit = ("'%s'" % tail) in app or ('/%s' % tail) in app or tail in app
    # ★문서가 «안 만들었다»고 스스로 밝힌 것은 «어긋남»이 아니다.
    #   실측 2026-09-10 — /cancel 을 「문서↔구현 불일치」로 올렸는데,
    #   API_SPEC 은 「## 취소 — 미구현」이라 «명시»하고 README 를 가리키고 있었다.
    #   ⇒ 「적어 놓고 안 만든 것」과 「안 만들었다고 적은 것」은 다르다.
    #     감사기가 그걸 못 가리면 «정직한 문서»에 벌을 준다.
    around = ''
    for mm in re.finditer(re.escape(d), spec):
        around += spec[max(0, mm.start() - 400):mm.end() + 200]
    declared_missing = bool(re.search(r'미구현|만들지 못|만들지 않았|안 만들었', around))
    if not hit and declared_missing:
        note('⚠', '미구현', 'API_SPEC 이 «미구현이라 밝힌» 엔드포인트 — %s' % d)
        print('    ⚠ %s  (문서가 「미구현」이라 밝힘 — 어긋남 아님)' % d)
    elif not hit:
        note('★', '문서↔구현', 'API_SPEC 에 있는데 app.py 에 없다 — %s' % d)
        print('    ✗ %s' % d)
    else:
        print('    ok %s' % d)

# 도구 수 — tools.js 의 name 개수
tools_js = read('app/tools.js')
n_tools = len(set(re.findall(r"name:\s*'([a-z_]+)'", tools_js)))
print('  CURATOR 도구 실제 %d종' % n_tools)

# ═══════════ B. 문서 내부 링크 ═══════════
print('\n' + '=' * 62)
print('B. 문서 내부 링크 — «실제로 닿는가»')
print('=' * 62)
bad_links = 0
checked = 0
for md in sorted(walk('.md')):
    base = os.path.dirname(md)
    for m in re.finditer(r'\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)', read(md)):
        href = m.group(1).strip()
        if href.startswith(('http://', 'https://', 'mailto:', 'data:')):
            continue
        checked += 1
        target = os.path.normpath(os.path.join(base, href))
        if not os.path.exists(target):
            bad_links += 1
            note('★', '링크', '%s → %s (없음)' % (md, href))
            print('    ✗ %-42s → %s' % (md, href))
print('  상대 링크 %d개 검사 · 깨진 것 %d' % (checked, bad_links))

# ═══════════ C. 배포 자산 ═══════════
print('\n' + '=' * 62)
print('C. 배포 자산 — 화면이 부르는 파일이 있는가')
print('=' * 62)
missing = 0
for html, base in [('index.html', '.'), ('cardnews/demo/index.html', 'cardnews/demo')]:
    # ★<script> 를 걷어내고 본다. 실측 2026-09-10 — JS 템플릿 문자열 안의
    #   src="' + cardSrc(c) + '" 를 «정적 참조»로 오인해 거짓 양성 7건이 났다.
    #   검사기가 틀렸지 코드가 틀린 게 아니었다.
    s = re.sub(r'<script[\s\S]*?</script>', '', read(html))
    refs = set(re.findall(r'(?:src|href)="(?!https?:|#|mailto:|data:)([^"]+)"', s))
    for r in sorted(refs):
        if r.startswith('?') or r == './':
            continue
        p = os.path.normpath(os.path.join(base, r.split('?')[0]))
        if not os.path.exists(p):
            missing += 1
            note('★', '배포', '%s 가 부르는 %s 가 없다' % (html, r))
            print('    ✗ %s → %s' % (html, r))
    print('  %-28s 참조 %d개' % (html, len(refs)))
# 데모가 fetch 하는 것
for name in ('news', 'myth'):
    for p in ('cardnews/demo/runs/%s.json' % name,
              'cardnews/demo/runs/%s-manifest.json' % name):
        if not os.path.exists(p):
            missing += 1
            note('★', '배포', '데모가 부르는 %s 가 없다' % p)
    st = json.loads(read('cardnews/demo/runs/%s.json' % name) or '{}')
    for c in st.get('cards', []):
        p = 'cardnews/demo/runs/%s-cards/card-%02d.jpg' % (name, c['n'])
        if not os.path.exists(p):
            missing += 1
            note('★', '배포', '데모 카드 없음 — %s' % p)
print('  빠진 자산 %d' % missing)

# ═══════════ D. 숫자 주장 ═══════════
print('\n' + '=' * 62)
print('D. 숫자 주장 — 문서가 말한 수가 사실인가')
print('=' * 62)
idx = json.loads(read('data/works-index.json') or '[]')
facts = {'아카이브 점수': len(idx), 'CURATOR 도구': n_tools}
docs = ' '.join(read(p) for p in walk('.md'))
claims = [
    ('982점', len(idx), 982),
    ('도구 8종', n_tools, 8),
]
for label, actual, claimed in claims:
    said = label in docs
    ok = actual == claimed
    print('  %-14s 문서주장 %-4s 실제 %-4s %s' % (label, claimed, actual, 'ok' if ok else '★불일치'))
    if said and not ok:
        note('★', '숫자', '%s — 문서 %s / 실제 %s' % (label, claimed, actual))

# ═══════════ E. 미구현 선언 ═══════════
print('\n' + '=' * 62)
print('E. 문서가 «스스로» 미구현이라 적은 것')
print('=' * 62)
pat = re.compile(r'^.*(❌|미구현|미검증|안 했다|안 함|하지 않았다|못 했다).*$', re.M)
seen = set()
for md in sorted(walk('.md')):
    for line in pat.findall(read(md)):
        pass
for md in sorted(walk('.md')):
    for m in re.finditer(r'^(.*(?:❌|미구현|미검증).*)$', read(md), re.M):
        line = m.group(1).strip().lstrip('|').strip()
        key = line[:60]
        if key in seen:
            continue
        seen.add(key)
        print('  · [%s] %s' % (md, line[:96]))
        note('⚠', '미구현', '%s — %s' % (md, line[:80]))

# ═══════════ F. 위생 ═══════════
print('\n' + '=' * 62)
print('F. 위생 — 제어문자 · HTML 태그')
print('=' * 62)
ctl_total = 0
for p in walk(('.py', '.js', '.mjs', '.md', '.html', '.css', '.json')):
    s = read(p)
    bad = [hex(ord(c)) for c in s if ord(c) < 9 or 11 <= ord(c) <= 12 or 14 <= ord(c) < 32]
    if bad:
        ctl_total += len(bad)
        note('★', '위생', '%s 에 제어문자 %d개 %s' % (p, len(bad), bad[:4]))
        print('    ✗ %s — %d개' % (p, len(bad)))
print('  제어문자 총 %d' % ctl_total)

VOID = {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'path', 'circle', 'rect'}
for p in walk('.html'):
    body = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>|<!--[\s\S]*?-->', '', read(p))
    stack, bad = [], []
    for m in re.finditer(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>', body):
        cl, tag, sf = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or sf:
            continue
        if not cl:
            stack.append(tag)
        elif stack:
            t = stack.pop()
            if t != tag:
                bad.append('<%s>…</%s>' % (t, tag))
        else:
            bad.append('여는 것 없이 </%s>' % tag)
    if bad or stack:
        note('★', '위생', '%s 태그 — 교차 %s / 미닫힘 %s' % (p, bad, stack))
        print('    ✗ %s — 교차 %s · 미닫힘 %s' % (p, bad or '없음', stack or '없음'))
print('  HTML %d개 태그 검사 완료' % len(list(walk('.html'))))

# ═══════════ G. 시험 ═══════════
print()
print('=' * 62)
print('G. 시험 — 실제로 돌려 본다')
print('=' * 62)
SUITES = ['verify-tools.mjs', 'verify-loop.mjs', 'verify-mcp.mjs']
tot_pass = tot_fail = 0
for f in SUITES:
    p = os.path.join('tools', f)
    if not os.path.exists(p):
        note('★', '시험', '%s 가 없다' % f)
        continue
    try:
        out = subprocess.run(['node', p], capture_output=True, text=True,
                             encoding='utf-8', errors='replace', timeout=300).stdout
    except Exception as e:
        note('★', '시험', '%s 실행 실패 — %s' % (f, e))
        continue
    m = re.search(r'통과\s*(\d+)\s*·\s*실패\s*(\d+)', out)
    if not m:
        note('★', '시험', '%s — 결과 줄을 못 읽었다' % f)
        print('    ? %-18s 결과 미확인' % f)
        continue
    ps, fs = int(m.group(1)), int(m.group(2))
    tot_pass += ps
    tot_fail += fs
    print('    %-18s 통과 %-3d 실패 %d' % (f, ps, fs))
    if fs:
        note('★', '시험', '%s 에서 %d건 실패' % (f, fs))
print('  합계 통과 %d · 실패 %d' % (tot_pass, tot_fail))

# ═══════════ H. 수용 기준 ═══════════
print()
print('=' * 62)
print('H. 수용 기준 — PRD §8 에 «미리» 적은 것')
print('=' * 62)
try:
    out = subprocess.run(['node', 'tools/acceptance.mjs'], capture_output=True, text=True,
                         encoding='utf-8', errors='replace', timeout=600).stdout
    m = re.search(r'기준\s*(\d+)\s*충족\s*·\s*(\d+)\s*미달', out)
    if m:
        print('    충족 %s · 미달 %s' % (m.group(1), m.group(2)))
        if int(m.group(2)):
            note('★', '수용기준', '%s건 미달' % m.group(2))
    else:
        note('★', '수용기준', '결과 줄을 못 읽었다')
except Exception as e:
    note('★', '수용기준', '실행 실패 — %s' % e)

# ═══════════ I. 배포 도달 ═══════════
print()
print('=' * 62)
print('I. 배포 — 실제로 열리는가')
print('=' * 62)
BASE = 'https://kimjy0977.github.io/KDT_Works/05_module4/a_mq_N7-domain-agentic-workflow'
PATHS = ['/', '/app/style.css', '/app/ui.js', '/app/agent.js', '/app/tools.js',
         '/data/works-index.json', '/results/demo-runs.json',
         '/cardnews/demo/', '/cardnews/demo/runs/myth.json', '/cardnews/demo/runs/news.json',
         '/cardnews/demo/runs/myth-cards/card-01.jpg']
import urllib.request
for u in PATHS:
    try:
        r = urllib.request.urlopen(BASE + u, timeout=30)
        code, n = r.status, len(r.read())
    except Exception as e:
        code, n = getattr(e, 'code', 0), 0
    ok = code == 200 and n > 0
    print('    %-44s %s %d bytes' % (u, code, n))
    if not ok:
        note('★', '배포', '%s → HTTP %s' % (u, code))

# ═══════════ 요약 ═══════════
print('\n' + '=' * 62)
print('감사 요약')
print('=' * 62)
crit = [f for f in FINDINGS if f[0] == '★']
warn = [f for f in FINDINGS if f[0] == '⚠']
print('  ★고쳐야 할 것 %d건 · ⚠기록된 미구현 %d건' % (len(crit), len(warn)))
for s, k, m in crit:
    print('    ★ [%s] %s' % (k, m))
print()
sys.exit(1 if crit else 0)
