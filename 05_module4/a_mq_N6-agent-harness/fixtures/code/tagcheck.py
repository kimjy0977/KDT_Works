# -*- coding: utf-8 -*-
"""HTML 태그 균형 검사기.

여는 태그와 닫는 태그의 개수가 맞는지 본다.
맞지 않으면 태그 이름과 개수를 돌려준다.
"""
import re

TAG = re.compile(r'<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)')


def check(html):
    """태그별 (여는 수, 닫는 수)를 세어, 어긋난 것만 dict 로 돌려준다."""
    opened = {}
    closed = {}
    for slash, name in TAG.findall(html):
        name = name.lower()
        if slash:
            closed[name] = closed.get(name, 0) + 1
        else:
            opened[name] = opened.get(name, 0) + 1

    bad = {}
    for name in set(opened) | set(closed):
        o = opened.get(name, 0)
        c = closed.get(name, 0)
        if o != c:
            bad[name] = (o, c)
    return bad


if __name__ == '__main__':
    import io
    import sys
    path = sys.argv[1]
    result = check(io.open(path, encoding='utf-8').read())
    if not result:
        print('OK')
    else:
        for name, (o, c) in sorted(result.items()):
            print('%s: 여는 %d / 닫는 %d' % (name, o, c))
