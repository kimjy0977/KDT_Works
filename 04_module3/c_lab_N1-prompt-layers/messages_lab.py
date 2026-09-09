# 모듈3 노드1 5강 · 프롬프트 실행 실습 (Claude Agent SDK 경로)
# 목적: 같은 질문을 고정하고 "한 층만" 바꿔, 날것 출력이 어떻게 달라지는지 저장·비교.
#   1) system A 로 실행       -> 01-customer-support.txt
#   2) system B 로 실행       -> 02-technical-documentation.txt   (system만 바꿈)
#   3) 앞선 대화 이력을 추가   -> 03-with-history.txt              (이력만 추가)
import asyncio, sys
from pathlib import Path
from claude_agent_sdk import ClaudeAgentOptions, query

QUESTION = "배송일은 언제인가요?"
SYSTEM_A = "고객 문의에 정중하게 답한다"
SYSTEM_B = "기술 문서 톤으로 답한다"
# SDK는 messages 배열을 직접 받지 않으므로, 앞선 대화를 한 user 요청에 명시해 전달한다(강의가 짚은 방식).
HISTORY_REQUEST = (
    "앞선 대화는 다음과 같습니다.\n"
    "사용자: 배송일은 언제인가요?\n"
    "도우미: 정확한 안내를 위해 주문번호 또는 운송장 번호를 알려 주세요.\n"
    "운송장 번호는 아직 없어요. 주문번호가 없으면 무엇을 확인해야 하나요?"
)

OUT = Path(__file__).parent

async def user_messages(text):
    yield {"type": "user", "message": {"role": "user", "content": text}}

async def save_run(filename, system_prompt, user_text):
    options = ClaudeAgentOptions(system_prompt=system_prompt, max_turns=1, tools=[])
    record = [f"system_prompt: {system_prompt}", f"user: {user_text}", "", "=== 응답 ==="]
    try:
        async for event in query(prompt=user_messages(user_text), options=options):
            # AssistantMessage 안의 텍스트 블록만 뽑아 기록
            blocks = getattr(event, "content", None)
            if blocks:
                for b in blocks:
                    t = getattr(b, "text", None)
                    if t:
                        record.append(t)
    except Exception as e:
        record.append(f"[오류] {type(e).__name__}: {e}")
    (OUT / filename).write_text("\n".join(record), encoding="utf-8")
    print(f"저장: {filename}")

async def main():
    await save_run("01-customer-support.txt",        SYSTEM_A, QUESTION)         # 1) system A
    await save_run("02-technical-documentation.txt",  SYSTEM_B, QUESTION)         # 2) system만 B로
    await save_run("03-with-history.txt",             SYSTEM_B, HISTORY_REQUEST)  # 3) 이력만 추가
    print("완료 — 세 파일을 열어 비교하세요.")

if __name__ == "__main__":
    asyncio.run(main())
