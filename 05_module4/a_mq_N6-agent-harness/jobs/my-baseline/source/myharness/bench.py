# -*- coding: utf-8 -*-
"""평가 연결부 — 고정 10문항 평가기와 «내 하네스»를 잇는다.

    uv run python -m harness_lab.bench --name my-baseline \\
        --agent my_agent:solve_task --provider ollama --model qwen3.5:2b

★어댑터는 «연결»만 한다 — 모델·도구 반복을 수행하는 주체는
  `m4n6-하네스설계키트/myharness/core.py` 의 `Agent` 다(12강 요구).
  이 파일은 원본 작업 지시·시행 폴더·실행 한도를 내 프로그램에 «전달»하고
  결과·상태·지표를 평가기 계약으로 «돌려주는» 일만 한다.

설명할 것(12강)
  · 작업 디렉터리 — 시행별 `workspace` 를 내 Workspace 루트로 쓴다
  · 종료 코드   — 평가기는 종료 코드가 아니라 반환 dict 의 status 를 본다
  · 출력 파싱   — 없음. 내 Agent 가 구조화된 결과를 그대로 돌려준다
  · 시간 초과   — 내 Agent 의 total_seconds 한도로 처리하고 status 로 표시한다
  · 사용량 미관측 — Ollama 가 사용량을 주지 않으므로 `usage_known=False`,
                   토큰 항목은 «0 이 아니라 None».
"""
from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path

from .core import (Agent, Limits, OllamaProvider, Tools, Workspace,
                   always_allow, system_prompt)


async def solve_task(instruction: str, workspace: Path, logs_dir: Path,
                     options: dict) -> dict:
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    if options.get("provider") != "ollama":
        # 지원하지 않는 조건을 «조용히 넘기지» 않는다.
        raise ValueError("내 하네스는 현재 ollama 만 지원한다 (D04·D08)")

    limits = Limits(
        max_steps=options["max_steps"],
        max_tool_calls=options["max_steps"] * 4,
        total_seconds=options["max_seconds"],
        tool_seconds=options["command_timeout"] + 2,
    )
    tools = Tools(Workspace(workspace), approve=always_allow, mode="bench",
                  tool_seconds=limits.tool_seconds)
    agent = Agent(OllamaProvider(options["model"]), tools, limits,
                  log_path=logs_dir / "events.jsonl")

    # 평가 작업 «복사본» 안의 변경은 사전 허용이다(9강의 두 승인 정책).
    # 이것이 «사용자 컴퓨터의 다른 파일 접근»까지 뜻하지는 않는다.
    prompt = instruction
    if options.get("task_cwd"):
        prompt += ("\n\n작업 기준 폴더(작업 폴더 상대): " + options["task_cwd"])

    history = [{"role": "system", "content": system_prompt("bench")}]
    result = await asyncio.to_thread(agent.run, prompt, history)

    # 대화도 남긴다 — «모델이 주장한 것»과 «실제 실행»을 나중에 대조하기 위해서다.
    io.open(logs_dir / "trial.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"status": result.status, "answer": result.answer,
                    "metrics": result.metrics.__dict__},
                   ensure_ascii=False, indent=1))

    m = result.metrics
    return {
        # ★completed 는 «텍스트를 돌려줬다»는 뜻이지 «정답»이 아니다.
        #   정답 여부는 «이후 채점기»가 판정한다.
        "status": "completed" if result.status == "completed" else result.status,
        "answer": result.answer,
        "metrics": {
            "model_calls": m.model_calls,
            "tool_calls": m.tool_calls,
            "tool_errors": m.tool_errors,
            "elapsed_seconds": m.elapsed_seconds,
            "usage_known": False,
        },
        # 관측하지 못한 값은 «0 이 아니라 None» 이다.
        "n_input_tokens": None,
        "n_output_tokens": None,
        "n_cache_tokens": None,
        "cost_usd": None,
    }
