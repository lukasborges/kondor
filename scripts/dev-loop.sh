#!/usr/bin/env bash
# Developer agent loop: polls the roadmap queue and runs the developer (Claude Code by default, or
# opencode) whenever the queue has a row for it. See docs/agents/developer.md → "Automatic mode".
#
#   scripts/dev-loop.sh                 # loop forever (what the systemd service runs)
#   scripts/dev-loop.sh --once          # one check (and at most one developer run), then exit
#   scripts/dev-loop.sh --dry-run       # one check, print what would run, run nothing
#   scripts/dev-loop.sh --resume <N>    # clear the pause flag of issue #N
#   scripts/dev-loop.sh --install       # create the control worktree + systemd user service, start it
#   scripts/dev-loop.sh --uninstall     # stop and remove the systemd user service
#
# Environment (all optional):
#   KONDOR_REPO          main checkout (default: the repository this script belongs to)
#   KONDOR_CONTROL_DIR   loop-owned worktree kept at origin/main (default: ~/.local/share/kondor-dev-loop/control)
#   KONDOR_STATE_DIR     lock, log, counters and pause flags (default: ~/.local/state/kondor-dev-loop)
#   KONDOR_INTERVAL      seconds between checks (default: 60)
#   KONDOR_MAX_NO_PROGRESS  developer runs on the same issue without leaving `to-dev` before pausing (default: 2)
#   KONDOR_ENGINE        claude (Claude Code, default) or opencode
#   KONDOR_CLAUDE        claude binary (default: claude in PATH, else ~/.local/bin/claude)
#   KONDOR_OPENCODE      opencode binary (default: opencode in PATH, else ~/.opencode/bin/opencode)
#   KONDOR_MODEL         model for the developer (default: sonnet with claude,
#                        deepseek/deepseek-flash with opencode; see `opencode models`)
#
# Everything is wrapped in main() so bash parses the whole file before running it: the service
# runs this script from the control worktree, which is updated to origin/main while it runs.

main() {
  set -uo pipefail

  local script_dir repo
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo="${KONDOR_REPO:-$(dirname "$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)")}"
  local control="${KONDOR_CONTROL_DIR:-$HOME/.local/share/kondor-dev-loop/control}"
  local state="${KONDOR_STATE_DIR:-$HOME/.local/state/kondor-dev-loop}"
  local interval="${KONDOR_INTERVAL:-60}"
  local max_no_progress="${KONDOR_MAX_NO_PROGRESS:-2}"
  local engine="${KONDOR_ENGINE:-claude}"
  local claude="${KONDOR_CLAUDE:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
  local opencode="${KONDOR_OPENCODE:-$(command -v opencode || echo "$HOME/.opencode/bin/opencode")}"
  local model
  case "$engine" in
    claude)   model="${KONDOR_MODEL:-sonnet}" ;;
    opencode) model="${KONDOR_MODEL:-deepseek/deepseek-flash}" ;;
    *) echo "KONDOR_ENGINE must be claude or opencode, not '$engine'" >&2; exit 2 ;;
  esac
  local log="$state/dev-loop.log"
  mkdir -p "$state"

  log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$log"; }
  notify() { command -v notify-send >/dev/null && notify-send -a "Kondor dev loop" -i kondor "$1" "${2:-}" 2>/dev/null || true; }

  ensure_control() {
    git -C "$repo" fetch -q origin || { log "fetch failed"; return 1; }
    if [[ ! -e "$control/.git" ]]; then
      mkdir -p "$(dirname "$control")"
      git -C "$repo" worktree add -q --detach "$control" origin/main || { log "cannot create $control"; return 1; }
    fi
    # Loop-owned checkout: always exactly origin/main.
    git -C "$control" checkout -q --force --detach origin/main && git -C "$control" clean -fdq
  }

  # Prints the issue number of the topmost developer row, or nothing.
  next_dev_issue() {
    (cd "$control" && bash scripts/update-queue.sh --stdout) |
      awk -F'|' '$5 ~ /developer/ { if (match($2, /#[0-9]+/)) { print substr($2, RSTART + 1, RLENGTH - 1); exit } }'
  }

  prompt_for() {
    local n="$1"
    cat <<EOF
You are the developer agent of this repository. Follow docs/agents/developer.md and AGENTS.md
(read them from origin/main). The work queue assigns issue #$n to the developer; work only on it.

1. git fetch origin. Read the spec docs/specs/$(printf '%04d' "$n")-*.md from origin/main and its
   prototype (if issue #$n is labeled bug, its body is the spec instead), and every comment on issue #$n and on its PR (gh issue view $n --comments; gh pr list --search "Closes #$n").
2. If a branch for this issue already exists (git branch --list 'feature/$n-*' 'fix/$n-*'; git worktree list),
   continue it in the worktree where it is checked out. Otherwise create a new worktree from
   origin/main as described in docs/agents/developer.md. Never commit in the current directory
   (it is the loop's read-only control checkout).
3. Do exactly the next step: implement the spec or address every open review point, build, run
   the offscreen smoke test and the spec's manual test (always with temporary XDG_CONFIG_HOME,
   XDG_DATA_HOME and XDG_CACHE_HOME as in AGENTS.md, never the real profile), rebase on origin/main, push, open or update
   the PR using .github/pull_request_template.md (Closes #$n), and switch the issue label from
   to-dev to in-review.
4. If the spec is ambiguous, comment "**Question:** ..." on the PR (or the issue) and add the
   question label instead of guessing.
5. Never edit docs/specs, prototypes, AGENTS.md or docs/agents; never merge; never push to main.
6. Commit messages and PR bodies never carry Co-Authored-By or any other attribution trailer.
7. Build with cmake --build <dir> --parallel 4, never a bare --parallel (with Makefiles it means unlimited jobs and runs the machine out of memory).

Stop after this one step and print a short report: what changed, test results, PR link, labels.
EOF
  }

  # One developer run on issue #$1, from the control checkout.
  run_developer() {
    local n="$1"
    cd "$control" || return 1
    if [[ "$engine" == opencode ]]; then
      # opencode loads docs/agents/developer.md through opencode.json.
      "$opencode" run --standalone --auto --model "$model" --title "Kondor developer #$n" "$(prompt_for "$n")"
    else
      # Claude Code does not read opencode.json: pass the role file as system prompt. Its default
      # commit/PR attribution trailers are turned off: the project forbids them (AGENTS.md).
      "$claude" -p --permission-mode auto --model "$model" --output-format text \
        --settings '{"includeCoAuthoredBy": false, "attribution": {"commit": "", "pr": ""}}' \
        --append-system-prompt "$(cat docs/agents/developer.md)" \
        "$(prompt_for "$n")"
    fi
  }

  step() {
    local dry="$1" n count_file count
    ensure_control || return 0
    n="$(next_dev_issue)"
    if [[ -z "$n" ]]; then
      log "queue: nothing for the developer"
      return 0
    fi
    if [[ -e "$state/paused-$n" ]]; then
      log "queue: #$n is for the developer but paused (scripts/dev-loop.sh --resume $n)"
      return 0
    fi
    if [[ "$dry" == 1 ]]; then
      log "dry-run: would run the developer on #$n from $control"
      prompt_for "$n"
      return 0
    fi

    local run_log="$state/run-$n-$(date +%Y%m%d-%H%M%S).log"
    log "running developer on #$n with $engine/$model (log: $run_log)"
    run_developer "$n" >"$run_log" 2>&1
    local rc=$?
    ensure_control || return 0
    count_file="$state/no-progress-$n"
    if [[ "$(next_dev_issue)" == "$n" ]]; then
      count=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 ))
      echo "$count" > "$count_file"
      log "developer run on #$n finished (rc=$rc) but #$n is still to-dev (attempt $count/$max_no_progress)"
      if (( count >= max_no_progress )); then
        touch "$state/paused-$n"
        log "pausing #$n — check $run_log, then: scripts/dev-loop.sh --resume $n"
        notify "Developer paused on #$n" "No progress after $count runs. See $run_log"
      fi
    else
      rm -f "$count_file"
      log "developer moved #$n forward (rc=$rc)"
      notify "Developer finished a step on #$n" "The issue left to-dev — architect's turn (review or question)."
    fi
  }

  install_service() {
    ensure_control || exit 1
    local unit_dir="$HOME/.config/systemd/user" unit="kondor-dev-loop.service"
    mkdir -p "$unit_dir"
    cat > "$unit_dir/$unit" <<EOF
[Unit]
Description=Kondor developer agent loop ($engine)
After=network-online.target

[Service]
Type=simple
Environment=CMAKE_BUILD_PARALLEL_LEVEL=4
MemoryHigh=12G
MemoryMax=16G
Environment=PATH=$control/scripts/bin:$HOME/.opencode/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=KONDOR_REPO=$repo
Environment=KONDOR_CONTROL_DIR=$control
Environment=KONDOR_STATE_DIR=$state
Environment=KONDOR_ENGINE=$engine
Environment=KONDOR_MODEL=$model
ExecStartPre=/usr/bin/git -C $repo fetch -q origin
ExecStartPre=/usr/bin/git -C $control checkout -q --force --detach origin/main
ExecStart=/bin/bash $control/scripts/dev-loop.sh
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now "$unit"
    log "installed and started $unit (journalctl --user -u kondor-dev-loop -f)"
  }

  case "${1:-}" in
    --once)      exec 9>"$state/lock"; flock -n 9 || { log "another loop is running"; exit 0; }; step 0 ;;
    --dry-run)   step 1 ;;
    --resume)    rm -f "$state/paused-${2:?issue number}" "$state/no-progress-${2}"; log "resumed #$2" ;;
    --install)   install_service ;;
    --uninstall) systemctl --user disable --now kondor-dev-loop.service; rm -f "$HOME/.config/systemd/user/kondor-dev-loop.service"; systemctl --user daemon-reload; log "service removed" ;;
    "")
      exec 9>"$state/lock"
      flock -n 9 || { log "another loop is running; exiting"; exit 0; }
      log "loop started (every ${interval}s, $engine model $model, repo $repo, control $control)"
      local self="${BASH_SOURCE[0]}" self_sum
      self_sum="$(sha1sum "$self" | cut -d' ' -f1)"
      while true; do
        step 0
        sleep "$interval"
        # Self-update between runs: ensure_control may have moved this file to a newer main.
        ensure_control || true
        if [[ "$(sha1sum "$self" | cut -d' ' -f1)" != "$self_sum" ]]; then
          log "dev-loop.sh changed on main; restarting with the new version"
          exec bash "$self"
        fi
      done ;;
    *) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 2 ;;
  esac
}

main "$@"
