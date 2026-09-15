"""검수가 «실제로 작동하는지» 확인한다 — 9강 더 해보기 ②.

★교안의 경고:
  「검수처럼 평소에 아무 일도 안 하는 장치는 «고장 나도 티가 나지 않습니다».
   일부러 틀린 입력을 넣어 잡히는지 확인하는 것을 «습관»으로 삼아야 합니다.」

  그래서 verify_fail 이 0이라는 것은 «좋은 소식»이 아니라
  «확인이 필요하다»는 신호다.

  python 01_test_verify.py
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

from graph import verify, llm_backend  # noqa: E402

BODY = (
    "OpenAI announced a new model today. The company said the context window "
    "has doubled to 400,000 tokens, and pricing stays at $3 per million input tokens. "
    "The rollout begins next week for Plus subscribers. "
    "CEO Sam Altman said the model was trained on a new cluster in Texas. "
    "The company raised $60 million just three months after its previous round."
)

CASES = [
    # (이름, headline, summary, 기대)
    ("정상 — 사실만",
     "오픈AI, 컨텍스트 40만 토큰으로 두 배 확대",
     "오픈AI가 새 모델을 공개했습니다. 컨텍스트 한도가 40만 토큰으로 두 배 늘었습니다. "
     "가격은 입력 100만 토큰당 3달러로 유지됩니다.",
     True),
    ("★번역·단위 환산 — 통과해야 «맞다»",
     "오픈AI, 6000만 달러 투자 유치 3개월 만에 새 모델",
     "오픈AI가 새 모델을 공개했습니다. 직전 라운드 3개월 뒤 6000만 달러를 모았습니다. "
     "컨텍스트는 40만 토큰입니다.",
     True),
    ("★가짜 숫자 — 잡아야 한다",
     "오픈AI, 컨텍스트 400만 토큰으로 확대",
     "오픈AI가 새 모델을 공개했습니다. 컨텍스트 한도가 400만 토큰으로 열 배 늘었습니다. "
     "가격은 100만 토큰당 300달러입니다.",
     False),
    ("★없는 고유명사 — 잡아야 한다 (실측 환각 재현)",
     "오픈AI, 디플로메트당과 협약 체결",
     "오픈AI가 새 모델을 공개했습니다. 디플로메트당 소속 의원들이 이 모델을 검토했습니다. "
     "구글 딥마인드가 공동 개발에 참여했습니다.",
     False),
    ("★문장이 끊김 — 잡아야 한다 (실측 결함 재현)",
     "오픈AI",
     "오픈AI가 새 모델을 공개했습니다. 컨텍스트 한도가 두 배로 늘었는데 이에 대해서는",
     False),
]


def main():
    print("=" * 78)
    print("검수 장치 점검 · 백엔드 %s" % llm_backend())
    print("=" * 78)
    drafted = [{"headline": h, "summary": s, "body": BODY, "source": "test",
                "url": "https://example.com/%d" % i, "why": "-", "topic": "모델·API"}
               for i, (_, h, s, _) in enumerate(CASES)]
    out = verify({"drafted": drafted})
    passed_urls = {d["url"] for d in out["verified"]}

    hit = 0
    for i, (name, h, s, want_ok) in enumerate(CASES):
        got_ok = ("https://example.com/%d" % i) in passed_urls
        mark = "OK  " if got_ok == want_ok else "★MISS"
        if got_ok == want_ok:
            hit += 1
        print("%s %-42s 기대 %-6s 실제 %s"
              % (mark, name, "합격" if want_ok else "불합격", "합격" if got_ok else "불합격"))
    print("-" * 78)
    print("%d / %d 일치" % (hit, len(CASES)))
    if hit < len(CASES):
        print()
        print("★검수가 놓친 것이 있다. verify_fail 이 0이어도 «안전하다는 뜻이 아니다».")
    for line in out["log"]:
        print("   " + line)


if __name__ == "__main__":
    main()
