#!/usr/bin/env bash
# ensure_single_watcher.sh — 단일 인스턴스 감시기 보장 (watcher-arm 스킬의 결정론적 헬퍼)
# 공개 저장소용 일반 절차: 비공개 경로·키 없음. 경로·스코프는 인자로 주입한다.
#
# 사용: ensure_single_watcher.sh <감시대상경로> <lease파일경로> [폴링초=15]
#   - 살아있는 lease(PID 실존 + heartbeat 신선)면 재사용하고 종료(exit 0).
#   - stale/부재면 원자적으로 lease를 획득하고 감시 루프를 돈다.
#   - 정상 종료 시 lease를 반납한다.
set -euo pipefail

TARGET="${1:?감시 대상 경로를 주세요}"
LEASE="${2:?lease 파일 경로를 주세요}"
POLL="${3:-15}"
STALE=$(( POLL * 2 ))

now(){ date +%s; }

lease_alive(){
  [ -f "$LEASE" ] || return 1
  local pid mtime age
  pid=$(sed -n 's/^pid=//p' "$LEASE" 2>/dev/null || true)
  mtime=$(stat -c %Y "$LEASE" 2>/dev/null || echo 0)
  age=$(( $(now) - mtime ))
  # PID 실존 + heartbeat 신선도(mtime) 둘 다 만족해야 '살아있음'
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && [ "$age" -le "$STALE" ]
}

if lease_alive; then
  echo "reuse: 살아있는 감시기 lease 재사용 ($LEASE)"
  exit 0
fi

# stale/부재 → 원자적으로 lease 획득 (임시파일 후 mv -f = atomic replace)
tmp="$LEASE.$$.tmp"
printf 'pid=%s\nstarted=%s\npoll=%s\nscope=%s\n' "$$" "$(now)" "$POLL" "$TARGET" > "$tmp"
mv -f "$tmp" "$LEASE"
trap 'rm -f "$LEASE"' EXIT   # 정상 종료 시 lease 반납

echo "armed: 새 감시기 lease 획득 pid=$$ ($LEASE) 대상=$TARGET poll=${POLL}s"
last=$(stat -c %Y "$TARGET" 2>/dev/null || echo 0)
while true; do
  touch "$LEASE"                                   # heartbeat 갱신(mtime = 생존 신호)
  cur=$(stat -c %Y "$TARGET" 2>/dev/null || echo "$last")
  if [ "$cur" != "$last" ]; then
    echo "change: $TARGET 변경 감지 ($(date '+%H:%M:%S'))"
    last=$cur
  fi
  sleep "$POLL"
done
