#!/usr/bin/env bash
# Follows the architect and developer loops live in one terminal: queue events from each loop's log,
# and what the agent writes (💬) and which tools it calls (🔧) in the running Claude session. Moves to
# each new run by itself. Ctrl+C stops it.
#
#   scripts/watch-agents.sh            # the architect and every installed developer loop
#   scripts/watch-agents.sh architect  # one loop: architect, dev (developer 1), dev2, dev3, …
#
# The session view reads Claude Code transcripts: a developer loop on opencode shows queue events only.
# Uses the same KONDOR_ARCH_CONTROL / KONDOR_ARCH_STATE overrides as the architect loop; developer
# loops use their default folders (scripts/dev-loop.sh, KONDOR_DEV_ID).
set -uo pipefail

readonly POLL_SECONDS=5
readonly CONTEXT_LINES=40

main() {
  require jq
  trap 'trap - EXIT; kill_children $$; exit' EXIT INT TERM
  case "${1:-all}" in
    architect) watch_architect ;;
    dev)       watch_dev 1 ;;
    dev[0-9]*) watch_dev "${1#dev}" ;;
    all)       watch_architect; watch_all_devs ;;
    *)         echo "usage: $0 [architect|dev|dev2|…|all]" >&2; exit 2 ;;
  esac
  wait
}

require() {
  command -v "$1" >/dev/null || { echo "$1 is missing: sudo dnf install $1" >&2; exit 1; }
}

watch_architect() {
  watch_loop architect 35 \
    "${KONDOR_ARCH_CONTROL:-$HOME/.local/share/kondor-architect-loop/control}" \
    "${KONDOR_ARCH_STATE:-$HOME/.local/state/kondor-architect-loop}/architect-loop.log"
}

# watch_dev <developer loop number>
watch_dev() {
  local suffix="" name=dev
  [[ "$1" == 1 ]] || { suffix="-$1"; name="dev$1"; }
  watch_loop "$name" 36 \
    "$HOME/.local/share/kondor-dev-loop/control$suffix" \
    "$HOME/.local/state/kondor-dev-loop$suffix/dev-loop.log"
}

watch_all_devs() {
  local id
  watch_dev 1
  for id in 2 3 4 5 6 7 8 9; do
    [[ -d "$HOME/.local/state/kondor-dev-loop-$id" ]] && watch_dev "$id"
  done
}

# watch_loop <name> <color> <control dir> <loop log>
watch_loop() {
  local tag
  tag="$(colored_tag "$1" "$2")"
  follow_loop_log "$tag" "$4" &
  follow_sessions "$tag" "$(transcript_dir "$3")" &
}

colored_tag() {
  if [[ -t 1 ]]; then printf '\e[1;%sm[%s]\e[0m' "$2" "$1"; else printf '[%s]' "$1"; fi
}

# Claude Code keeps a session's transcript under ~/.claude/projects/<cwd with / and . as ->.
transcript_dir() {
  local encoded="${1//\//-}"
  echo "$HOME/.claude/projects/${encoded//./-}"
}

follow_loop_log() {
  tail -n 3 -F "$2" 2>/dev/null | drop_idle_lines | prefix_lines "$1 ⏱"
}

drop_idle_lines() {
  grep --line-buffered -v -E 'queue: (nothing for the developer|backlog empty)'
}

follow_sessions() {
  local tag="$1" dir="$2" current="" newest follower=""
  while true; do
    newest="$(newest_transcript "$dir")"
    if [[ -n "$newest" && "$newest" != "$current" ]]; then
      stop_follower "$follower"
      start_follower "$tag" "$newest" "$current"
      current="$newest"
    fi
    sleep "$POLL_SECONDS"
  done
}

newest_transcript() {
  ls -t "$1"/*.jsonl 2>/dev/null | head -n 1
}

# Sets the caller's $follower. The first session shows its last lines for context; later ones are
# new runs, shown from the start.
start_follower() {
  local tag="$1" file="$2" previous="$3" from="-$CONTEXT_LINES"
  [[ -n "$previous" ]] && from="+1"
  echo "$tag ▶ session $(basename "$file" .jsonl)"
  ( tail -n "$from" -F "$file" 2>/dev/null | render_transcript | prefix_lines "$tag" ) &
  follower=$!
}

stop_follower() {
  [[ -n "$1" ]] || return 0
  kill_children "$1"
  kill "$1" 2>/dev/null
}

kill_children() {
  local child
  for child in $(pgrep -P "$1"); do
    kill_children "$child"
    kill "$child" 2>/dev/null
  done
}

render_transcript() {
  jq --unbuffered -r '
    def summary: .description // .command // .file_path // .pattern // .url // .skill // .prompt // "";
    select(.type == "assistant") | .message.content[]? |
    if .type == "text" then "💬 " + .text
    elif .type == "tool_use" then "🔧 " + .name + " " + (.input | summary | tostring | .[0:160])
    else empty end
  ' 2>/dev/null
}

prefix_lines() {
  sed -u "s/^/$1 /"
}

main "$@"
