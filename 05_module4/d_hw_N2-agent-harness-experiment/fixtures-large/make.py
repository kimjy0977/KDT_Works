# -*- coding: utf-8 -*-
"""2차 실험용 「큰」 fixture 저장소를 만든다.

1차 실험(7파일)의 가장 큰 한계는 «전수 열거가 싸서 탐색 범위를 좁힐 이유가 없었다»는 것이었다.
여기서는 그 조건을 실제로 만든다.

- 파일 약 300개, 최대 깊이 8
- 정답 파일은 «깊이 7»에 하나만 둔다
- settings.toml 을 서로 다른 깊이 5곳에 흩어 둔다
- 미끼: handoff 와 이름이 비슷하지만 정답이 아닌 파일들

난수를 쓰지 않는다(고정된 규칙으로만 생성) → 누가 돌려도 같은 저장소가 나온다.

사용: python3 fixtures-large/make.py
"""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'repo')

SERVICES = ['api', 'worker', 'gateway', 'billing', 'search', 'notify']
LAYERS = ['handlers', 'models', 'utils']
MODULES = ['user', 'order', 'payment', 'report', 'audit']

# 정답 — 깊이 7
ANSWER = 'docs/internal/team/ops/handoff/2026/HANDOFF-tutor.md'

# 설정 파일 — 서로 다른 깊이 5곳
CONFIGS = [
    'settings.toml',
    'src/config/settings.toml',
    'services/api/config/settings.toml',
    'services/billing/deploy/config/settings.toml',
    'services/search/internal/engine/config/settings.toml',
]

# 미끼 — 이름은 비슷한데 정답이 아니다
DECOYS = [
    'docs/archive/handoff-template.md',
    'docs/internal/team/onboarding/handoff-checklist.md',
    'services/notify/docs/HANDOFF.md.bak',
]


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)


def build():
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)

    write('README.md',
          '# big-sample\n\n'
          '서비스 여섯 개로 이루어진 예제 저장소.\n\n'
          '문서:\n'
          '- [설치 안내](docs/INSTALL.md)\n'
          '- [운영 절차](docs/OPERATIONS.md)\n'
          '- [기여 가이드](docs/CONTRIBUTING.md)\n'
          '- [보안 정책](SECURITY.md)\n')
    write('docs/INSTALL.md', '# 설치\n\nuv sync --locked\n')
    write('docs/OPERATIONS.md', '# 운영\n\n배포는 main 브랜치 푸시로 이루어진다.\n')

    # 서비스별 소스 — 6 × 3 × 5 = 90 파일
    for svc in SERVICES:
        for layer in LAYERS:
            for mod in MODULES:
                write('services/%s/src/%s/%s.py' % (svc, layer, mod),
                      '# %s / %s / %s\n\n\ndef run():\n    return "%s"\n' % (svc, layer, mod, mod))

    # 서비스별 테스트 — 6 × 5 = 30 파일
    for svc in SERVICES:
        for mod in MODULES:
            write('services/%s/tests/test_%s.py' % (svc, mod),
                  'def test_%s():\n    assert True\n' % mod)

    # 서비스별 문서 — 6 × 4 = 24 파일
    for svc in SERVICES:
        for name in ['README', 'API', 'RUNBOOK', 'CHANGELOG']:
            write('services/%s/docs/%s.md' % (svc, name),
                  '# %s · %s\n\n예제 문서.\n' % (svc, name))

    # 공용 라이브러리 — 5 × 6 = 30 파일
    for mod in MODULES:
        for name in ['__init__', 'core', 'helpers', 'errors', 'types', 'compat']:
            write('src/lib/%s/%s.py' % (mod, name), '# lib %s %s\n' % (mod, name))

    # 마이그레이션 — 40 파일
    for i in range(1, 41):
        write('db/migrations/%04d_change.sql' % i,
              '-- migration %04d\nSELECT 1;\n' % i)

    # 스크립트 — 20 파일
    for i in range(1, 21):
        write('scripts/task_%02d.sh' % i, '#!/bin/sh\necho task %02d\n' % i)

    # 깊은 문서 트리 — 정답이 묻힐 자리
    for team in ['alpha', 'beta', 'gamma']:
        for topic in ['meeting', 'spec', 'review', 'retro']:
            for n in (1, 2, 3):
                write('docs/internal/team/%s/%s/2026/note-%02d.md' % (team, topic, n),
                      '# %s %s note %02d\n\n예제 기록.\n' % (team, topic, n))

    for rel in CONFIGS:
        write(rel, 'port = 8080\n')
    for rel in DECOYS:
        write(rel, '# 미끼 — 실제 인계 문서가 아니다.\n')

    write(ANSWER,
          '# 인계 문서\n\n마지막 갱신: 초기 상태\n남은 일: (없음)\n')


def tree():
    rels = []
    for base, _, files in os.walk(ROOT):
        for f in files:
            rels.append(os.path.relpath(os.path.join(base, f), ROOT).replace('\\', '/'))
    return sorted(rels)


if __name__ == '__main__':
    build()
    rels = tree()
    io.open(os.path.join(HERE, 'tree.txt'), 'w', encoding='utf-8', newline='\n') \
        .write('\n'.join(rels) + '\n')
    depths = [r.count('/') + 1 for r in rels]
    print('파일 %d개 · 최대 깊이 %d' % (len(rels), max(depths)))
    print('정답 파일: %s (깊이 %d)' % (ANSWER, ANSWER.count('/') + 1))
    print('settings.toml: %d개' % len([r for r in rels if r.endswith('settings.toml')]))
    print('handoff 이름 포함: %d개' % len([r for r in rels if 'handoff' in r.lower()]))
    print('tree.txt %d줄' % len(rels))
