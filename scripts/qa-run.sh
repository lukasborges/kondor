#!/usr/bin/env bash
# QA agent: tests main like a user and files bug issues. See docs/agents/qa.md.
#
#   scripts/qa-run.sh              # one run, then exit (what kondor-qa.service runs)
#   scripts/qa-run.sh --dry-run    # print the commit, the scenarios, the parity mode and the prompt
#   scripts/qa-run.sh --install    # create the control worktree, kondor-qa.service and kondor-qa.timer
#   scripts/qa-run.sh --uninstall  # remove the service and the timer
#
# Environment (all optional):
#   KONDOR_REPO          main checkout (default: the repository this script belongs to)
#   KONDOR_QA_CONTROL    worktree kept at origin/main (default: ~/.local/share/kondor-qa/control)
#   KONDOR_QA_STATE      logs, last-sha, tested.tsv, screenshots (default: ~/.local/state/kondor-qa)
#   KONDOR_QA_MODEL      model (default: opus)
#   KONDOR_QA_EFFORT     Claude Code effort level (default: medium)
#   KONDOR_QA_MAX_BUGS   new issues per run (default: 5)
#   KONDOR_QA_SCENARIOS  scenarios per run (default: 5)
#   KONDOR_AGENT_FILES   folder with AGENTS.md and opencode.json (default: ~/.config/kondor-agents)
#   KONDOR_CLAUDE        claude binary (default: claude in PATH, else ~/.local/bin/claude)
#
# Everything is wrapped in main() so bash parses the whole file before running it: the control
# worktree is moved to origin/main while this script runs.

main() {
  set -uo pipefail

  local script_dir repo
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  . "$script_dir/claude-limit.sh"
  repo="${KONDOR_REPO:-$(dirname "$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)")}"
  local control="${KONDOR_QA_CONTROL:-$HOME/.local/share/kondor-qa/control}"
  local state="${KONDOR_QA_STATE:-$HOME/.local/state/kondor-qa}"
  local agent_files="${KONDOR_AGENT_FILES:-$HOME/.config/kondor-agents}"
  local claude="${KONDOR_CLAUDE:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
  local model="${KONDOR_QA_MODEL:-opus}" effort="${KONDOR_QA_EFFORT:-medium}"
  local max_bugs="${KONDOR_QA_MAX_BUGS:-5}" scenario_count="${KONDOR_QA_SCENARIOS:-5}"
  local today unit_dir="$HOME/.config/systemd/user"
  today="$(date +%F)"
  mkdir -p "$state"
  local log="$state/qa.log"

  log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$log"; }

  ensure_control() {
    git -C "$repo" fetch -q origin || { log "fetch failed"; return 1; }
    if [[ ! -e "$control/.git" ]]; then
      mkdir -p "$(dirname "$control")"
      git -C "$repo" worktree add -q --detach "$control" origin/main || { log "cannot create $control"; return 1; }
    fi
    git -C "$control" checkout -q --force --detach origin/main && git -C "$control" clean -fdq &&
      link_agent_files
  }

  link_agent_files() {
    local file
    for file in AGENTS.md opencode.json; do
      ln -sfn "$agent_files/$file" "$control/$file"
    done
  }

  commit_under_test() { git -C "$control" rev-parse origin/main; }

  is_unchanged() { [[ "$(cat "$state/last-sha" 2>/dev/null)" == "$1" ]]; }

  has_python_app() { [[ -f "$control/src/kondor/__main__.py" ]]; }

  has_cpp_app() { [[ -f "$control/CMakeLists.txt" ]]; }

  parity_mode() { has_python_app && has_cpp_app && echo on || echo off; }

  closed_issue_numbers() {
    gh issue list --repo lukasborges/kondor-browser --state closed --limit 1000 --json number --jq '.[].number' || log "gh failed listing closed issues" >&2
  }

  closed_bug_numbers() {
    gh issue list --repo lukasborges/kondor-browser --state closed --label bug --limit 1000 --json number --jq '.[].number' || log "gh failed listing closed bugs" >&2
  }

  spec_number() { basename "$1" | cut -c1-4 | sed 's/^0*//'; }

  closed_spec_scenarios() {
    local closed spec
    closed="$(closed_issue_numbers)"
    for spec in "$control"/docs/specs/*.md; do
      grep -q '^## Manual test' "$spec" || continue
      grep -qx "$(spec_number "$spec")" <<<"$closed" && echo "docs/specs/$(basename "$spec")"
    done
  }

  all_scenarios() {
    closed_spec_scenarios
    closed_bug_numbers | sed 's/^/bug-/'
  }

  last_tested() {
    awk -F'\t' -v key="$1" '$1 == key { print $2 }' "$state/tested.tsv" 2>/dev/null | tail -n 1
  }

  scenarios_by_age() {
    local key
    while read -r key; do
      printf '%s\t%s\n' "$(last_tested "$key" | grep . || echo 0000-00-00)" "$key"
    done < <(all_scenarios) | sort -s -t$'\t' -k1,1 | cut -f2
  }

  chosen_scenarios() { scenarios_by_age | head -n "$scenario_count"; }

  has_untested_scenarios() { [[ -z "$(last_tested "$(scenarios_by_age | head -n 1)")" ]]; }

  record_tested() {
    local key
    for key in $1; do printf '%s\t%s\n' "$key" "$today" >> "$state/tested.tsv"; done
  }

  prompt_for() {
    local sha="$1" scenarios="$2" parity="$3"
    cat <<PROMPT
You are the QA agent of this repository. Follow docs/agents/qa.md and AGENTS.md.

Commit under test: $sha (origin/main). The control worktree is the current directory.
Parity mode: $parity.
Scenarios for this run (spec files: their "Manual test" section; bug-N: the "Steps" of issue #N):
$(sed 's/^/  - /' <<<"$scenarios")
Run folder for screenshots, logs and fresh profiles: $state/shots-$today (create it).
Bug limit: at most $max_bugs new issues; the rest go to the run log.

Build the apps and run their offscreen smoke tests first, then the scenarios, each on its own
Xvfb display and fresh XDG folders. List skipped steps in your report. Only file issues; never edit
files, push, or comment on PRs.

Stop after the report.
PROMPT
  }

  run_qa() {
    local sha="$1" scenarios="$2" parity="$3"
    cd "$control" || return 1
    unset DISPLAY WAYLAND_DISPLAY
    "$claude" -p --permission-mode auto --model "$model" --effort "$effort" \
      --output-format stream-json --verbose \
      --settings '{"includeCoAuthoredBy": false, "attribution": {"commit": "", "pr": ""}}' \
      --append-system-prompt "$(cat docs/agents/qa.md)" \
      "$(prompt_for "$sha" "$scenarios" "$parity")" \
      | jq -rj --unbuffered -f "$script_dir/claude-progress.jq"
  }

  print_dry_run() {
    log "dry-run: would test $1, parity mode $3"
    prompt_for "$1" "$2" "$3"
  }

  step() {
    local dry="$1" sha scenarios parity
    ensure_control || return 0
    sha="$(commit_under_test)"
    if is_unchanged "$sha" && ! has_untested_scenarios; then
      log "main unchanged since the last run ($sha) and every scenario was tested"
      return 0
    fi
    scenarios="$(chosen_scenarios)"
    parity="$(parity_mode)"
    [[ -n "$scenarios" ]] || { log "no scenarios found (gh failed?), nothing run"; return 1; }
    [[ "$dry" == 1 ]] && { print_dry_run "$sha" "$scenarios" "$parity"; return 0; }
    execute_run "$sha" "$scenarios" "$parity"
  }

  execute_run() {
    local run_log
    while true; do
      run_log="$state/run-$(date +%F-%H%M).log"
      log "testing $1 (parity mode $3, log: $run_log)"
      run_qa "$1" "$2" "$3" >"$run_log" 2>&1 && { finish_run "$1" "$2"; return 0; }
      hit_usage_limit "$run_log" || { log "QA run failed, see $run_log"; return 1; }
      wait_for_usage_reset "$run_log"
    done
  }

  finish_run() {
    echo "$1" > "$state/last-sha"
    record_tested "$2"
    log "QA run finished"
  }

  wait_for_usage_reset() {
    record_usage_limit "$state" "$1"
    log "QA run hit the Claude usage limit, waiting until $(usage_limit_until "$state") to run it again"
    while waiting_for_usage_limit "$state"; do sleep 60; done
  }

  write_units() {
    mkdir -p "$unit_dir"
    cat > "$unit_dir/kondor-qa.service" <<UNIT
[Unit]
Description=Kondor QA agent (one daily run)
After=network-online.target

[Service]
WorkingDirectory=$control
Type=oneshot
MemoryHigh=12G
MemoryMax=16G
UnsetEnvironment=DISPLAY WAYLAND_DISPLAY
Environment=PATH=$control/scripts/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=KONDOR_REPO=$repo
Environment=KONDOR_QA_CONTROL=$control
Environment=KONDOR_QA_STATE=$state
EnvironmentFile=-%h/.config/kondor-dev-loop/github.env
ExecStartPre=/usr/bin/git -C $repo fetch -q origin
ExecStartPre=/usr/bin/git -C $control checkout -q --force --detach origin/main
ExecStart=/bin/bash $control/scripts/qa-run.sh
UNIT
    cat > "$unit_dir/kondor-qa.timer" <<UNIT
[Unit]
Description=Kondor QA agent, daily

[Timer]
OnCalendar=*-*-* 03:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT
  }

  install_units() {
    ensure_control || exit 1
    write_units
    systemctl --user daemon-reload
    systemctl --user enable --now kondor-qa.timer
    log "installed kondor-qa.timer (systemctl --user list-timers | grep kondor-qa)"
  }

  uninstall_units() {
    systemctl --user disable --now kondor-qa.timer
    rm -f "$unit_dir/kondor-qa.service" "$unit_dir/kondor-qa.timer"
    systemctl --user daemon-reload
    log "kondor-qa removed"
  }

  case "${1:-}" in
    "")          exec 9>"$state/lock"; flock -n 9 || { log "another QA run is active"; exit 0; }; step 0 ;;
    --dry-run)   step 1 ;;
    --install)   install_units ;;
    --uninstall) uninstall_units ;;
    *) sed -n '2,6p' "${BASH_SOURCE[0]}"; exit 2 ;;
  esac
}

main "$@"
