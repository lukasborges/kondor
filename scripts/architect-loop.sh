#!/usr/bin/env bash
# Architect agent loop: polls the roadmap queue and runs the architect (Claude Code, headless)
# whenever the queue has a row for it, or when nothing is in flight (to promote the next issue).
# See docs/agents/architect.md → "Automatic mode".
#
#   scripts/architect-loop.sh                 # loop forever (what the systemd service runs)
#   scripts/architect-loop.sh --once          # one check (and at most one architect run), then exit
#   scripts/architect-loop.sh --dry-run       # one check, print what would run, run nothing
#   scripts/architect-loop.sh --resume <key>  # clear a pause flag (<key> = issue number or "promote")
#   scripts/architect-loop.sh --install       # create the control worktree + systemd user service, start it
#   scripts/architect-loop.sh --uninstall     # stop and remove the systemd user service
#
# Environment (all optional):
#   KONDOR_REPO           main checkout (default: the repository this script belongs to)
#   KONDOR_ARCH_CONTROL   loop-owned worktree kept at origin/main (default: ~/.local/share/kondor-architect-loop/control)
#   KONDOR_ARCH_STATE     lock, log, counters and pause flags (default: ~/.local/state/kondor-architect-loop)
#   KONDOR_ARCH_INTERVAL  seconds between checks (default: 180)
#   KONDOR_ARCH_MAX_NO_PROGRESS  runs on the same step without progress before pausing (default: 2)
#   KONDOR_ARCH_MODEL     Claude model (default: Claude Code's default)
#   KONDOR_ARCH_MERGE     0 = approve and leave the merge to a human (default), 1 = merge approved PRs automatically
#   KONDOR_CLAUDE         claude binary (default: claude in PATH, else ~/.local/bin/claude)
#
# Permissions: runs with `--permission-mode auto`, so every action still goes through Claude
# Code's safety classifier. A blocked action means no progress; after repeated attempts the
# step is paused and a desktop notification is sent.

main() {
  set -uo pipefail

  local script_dir repo
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo="${KONDOR_REPO:-$(dirname "$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)")}"
  local control="${KONDOR_ARCH_CONTROL:-$HOME/.local/share/kondor-architect-loop/control}"
  local state="${KONDOR_ARCH_STATE:-$HOME/.local/state/kondor-architect-loop}"
  local interval="${KONDOR_ARCH_INTERVAL:-180}"
  local max_no_progress="${KONDOR_ARCH_MAX_NO_PROGRESS:-2}"
  local model="${KONDOR_ARCH_MODEL:-}"
  local merge="${KONDOR_ARCH_MERGE:-0}"
  local claude="${KONDOR_CLAUDE:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
  local log="$state/architect-loop.log"
  mkdir -p "$state"

  log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$log"; }
  notify() { command -v notify-send >/dev/null && notify-send -a "Kondor architect loop" -i kondor "$1" "${2:-}" 2>/dev/null || true; }

  ensure_control() {
    git -C "$repo" fetch -q origin || { log "fetch failed"; return 1; }
    if [[ ! -e "$control/.git" ]]; then
      mkdir -p "$(dirname "$control")"
      git -C "$repo" worktree add -q --detach "$control" origin/main || { log "cannot create $control"; return 1; }
    fi
    git -C "$control" checkout -q --force --detach origin/main && git -C "$control" clean -fdq
  }

  queue() { (cd "$control" && bash scripts/update-queue.sh --stdout); }

  # Prints "<issue> <state>" for the topmost architect row (Ready first, then Waiting),
  # "promote -" when the queue has no rows at all, or nothing when it is the developer's turn.
  next_architect_step() {
    queue | awk -F'|' '
      /^\| #/ { rows++
                if ($5 ~ /architect/ && !found) {
                  match($2, /#[0-9]+/); n = substr($2, RSTART + 1, RLENGTH - 1)
                  st = $3; gsub(/ /, "", st)
                  if ($4 ~ /Answer the question/) st = "question"
                  print n, st; found = 1 } }
      END { if (!rows) print "promote -" }'
  }

  prompt_for() {
    local n="$1" st="$2" common merge_rule
    if [[ "$merge" == 1 ]]; then
      merge_rule="If it passes, approve it (gh pr review --approve), squash-merge it (gh pr merge --squash --delete-branch), then promote the next issue of the roadmap order to to-dev (see step for promotion below)."
    else
      merge_rule="If it passes, approve it (gh pr review --approve), comment on issue #$n that it is approved and waiting for the maintainer to merge, and stop: a human merges it (the next issue is promoted after the merge)."
    fi
    common="You are the architect agent of this repository, running unattended. Follow docs/agents/architect.md and AGENTS.md (read them from origin/main) strictly. Never edit src/ or qml/, never push to the developer's branches. For any change to docs/specs, prototypes or other architect-owned files, create your own git worktree from origin/main outside the current directory, commit there (English, Conventional Commits, no attribution trailers) and push to main. The current directory is the loop's read-only control checkout. Record every decision on GitHub (issue/PR comments or reviews). Stop after this one step and print a short report."
    case "$st" in
      in-review) cat <<EOF
$common

Step: review the open PR for issue #$n (gh pr list --search "Closes #$n"). Use the review checklist in docs/agents/architect.md: build the PR head in a separate worktree, run the offscreen smoke test, the spec's manual test where possible and ctest if tests exist; check the spec (docs/specs/$(printf '%04d' "$n")-*.md) acceptance criteria and out of scope, AGENTS.md conventions, private-tab privacy and visual parity with the prototype. Post the review as a PR review with concrete file:line comments.
$merge_rule
If it does not pass, submit "request changes" (gh pr review --request-changes) and switch issue #$n from in-review to to-dev.
Promotion: if the queue is now empty, add the label to-dev to the next issue of AGENTS.md "Roadmap order" that is still open and not yet started, with a short issue comment saying it is now the current issue.
EOF
      ;;
      question) cat <<EOF
$common

Step: issue #$n has the question label. Find the developer's "**Question:**" comment (on the PR for #$n if there is one, otherwise on the issue), answer it in that thread, add a | Question | Decision | row to the "Decisions" table of docs/specs/$(printf '%04d' "$n")-*.md (commit and push to main), then remove the question label from issue #$n (keep its state label).
EOF
      ;;
      to-spec) cat <<EOF
$common

Step: issue #$n is to-spec. Write or refresh its spec at docs/specs/$(printf '%04d' "$n")-<slug>.md using the template in docs/agents/architect.md, and its prototype under prototypes/ if it has UI (render it with python3 prototypes/render.py). Commit and push to main, update the issue body to a summary that links the spec, then switch the label from to-spec to to-dev.
EOF
      ;;
      promote) cat <<EOF
$common

Step: nothing is in flight (no issue is to-spec, to-dev or in-review). Promote the next issue of AGENTS.md "Roadmap order" that is still open and has no state label: add the label to-dev and post a short comment on it saying it is now the current issue and linking its spec. Do nothing else.
EOF
      ;;
    esac
  }

  step() {
    local dry="$1" next n st key count_file count run_log rc after
    ensure_control || return 0
    next="$(next_architect_step)"
    if [[ -z "$next" ]]; then
      log "queue: nothing for the architect"
      return 0
    fi
    read -r n st <<<"$next"
    [[ "$n" == "promote" ]] && st="promote"
    key="$n"
    if [[ -e "$state/paused-$key" ]]; then
      log "queue: architect step '$st' on $key is paused (scripts/architect-loop.sh --resume $key)"
      return 0
    fi
    if [[ "$dry" == 1 ]]; then
      log "dry-run: would run the architect: $st on $key"
      prompt_for "$n" "$st"
      return 0
    fi

    run_log="$state/run-$key-$st-$(date +%Y%m%d-%H%M%S).log"
    log "running architect: $st on $key (log: $run_log)"
    local args=(-p --permission-mode auto --output-format text)
    [[ -n "$model" ]] && args+=(--model "$model")
    (cd "$control" && "$claude" "${args[@]}" "$(prompt_for "$n" "$st")") >"$run_log" 2>&1
    rc=$?
    ensure_control || return 0
    after="$(next_architect_step)"
    count_file="$state/no-progress-$key"
    if [[ "$after" == "$next" ]]; then
      count=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 ))
      echo "$count" > "$count_file"
      log "architect run ($st on $key) finished (rc=$rc) without changing the queue (attempt $count/$max_no_progress)"
      if (( count >= max_no_progress )); then
        touch "$state/paused-$key"
        log "pausing architect step on $key — check $run_log, then: scripts/architect-loop.sh --resume $key"
        notify "Architect paused on $key" "No progress after $count runs ($st). See $run_log"
      fi
    else
      rm -f "$count_file"
      log "architect finished $st on $key (rc=$rc)"
      notify "Architect finished: $st on $key" "$(tail -n 3 "$run_log" | cut -c1-200)"
    fi
  }

  install_service() {
    ensure_control || exit 1
    local unit_dir="$HOME/.config/systemd/user" unit="kondor-architect-loop.service"
    mkdir -p "$unit_dir"
    cat > "$unit_dir/$unit" <<EOF
[Unit]
Description=Kondor architect agent loop (Claude Code)
After=network-online.target

[Service]
Type=simple
Environment=PATH=$HOME/.local/bin:$HOME/.opencode/bin:/usr/local/bin:/usr/bin:/bin
Environment=KONDOR_REPO=$repo
Environment=KONDOR_ARCH_CONTROL=$control
Environment=KONDOR_ARCH_STATE=$state
Environment=KONDOR_ARCH_MERGE=$merge
ExecStartPre=/usr/bin/git -C $repo fetch -q origin
ExecStartPre=/usr/bin/git -C $control checkout -q --force --detach origin/main
ExecStart=/bin/bash $control/scripts/architect-loop.sh
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now "$unit"
    log "installed and started $unit (journalctl --user -u kondor-architect-loop -f)"
  }

  case "${1:-}" in
    --once)      exec 9>"$state/lock"; flock -n 9 || { log "another loop is running"; exit 0; }; step 0 ;;
    --dry-run)   step 1 ;;
    --resume)    rm -f "$state/paused-${2:?issue number or promote}" "$state/no-progress-${2}"; log "resumed $2" ;;
    --install)   install_service ;;
    --uninstall) systemctl --user disable --now kondor-architect-loop.service; rm -f "$HOME/.config/systemd/user/kondor-architect-loop.service"; systemctl --user daemon-reload; log "service removed" ;;
    "")
      exec 9>"$state/lock"
      flock -n 9 || { log "another loop is running; exiting"; exit 0; }
      log "loop started (every ${interval}s, model ${model:-default}, merge=$merge, repo $repo, control $control)"
      local self="${BASH_SOURCE[0]}" self_sum
      self_sum="$(sha1sum "$self" | cut -d' ' -f1)"
      while true; do
        step 0
        sleep "$interval"
        ensure_control || true
        if [[ "$(sha1sum "$self" | cut -d' ' -f1)" != "$self_sum" ]]; then
          log "architect-loop.sh changed on main; restarting with the new version"
          exec bash "$self"
        fi
      done ;;
    *) sed -n '2,25p' "${BASH_SOURCE[0]}"; exit 2 ;;
  esac
}

main "$@"
