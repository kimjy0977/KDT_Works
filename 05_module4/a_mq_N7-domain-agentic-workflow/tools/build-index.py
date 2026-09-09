# -*- coding: utf-8 -*-
"""아카이브 색인과 평가 세트를 만든다.

입력 (읽기 전용):
  ../../04_module3/a_mq_N5-myth-rag-guide/data/works.json    982점 구조화 레코드
  ../../04_module3/a_mq_N5-myth-rag-guide/data/chunks.json   2,978청크 (meta/description/myth/insight)

출력:
  data/works-index.json   에이전트의 archive_search 가 쓰는 색인 (중복 등재 확인 · 인물/사조 연결)
  data/evalset.json       평가 세트 40점 + 정답지

★2.2MB 청크를 통째로 복제하지 않는다. 필요한 필드만 뽑는다.
★원문 폴더는 «읽기만» 한다.
"""
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(
    HERE, '..', '..', '..', '04_module3', 'a_mq_N5-myth-rag-guide', 'data'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'data'))

MYTH_KO = {'greco-roman': '그리스로마', 'norse': '북유럽', 'egyptian': '이집트',
           'mesopotamian': '메소포타미아', 'hindu': '힌두', 'chinese': '중국'}

# meta 문장에서 사실을 뽑는 패턴. 정답지의 근거이므로 «원문 그대로» 잡는다.
PAT = {
    'origTitle': r'\(원제\s*(.+?)\)\.\s',
    'origTitle2': r'\(원제\s*([^)]+)\)',
    'inception': r'제작 시기는\s*([^.]{1,80})',
    'material': r'매체는\s*([^.]{1,50})',
    'size': r'크기는\s*([^.]{1,60})',
    'collection': r'([^.]{2,70})에 소장되어 있다',
    'era': r'사조는\s*([^.]{1,50})',
    'people': r'등장 인물은\s*([^.]{1,80})',
}


def parse_meta(text):
    """meta 문장을 필드로 가른다. 없으면 None — «없음»을 «빈 문자열»로 위장하지 않는다."""
    out = {}
    m = re.search(PAT['origTitle'], text) or re.search(PAT['origTitle2'], text)
    if m:
        # 「Mercury (Flying Mercury」처럼 괄호가 잘린 꼬리를 정리
        out['origTitle'] = re.sub(r'\s*\([^)]*$', '', m.group(1)).strip()
    for key in ('inception', 'material', 'size', 'collection', 'era', 'people'):
        m = re.search(PAT[key], text)
        if m:
            out[key] = m.group(1).strip()
    return out


def query_variants(orig):
    """제목 하나에서 «질의 후보»를 만든다. 실측에서 30%→60%를 만든 바로 그 변형."""
    if not orig:
        return []
    v = [orig]
    a = re.sub(r'\s*\([^)]*\)', '', orig).strip()          # 괄호 통째로 제거
    if a and a not in v:
        v.append(a)
    b = re.split(r'\s*[—–]\s*|\s+-\s+|,\s(?=[A-Z])', a)[0].strip()   # 부제·쉼표 절단
    if b and b not in v:
        v.append(b)
    inner = re.search(r'\(([^)]{3,})\)', orig)              # 괄호 «안»을 제목으로
    if inner and inner.group(1).strip() not in v:
        v.append(inner.group(1).strip())
    return v


def main():
    works = json.load(io.open(os.path.join(SRC, 'works.json'), encoding='utf-8'))
    chunks = json.load(io.open(os.path.join(SRC, 'chunks.json'), encoding='utf-8'))

    sect = collections.defaultdict(dict)
    for c in chunks:
        sect[c['id'].split('#')[0]][c['section']] = c

    index = []
    for w in works:
        slug = w['slug']
        s = sect.get(slug, {})
        meta_text = s.get('meta', {}).get('text', '')
        parsed = parse_meta(meta_text) if meta_text else {}
        myth = s.get('meta', {}).get('mythology') or slug.split('-')[0]
        index.append({
            'slug': slug,
            'url': w['url'],
            'title': w['title'],
            'origTitle': parsed.get('origTitle'),
            'artist': w['artist'],
            'era': w['era'],
            'people': w.get('people') or [],
            'myth': myth,
            'mythKo': MYTH_KO.get(myth, myth),
            'inception': parsed.get('inception'),
            'material': parsed.get('material'),
            'collection': parsed.get('collection'),
            'hasDesc': 'description' in s,
            'hasMyth': 'myth' in s,
            'hasInsight': 'insight' in s,
        })

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'works-index.json')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(index, ensure_ascii=False, separators=(',', ':')))
    print('works-index.json  %d점  %.0f KB' % (len(index), os.path.getsize(p) / 1024.0))

    # ── 평가 세트: 신화별 비율대로 층화 표본 40점.
    #    난수를 쓰지 않는다 — 같은 입력이면 같은 표본이 나와야 재현이 된다.
    by = collections.defaultdict(list)
    for it in index:
        if it['origTitle']:            # 원제가 없으면 외부 검색 자체가 불가 → 제외
            by[it['myth']].append(it)
    total = sum(len(v) for v in by.values())
    quota, picked = {}, []
    for m in sorted(by, key=lambda k: -len(by[k])):
        quota[m] = max(2, round(40.0 * len(by[m]) / total))
    for m in sorted(quota):
        pool = sorted(by[m], key=lambda x: x['slug'])
        step = max(1, len(pool) // quota[m])
        picked += pool[::step][:quota[m]]
    picked = picked[:40]

    evalset = []
    for it in picked:
        evalset.append({
            'id': it['slug'],
            'input': {'title': it['origTitle'], 'artist': it['artist']},
            'queries': query_variants(it['origTitle']),
            'truth': {k: it[k] for k in
                      ('title', 'origTitle', 'artist', 'era', 'people',
                       'inception', 'material', 'collection', 'url', 'mythKo')},
        })
    p = os.path.join(OUT, 'evalset.json')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(evalset, ensure_ascii=False, indent=1))
    print('evalset.json      %d점  %.0f KB' % (len(evalset), os.path.getsize(p) / 1024.0))
    print('  신화 분포:', dict(collections.Counter(
        next(i['mythKo'] for i in index if i['slug'] == e['id']) for e in evalset)))

    # ── 색인 품질 보고. «채워졌다»를 세지 않고 «비었다»를 센다.
    print('\n필드 채움률 (n=%d)' % len(index))
    for k in ('origTitle', 'inception', 'material', 'collection', 'people', 'era'):
        n = sum(1 for i in index if i[k])
        print('  %-11s %4d  %3.0f%%   (빈 칸 %d)' % (k, n, n * 100.0 / len(index), len(index) - n))

    assert not [c for c in json.dumps(index, ensure_ascii=False)
                if ord(c) < 32 and c not in '\n\t'], '제어문자 발견'
    print('\n제어문자 0 · 원본 폴더 수정 없음(읽기만)')


main()
