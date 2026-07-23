#!/usr/bin/env bash
# ensure_single_watcher.sh — 단일 인스턴스 감시기 보장 (watcher-arm 스킬의 결정론적 헬퍼)
# 공개 저장소용 일반 절차: 비공개 경로·키 없음. 경로·스코프는 인자로 주입한다.
#
# 사용: ensure_single_watcher.sh <감시대상경로> <lease파일경로> [폴링초=15]
#   - 획득은 mkdir(원자적 배타 락)로 직렬화 → 동시 시작에서도 실행 writer는 최대 1개.
#   - lease는 owner token으로 소유권을 표기하고, cleanup은 owner 일치 시에만.
#   - 변경 감지는 재귀 스냅샷(하위 파일 수정·신규·rename/삭제·하위경로 변경 포함).
set -euo pipefail

TARGET="${1:?감시 대상 경로를 주세요}"
LEASE="${2:?lease 파일 경로를 주세요}"
POLL="${3:-15}"
STALE=$(( POLL * 2 ))
LOCKDIR="$LEASE.lock"
OWNER="$$_$(date +%s%N 2>/dev/null || date +%s)_${RANDOM}${RANDOM}"

now(){ date +%s; }
lease_field(){ sed -n "s/^$1=//p" "$LEASE" 2>/dev/null | head -1; }

lease_alive(){
  [ -f "$LEASE" ] || return 1
  local pid mtime age
  pid=$(lease_field pid)
  mtime=$(stat -c %Y "$LEASE" 2>/dev/null || echo 0)
  age=$(( $(now) - mtime ))
  # PID 실존 + heartbeat 신선도(mtime) 둘 다여야 '살아있음'
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && [ "$age" -le "$STALE" ]
}

# ---- 원자 락: mkdir은 존재 시 실패 = 배타적 뮤텍스 ----
acquire_lock(){
  local tries=0 lmtime lage
  while ! mkdir "$LOCKDIR" 2>/dev/null; do
    lmtime=$(stat -c %Y "$LOCKDIR" 2>/dev/null || echo 0)
    lage=$(( $(now) - lmtime ))
    [ "$lage" -gt "$STALE" ] && rm -rf "$LOCKDIR" 2>/dev/null || true   # stale 락 회수
    tries=$((tries+1)); [ "$tries" -gt 200 ] && return 1
    sleep 0.05
  done
  return 0
}
release_lock(){ rmdir "$LOCKDIR" 2>/dev/null || rm -rf "$LOCKDIR" 2>/dev/null || true; }

# ---- 재귀 스냅샷: 하위 전체의 (타입·경로·크기·mtime) 해시 ----
snapshot(){
  if [ -d "$TARGET" ]; then
    find "$TARGET" -printf '%y %p %s %T@\n' 2>/dev/null | LC_ALL=C sort | md5sum | cut -d' ' -f1
  elif [ -e "$TARGET" ]; then
    stat -c '%s %Y' "$TARGET" 2>/dev/null | md5sum | cut -d' ' -f1
  else
    echo absent
  fi
}

cleanup(){ [ -f "$LEASE" ] && [ "$(lease_field owner)" = "$OWNER" ] && rm -f "$LEASE" || true; }

# ==== 임계구역: 락 획득 → lease 재검사 → 기록 ====
acquire_lock || { echo "error: 락 획득 실패 ($LOCKDIR)"; exit 1; }
if lease_alive; then
  release_lock
  echo "reuse: 살아있는 감시기 재사용 (owner=$(lease_field owner) pid=$(lease_field pid))"
  exit 0
fi
tmp="$LEASE.$OWNER.tmp"
printf 'owner=%s\npid=%s\nstarted=%s\npoll=%s\nscope=%s\n' "$OWNER" "$$" "$(now)" "$POLL" "$TARGET" > "$tmp"
mv -f "$tmp" "$LEASE"
trap cleanup EXIT INT TERM
release_lock

echo "armed: owner=$OWNER pid=$$ 대상=$TARGET poll=${POLL}s"
last=$(snapshot)
while true; do
  # 소유권 잃었으면(다른 owner에게 회수됨) 조용히 종료 → 좀비 이중감시 방지
  [ "$(lease_field owner)" = "$OWNER" ] || { echo "yield: lease owner 변경, 종료"; exit 0; }
  touch "$LEASE"                       # heartbeat (mtime 갱신 = 생존 신호)
  cur=$(snapshot)
  if [ "$cur" != "$last" ]; then echo "change: $TARGET 변경 감지 ($(date '+%H:%M:%S'))"; last=$cur; fi
  sleep "$POLL"
done
