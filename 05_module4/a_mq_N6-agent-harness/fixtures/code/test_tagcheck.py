# -*- coding: utf-8 -*-
"""tagcheck 의 동작을 고정하는 검사. 표준 라이브러리만 쓴다.

실행: python test_tagcheck.py
"""
import unittest

from tagcheck import check


class TagCheckTest(unittest.TestCase):

    def test_균형이_맞으면_빈_결과(self):
        self.assertEqual(check('<p>안녕</p>'), {})

    def test_닫는_태그가_모자라면_잡아낸다(self):
        self.assertEqual(check('<p>안녕'), {'p': (1, 0)})

    def test_span을_b로_닫은_오타를_잡아낸다(self):
        # 실제로 자주 나는 실수 — span 을 열고 b 로 닫았다.
        self.assertEqual(check('<span class="hl">중요</b>'),
                         {'span': (1, 0), 'b': (0, 1)})

    def test_br_은_닫지_않아도_정상이다(self):
        # br 은 닫는 태그가 없는 것이 정상이다.
        self.assertEqual(check('<p>한 줄<br>두 줄</p>'), {})

    def test_img_도_닫지_않아도_정상이다(self):
        self.assertEqual(check('<p><img src="a.png"></p>'), {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
