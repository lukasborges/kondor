#!/usr/bin/env bash
# Developer agent loop: polls the roadmap queue and runs the developer (Claude Code by default, or
# opencode) whenever the queue has a row for it. See docs/agents/developer.md → "Automatic mode".
#
#   scripts/dev-loop.sh                 # loop forever (what the systemd service runs)
#   scripts/dev-loop.sh --once          # one check (and at most one developer run), then exit
#   scripts/dev-loop.sh --dry-run       # one check, print what would run, run nothing
#   scripts/dev-loop.sh --resume <N>    # unblock issue #N (same as removing its `blocked` label)
#   scripts/dev-loop.sh --install       # create the control worktree + systemd user service, start it
#   scripts/dev-loop.sh --uninstall     # stop and remove the systemd user service
#
# Several developer loops can run at once, one per KONDOR_DEV_ID (1, 2, …). Each one claims the
# issue it works on, so two loops never take the same issue, and keeps it through review rounds.
# Loop 1 uses the plain names below; loop N appends "-N" to the service, state and control names:
#
#   KONDOR_DEV_ID=2 scripts/dev-loop.sh --install   # kondor-dev-loop-2.service
#
# Environment (all optional):
#   KONDOR_DEV_ID        number of this developer loop (default: 1)
#   KONDOR_DEV_CLAIMS    folder shared by all developer loops for their claims (default: ~/.local/state/kondor-dev-claims)
#   KONDOR_REPO          main checkout (default: the repository this script belongs to)
#   KONDOR_CONTROL_DIR   loop-owned worktree kept at origin/main (default: ~/.local/share/kondor-dev-loop/control)
#   KONDOR_STATE_DIR     lock, log and counters (default: ~/.local/state/kondor-dev-loop)
#   KONDOR_INTERVAL      seconds between checks (default: 60)
#   KONDOR_MAX_NO_PROGRESS  developer runs on the same issue without leaving `to-dev` before blocking it (default: 2)
#   KONDOR_ENGINE        claude (Claude Code, default) or opencode
#   KONDOR_CLAUDE        claude binary (default: claude in PATH, else ~/.local/bin/claude)
#   KONDOR_OPENCODE      opencode binary (default: opencode in PATH, else ~/.opencode/bin/opencode)
#   KONDOR_MODEL         model for the developer (default: sonnet with claude,
#                        deepseek/deepseek-flash with opencode; see `opencode models`)
#   KONDOR_AGENT_FILES   folder with AGENTS.md and opencode.json, linked into the control checkout
#                        (default: ~/.config/kondor-agents)
#   KONDOR_EFFORT        Claude Code effort level: low, medium, high, xhigh or max (default: medium)
#
# The service also reads ~/.config/kondor-dev-loop/github.env when it exists (mode 600, one line
# GH_TOKEN=<token of the developer's bot account>), so the developer's comments, PRs and pushes
# show the bot as author instead of the maintainer, and ~/.config/kondor-dev-loop/identity.env
# (GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL of that account).
#
# Everything is wrapped in main() so bash parses the whole file before running it: the service
# runs this script from the control worktree, which is updated to origin/main while it runs.

main() {
  set -uo pipefail

  local script_dir repo
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  . "$script_dir/claude-limit.sh"
  repo="${KONDOR_REPO:-$(dirname "$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)")}"
  local dev_id="${KONDOR_DEV_ID:-1}" suffix=""
  [[ "$dev_id" == 1 ]] || suffix="-$dev_id"
  local control="${KONDOR_CONTROL_DIR:-$HOME/.local/share/kondor-dev-loop/control$suffix}"
  local agent_files="${KONDOR_AGENT_FILES:-$HOME/.config/kondor-agents}"
  local state="${KONDOR_STATE_DIR:-$HOME/.local/state/kondor-dev-loop$suffix}"
  local claims="${KONDOR_DEV_CLAIMS:-$HOME/.local/state/kondor-dev-claims}"
  local unit="kondor-dev-loop$suffix.service"
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
  local effort="${KONDOR_EFFORT:-medium}"
  local log="$state/dev-loop.log"
  mkdir -p "$state" "$claims"

  log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$log"; }
  notify() { command -v notify-send >/dev/null && notify-send -a "Kondor dev loop $dev_id" -i kondor "$1" "${2:-}" 2>/dev/null || true; }

  ensure_control() {
    git -C "$repo" fetch -q origin || { log "fetch failed"; return 1; }
    if [[ ! -e "$control/.git" ]]; then
      mkdir -p "$(dirname "$control")"
      git -C "$repo" worktree add -q --detach "$control" origin/main || { log "cannot create $control"; return 1; }
    fi
    # Loop-owned checkout: always exactly origin/main.
    git -C "$control" checkout -q --force --detach origin/main && git -C "$control" clean -fdq &&
      link_agent_files
  }

  # AGENTS.md and opencode.json are not in git: link the maintainer's copies into the checkout.
  link_agent_files() {
    local file
    for file in AGENTS.md opencode.json; do
      ln -sfn "$agent_files/$file" "$control/$file"
    done
  }

  # Issue numbers of the queue rows, in queue order: all rows, or only the developer's (arg "developer").
  queue_issues() {
    (cd "$control" && bash scripts/update-queue.sh --stdout) |
      awk -F'|' -v agent="${1:-}" '/^\| #/ && $5 ~ agent { if (match($2, /#[0-9]+/)) print substr($2, RSTART + 1, RLENGTH - 1) }'
  }

  claim_owner() { cat "$claims/$1" 2>/dev/null; }

  # The issue this loop should work on. A loop keeps one issue at a time: while its claimed issue
  # is still in the queue (also during review), it works only on that one, when it is the
  # developer's turn. Otherwise it takes the topmost developer row nobody has claimed.
  next_dev_issue() {
    local own
    own="$(own_issue)"
    if [[ -n "$own" ]]; then
      still_for_developer "$own" && echo "$own"
      return
    fi
    first_unclaimed "$(queue_issues developer)"
  }

  own_issue() {
    local n
    for n in $(queue_issues); do [[ "$(claim_owner "$n")" == "$dev_id" ]] && { echo "$n"; return; }; done
  }

  first_unclaimed() {
    local n
    for n in $1; do [[ -z "$(claim_owner "$n")" ]] && { echo "$n"; return; }; done
  }

  # Claims issue $1 for this loop, under a lock so two loops cannot claim it at once, and drops
  # the claims of issues that left the queue (merged or closed). Fails when another loop has it.
  claim_issue() {
    local n="$1" open f
    open="$(queue_issues)"
    (
      flock 8
      for f in "$claims"/*; do
        [[ -e "$f" ]] && ! grep -qx "$(basename "$f")" <<<"$open" && rm -f "$f"
      done
      [[ -z "$(claim_owner "$n")" ]] && echo "$dev_id" > "$claims/$n"
      [[ "$(claim_owner "$n")" == "$dev_id" ]]
    ) 8>"$claims/.lock"
  }

  still_for_developer() { queue_issues developer | grep -qx "$1"; }

  prompt_for() {
    local n="$1"
    cat <<EOF
You are the developer agent of this repository. Follow docs/agents/developer.md and AGENTS.md
(read them from origin/main). The work queue assigns issue #$n to the developer; work only on it. Other developer agents may
work on other issues at the same time: never touch a branch, worktree or PR of another issue.

1. git fetch origin. Read the spec docs/specs/$(printf '%04d' "$n")-*.md from origin/main and its
   prototype (if issue #$n is labeled bug, its body is the spec instead), and every comment on issue #$n and on its PR (gh issue view $n --comments; gh pr list --search "Closes #$n").
   If the spec says Repository: lukasborges/kondor-extensions, the work happens in that repository:
   follow AGENTS.md → "Extensions repository" for the clone, the worktree, the PR (in that
   repository, body "Closes lukasborges/kondor-browser#$n") and how to test; its PR is found with
   gh pr list --repo lukasborges/kondor-extensions --search "lukasborges/kondor-browser#$n".
2. If a branch for this issue already exists (git branch --list 'feature/$n-*' 'fix/$n-*'; git worktree list),
   continue it in the worktree where it is checked out. Otherwise create a new worktree from
   origin/main as described in docs/agents/developer.md. Never commit in the current directory
   (it is the loop's read-only control checkout).
3. Before writing any code, load the clean-code skill (AGENTS.md → "Code quality"; that section
   wins where they differ). Do exactly the next step: implement the spec or address every open review point, run the checks
   AGENTS.md → "Which checks a change needs" asks for (ruff, mypy, the staging, the Python tests and the offscreen smoke test) and the spec's manual test (always with temporary XDG_CONFIG_HOME,
   XDG_DATA_HOME and XDG_CACHE_HOME as in AGENTS.md, never the real profile), rebase on origin/main, push, open or update
   the PR using .github/pull_request_template.md (Closes #$n), and switch the issue label from
   to-dev to in-review.
4. If the spec is ambiguous, comment "**Question:** ..." on the PR (or the issue) and add the
   question label instead of guessing.
5. Never edit docs/specs, prototypes, AGENTS.md or docs/agents; never merge; never push to main.
6. Commit messages and PR bodies never carry Co-Authored-By or any other attribution trailer.
7. Run the Python tests only with scripts/run-pytests.sh [args] (it cleans up the private D-Bus session; a bare dbus-run-session -- pytest can hang).

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
      "$claude" -p --permission-mode auto --model "$model" --effort "$effort" --output-format text \
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
    if [[ "$dry" == 1 ]]; then
      log "dry-run: developer $dev_id would run on #$n from $control"
      prompt_for "$n"
      return 0
    fi
    if waiting_for_usage_limit "$state"; then
      log "queue: Claude usage limit reached, waiting until $(usage_limit_until "$state")"
      return 0
    fi
    if ! claim_issue "$n"; then
      log "queue: #$n was just claimed by developer $(claim_owner "$n")"
      return 0
    fi

    local run_log="$state/run-$n-$(date +%Y%m%d-%H%M%S).log"
    log "running developer on #$n with $engine/$model, effort $effort (log: $run_log)"
    run_developer "$n" >"$run_log" 2>&1
    local rc=$?
    if hit_usage_limit "$run_log"; then
      record_usage_limit "$state" "$run_log"
      log "developer run on #$n hit the Claude usage limit, waiting until $(usage_limit_until "$state")"
      return 0
    fi
    ensure_control || return 0
    count_file="$state/no-progress-$n"
    if still_for_developer "$n"; then
      count=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 ))
      echo "$count" > "$count_file"
      log "developer run on #$n finished (rc=$rc) but #$n is still to-dev (attempt $count/$max_no_progress)"
      if (( count >= max_no_progress )); then
        block_issue "$n" "$run_log"
        log "blocked #$n and moved on — check $run_log, then: scripts/dev-loop.sh --resume $n"
        notify "Developer blocked on #$n" "No progress after $count runs; it moved on to another issue. See $run_log"
      fi
    else
      rm -f "$count_file"
      log "developer moved #$n forward (rc=$rc)"
      notify "Developer finished a step on #$n" "The issue left to-dev — architect's turn (review or question)."
    fi
  }

  # Marks issue $1 blocked so this loop can take another one: the `blocked` label takes it out of
  # the queue (freeing its slot for the architect to promote the next issue), the comment says why,
  # and the board card moves to Blocked. The issue keeps its `to-dev` label for when it resumes.
  block_issue() {
    local n="$1" run_log="$2"
    gh issue edit "$n" --repo lukasborges/kondor-browser --add-label blocked >/dev/null
    gh issue comment "$n" --repo lukasborges/kondor-browser --body "$(blocked_comment "$n" "$run_log")" >/dev/null
    rm -f "$claims/$n" "$state/no-progress-$n"
    move_card "$n" Blocked
  }

  blocked_comment() {
    printf '**Blocked:** developer %s made no progress on this issue after %s runs and moved on to another one. ' \
      "$dev_id" "$max_no_progress"
    printf 'The run log is `%s` on the maintainer'"'"'s machine. ' "$2"
    printf 'Remove the `blocked` label (or run `scripts/dev-loop.sh --resume %s`) once it can continue.' "$1"
  }

  unblock_issue() {
    gh issue edit "$1" --repo lukasborges/kondor-browser --remove-label blocked >/dev/null
    rm -f "$state/no-progress-$1"
    move_card "$1" "In Progress"
    log "unblocked #$1"
  }

  move_card() {
    (cd "$control" && bash scripts/board.sh "$1" "$2") >/dev/null 2>&1 || log "board: could not move #$1 to $2"
  }

  install_service() {
    ensure_control || exit 1
    local unit_dir="$HOME/.config/systemd/user"
    mkdir -p "$unit_dir"
    cat > "$unit_dir/$unit" <<EOF
[Unit]
Description=Kondor developer agent loop $dev_id ($engine)
After=network-online.target

[Service]
Type=simple
MemoryHigh=12G
MemoryMax=16G
Environment=PATH=$HOME/.opencode/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=KONDOR_REPO=$repo
Environment=KONDOR_DEV_ID=$dev_id
Environment=KONDOR_CONTROL_DIR=$control
Environment=KONDOR_STATE_DIR=$state
Environment=KONDOR_ENGINE=$engine
Environment=KONDOR_MODEL=$model
Environment=KONDOR_EFFORT=$effort
EnvironmentFile=-%h/.config/kondor-dev-loop/github.env
EnvironmentFile=-%h/.config/kondor-dev-loop/identity.env
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
    log "installed and started $unit (journalctl --user -u ${unit%.service} -f)"
  }

  case "${1:-}" in
    --once)      exec 9>"$state/lock"; flock -n 9 || { log "another loop is running"; exit 0; }; step 0 ;;
    --dry-run)   step 1 ;;
    --resume)    ensure_control && unblock_issue "${2:?issue number}" ;;
    --install)   install_service ;;
    --uninstall) systemctl --user disable --now "$unit"; rm -f "$HOME/.config/systemd/user/$unit"; systemctl --user daemon-reload; log "$unit removed" ;;
    "")
      exec 9>"$state/lock"
      flock -n 9 || { log "another loop is running; exiting"; exit 0; }
      log "developer $dev_id loop started (every ${interval}s, $engine model $model, effort $effort, repo $repo, control $control)"
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
