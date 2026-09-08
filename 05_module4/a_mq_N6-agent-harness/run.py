# -*- coding: utf-8 -*-
"""내 하네스 CLI (D02 로컬 CLI · D07 세션 파일 저장).

  python run.py --workspace work --session 이름 --prompt "..."

세션(대화)과 실행 기록(무엇을 했나)을 «분리»해 저장한다 — D07.
그래야 «모델이 말한 것»과 «실제로 실행된 것»을 나중에 대조할 수 있다.
"""
import argparse
import io
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from myharness.core import (Agent, Limits, OllamaProvider, SYSTEM, Tools,  # noqa: E402
                            Workspace, ask_terminal)


def load_session(path: Path, provider: str, model: str, workspace: str):
    """재개 시 제공자·모델·작업 폴더가 다르면 «새 이름»을 요구한다 — D07."""
    if not path.exists():
        return [{"role": "system", "content": SYSTEM}]
    data = json.loads(path.read_text(encoding="utf-8"))
    stamp = data.get("stamp") or {}
    now = {"provider": provider, "model": model, "workspace": workspace}
    if stamp and stamp != now:
        raise SystemExit(
            "세션 조건이 다릅니다.\n  저장됨: %s\n  지금  : %s\n"
            "→ --session 에 «새 이름»을 주세요. (기존 기록을 덮어쓰지 않습니다)"
            % (stamp, now))
    return data.get("messages") or [{"role": "system", "content": SYSTEM}]


def main() -> int:
    parser = argparse.ArgumentParser(description="내 에이전트 하네스")
    parser.add_argument("--provider", default="ollama", choices=["ollama"])
    parser.add_argument("--model", default="qwen3.5:2b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--session")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--state-dir", default=".harness")
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--max-tool-calls", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--tool-timeout", type=float, default=30.0)
    args = parser.parse_args()

    root = Path(args.workspace).resolve()
    if not root.is_dir():
        raise SystemExit("작업 폴더가 없습니다: %s" % root)

    state = Path(args.state_dir)
    run_id = uuid.uuid4().hex
    log_path = state / "runs" / (run_id + ".jsonl")
    session_path = (state / "sessions" / (args.session + ".json")) if args.session else None

    history = None
    if session_path:
        history = load_session(session_path, args.provider, args.model, str(root))

    agent = Agent(
        provider=OllamaProvider(args.model, args.base_url),
        tools=Tools(Workspace(root), approve=ask_terminal, mode="cli",
                    tool_seconds=args.tool_timeout),
        limits=Limits(args.max_steps, args.max_tool_calls,
                      args.timeout, args.tool_timeout),
        log_path=log_path)

    result = agent.run(args.prompt, history)

    print("\n" + (result.answer or "(최종 텍스트 없음)"))
    print(json.dumps({"status": result.status,
                      "metrics": result.metrics.__dict__}, ensure_ascii=False))

    if session_path:
        session_path.parent.mkdir(parents=True, exist_ok=True)
        messages = list(history or [])
        messages.append({"role": "user", "content": args.prompt})
        if result.answer:
            messages.append({"role": "assistant", "content": result.answer})
        # 임시 파일에 쓴 뒤 «교체»한다 — 도중에 끊겨도 기존 기록이 깨지지 않는다.
        tmp = session_path.with_suffix(".json.tmp")
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"stamp": {"provider": args.provider, "model": args.model,
                                  "workspace": str(root)},
                        "messages": messages}, ensure_ascii=False, indent=1))
        tmp.replace(session_path)
        print("세션: %s" % session_path)
    print("실행 기록: %s" % log_path)
    # ⚠ 세션·기록에는 fixture 내용이 남는다. 공개 저장소에 넣지 않는다.
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
