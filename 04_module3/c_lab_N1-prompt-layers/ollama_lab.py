# 모듈3 노드1 5강 · 프롬프트 실행 실습 (Ollama 경로 · 완전 로컬)
# 목적: 같은 질문을 고정하고 "한 층만" 바꿔, 날것 출력이 어떻게 달라지는지 저장·비교.
#   1) system A         -> 01-customer-support.txt
#   2) system 만 B 로   -> 02-technical-documentation.txt
#   3) 이력만 추가       -> 03-with-history.txt   (role 배열을 그대로 전달)
import sys
from pathlib import Path
from ollama import chat

MODEL     = "llama3.2:1b"
QUESTION  = "배송일은 언제인가요?"
SYSTEM_A  = "고객 문의에 정중하게 답한다"
SYSTEM_B  = "기술 문서 톤으로 답한다"
OUT = Path(__file__).parent

def save_run(filename, messages):
    header = ["=== 보낸 messages ==="]
    for m in messages:
        header.append(f"[{m['role']}] {m['content']}")
    header += ["", "=== 응답 ==="]
    try:
        res = chat(model=MODEL, messages=messages)
        header.append(res.message.content)
    except Exception as e:
        header.append(f"[오류] {type(e).__name__}: {e}")
    (OUT / filename).write_text("\n".join(header), encoding="utf-8")
    print(f"저장: {filename}")

# 1) system A + 질문
save_run("01-customer-support.txt", [
    {"role": "system", "content": SYSTEM_A},
    {"role": "user",   "content": QUESTION},
])
# 2) system 만 B 로 바꿈 (질문 동일)
save_run("02-technical-documentation.txt", [
    {"role": "system", "content": SYSTEM_B},
    {"role": "user",   "content": QUESTION},
])
# 3) 이력만 추가 (system A 유지 + 앞선 문답을 role 배열로)
save_run("03-with-history.txt", [
    {"role": "system",    "content": SYSTEM_A},
    {"role": "user",      "content": QUESTION},
    {"role": "assistant", "content": "정확한 안내를 위해 주문번호 또는 운송장 번호를 알려 주세요."},
    {"role": "user",      "content": "운송장 번호는 아직 없어요. 주문번호가 없으면 무엇을 확인해야 하나요?"},
])
print("done")
