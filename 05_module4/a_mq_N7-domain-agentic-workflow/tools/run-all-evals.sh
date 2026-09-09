#!/bin/sh
# 세팅 5종을 «순서대로» 돌린다. 동시에 돌리면 Ollama 가 모델을 스왑하느라
# 측정하려는 속도 자체가 오염된다. GPU 는 하나다.
cd "$(dirname "$0")/.."
mkdir -p results
for s in base repair other3b smaller tight; do
  echo "════════ $s  $(date '+%H:%M:%S') ════════"
  node tools/eval.mjs "$s" --n 40 --out "results/$s.json" 2>&1
  echo
done
echo "════════ 전체 완료 $(date '+%H:%M:%S') ════════"
