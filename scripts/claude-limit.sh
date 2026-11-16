# Sourced by the agent loops. When Claude Code stops with its usage-limit message ("You've hit
# your 5-hour limit · resets 10:50pm"), the loops wait for the reset instead of counting the run
# as an attempt on the issue.

hit_usage_limit() { grep -qE "hit your .*limit" "$1"; }

reset_time_in() { grep -oE 'resets [0-9]{1,2}(:[0-9]{2})?[ap]m' "$1" | head -n 1 | cut -d' ' -f2; }

next_occurrence() {
  local epoch now
  now="$(date +%s)"
  epoch="$(date -d "$1" +%s 2>/dev/null)" || { echo $(( now + 3600 )); return; }
  (( epoch > now )) || epoch=$(( epoch + 86400 ))
  echo $(( epoch + 60 ))
}

record_usage_limit() { next_occurrence "$(reset_time_in "$2")" > "$1/usage-limit-until"; }

usage_limit_until() { date -d "@$(cat "$1/usage-limit-until")" '+%H:%M'; }

waiting_for_usage_limit() {
  local until
  until="$(cat "$1/usage-limit-until" 2>/dev/null)" || return 1
  (( $(date +%s) < until )) && return 0
  rm -f "$1/usage-limit-until"
  return 1
}
