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
#   KONDOR_ARCH_INTERVAL  seconds between checks (default: 60)
#   KONDOR_ARCH_MAX_NO_PROGRESS  runs on the same step without progress before pausing (default: 2)
#   KONDOR_ARCH_MAX_IN_FLIGHT    issues in to-spec, to-dev or in-review at once, one per developer
#                         loop (default: 2). An issue is promoted only when every issue on its
#                         "Depends on:" line (issue body) is closed.
#   KONDOR_ARCH_MODEL     Claude model (default: opus; empty = Claude Code's default)
#   KONDOR_ARCH_EFFORT    Claude Code effort level: low, medium, high, xhigh or max (default: medium)
#   KONDOR_ARCH_AUTOMERGE 1 = the architect squash-merges approved PRs whose build passed (default, the
#                         maintainer's decision), 0 = approve, add `approved` and leave the merge to a human
#   KONDOR_AGENT_FILES    folder with AGENTS.md and opencode.json, linked into the control checkout
#                         (default: ~/.config/kondor-agents)
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
  local agent_files="${KONDOR_AGENT_FILES:-$HOME/.config/kondor-agents}"
  local state="${KONDOR_ARCH_STATE:-$HOME/.local/state/kondor-architect-loop}"
  local interval="${KONDOR_ARCH_INTERVAL:-60}"
  local max_no_progress="${KONDOR_ARCH_MAX_NO_PROGRESS:-2}"
  local max_in_flight="${KONDOR_ARCH_MAX_IN_FLIGHT:-2}"
  local model="${KONDOR_ARCH_MODEL-opus}"
  local effort="${KONDOR_ARCH_EFFORT:-medium}"
  local merge="${KONDOR_ARCH_AUTOMERGE:-1}"
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

  queue() { (cd "$control" && bash scripts/update-queue.sh --stdout); }

  # Prints "<issue> <state>" for the topmost architect row (Ready first, then Waiting),
  # "promote -" when no row is the architect's and fewer than max_in_flight issues are in flight,
  # or nothing when it is the developers' turn.
  next_architect_step() {
    queue | awk -F'|' -v max="$max_in_flight" '
      /^\| #/ { rows++
                if ($5 ~ /architect/ && !found) {
                  match($2, /#[0-9]+/); n = substr($2, RSTART + 1, RLENGTH - 1)
                  st = $3; gsub(/ /, "", st)
                  if ($4 ~ /Answer the question/) st = "question"
                  print n, st; found = 1 } }
      END { if (!found && rows < max) print "promote -" }'
  }

  prompt_for() {
    local n="$1" st="$2" common merge_rule
    if [[ "$merge" == 1 ]]; then
      merge_rule="If it passes, approve it (gh pr review --approve; if GitHub refuses because the same account opened the PR, submit a comment review that starts with \"Verdict: APPROVE\") and add the label approved to issue #$n. Then check CI with gh pr checks <PR> --repo lukasborges/kondor: the build check must pass (ignore the queue check). If it passed, merge with exactly: gh pr merge <PR> --repo lukasborges/kondor --squash --body \"Closes #$n\" (the maintainer decided that the architect merges approved PRs; the explicit --body replaces GitHub's default squash message, which appends Co-authored-by trailers, and the maintainer wants no attribution trailers), and promote the next issue of the roadmap order to to-dev (see promotion below). If the build is still running, stop: the next run merges it. If the build failed, request changes instead. If the merge command is refused by a permission check, comment on issue #$n that the PR is approved and needs the maintainer to merge it, and stop."
    else
      merge_rule="If it passes, approve it (gh pr review --approve; if GitHub refuses because the same account opened the PR, submit a comment review that starts with \"Verdict: APPROVE\"), add the label approved to issue #$n (keep in-review), comment on issue #$n that it is approved and waiting for the maintainer to merge, and stop: a human merges it (the next issue is promoted after the merge)."
    fi
    common="You are the architect agent of this repository, running unattended. Follow docs/agents/architect.md (from origin/main) and AGENTS.md (the maintainer's local file, linked into the current directory and not in git) strictly. To change AGENTS.md (for example the roadmap order), edit $agent_files/AGENTS.md and never commit it. Never edit src/ or qml/, never push to the developer's branches. For any change to docs/specs, prototypes or other architect-owned files, create your own git worktree from origin/main outside the current directory, commit there (English, Conventional Commits, no attribution trailers) and push to main. The current directory is the loop's read-only control checkout. Record every decision on GitHub (issue/PR comments or reviews). Every issue you create must be put on the project board with scripts/board.sh <N>. Build with cmake --build <dir> --parallel 4, never a bare --parallel (with Makefiles it means unlimited jobs and runs the machine out of memory). Stop after this one step and print a short report."
    case "$st" in
      in-review) cat <<EOF
$common

Step: review the open PR for issue #$n (gh pr list --search "Closes #$n"; if the spec says Repository: lukasborges/kondor-extensions, the PR is in that repository instead: gh pr list --repo lukasborges/kondor-extensions --search "lukasborges/kondor#$n", and you review, check CI and merge it there with --repo lukasborges/kondor-extensions and --body "Closes lukasborges/kondor#$n", as AGENTS.md → "Extensions repository" says). If issue #$n already has the label approved, skip the review and only do the CI check and merge part below. Load the clean-code skill first and check the PR against it and AGENTS.md → "Code quality" (that section wins where they differ). Use the review checklist in docs/agents/architect.md: run the checks AGENTS.md → "Which checks a change needs" asks for (build the PR head in a separate worktree, run the offscreen smoke test and ctest only when the C++ checks apply), the spec's manual test where possible (always with temporary XDG_CONFIG_HOME, XDG_DATA_HOME and XDG_CACHE_HOME as in AGENTS.md, never the maintainer's real profile); check the spec (docs/specs/$(printf '%04d' "$n")-*.md, or the issue body for a bug issue) acceptance criteria and out of scope, AGENTS.md conventions, private-tab privacy and visual parity with the prototype. Post the review as a PR review with concrete file:line comments.
$merge_rule
If it does not pass, submit "request changes" (gh pr review --request-changes; or a comment review starting with \"Verdict: REQUEST CHANGES\" if GitHub refuses), remove the approved label if present and switch issue #$n from in-review to to-dev.
Do not promote another issue: the loop does that in its own step.
EOF
      ;;
      question) cat <<EOF
$common

Step: issue #$n has the question label. Find the developer's "**Question:**" comment (on the PR for #$n if there is one, otherwise on the issue), answer it in that thread, add a | Question | Decision | row to the "Decisions" table of docs/specs/$(printf '%04d' "$n")-*.md (commit and push to main; for a bug issue, which has no spec file, the answer comment is the record), then remove the question label from issue #$n (keep its state label).
EOF
      ;;
      prespec) cat <<EOF
$common

Step: nothing else needs you, so write the spec of issue #$n ahead of time: it is the next issue of AGENTS.md "Roadmap order" without one, and it will be promoted later, when its "Depends on:" issues are closed. Write docs/specs/$(printf '%04d' "$n")-<slug>.md with the template in docs/agents/architect.md, and its prototype under prototypes/ if it has UI (render it with python3 prototypes/render.py). Commit and push to main, then update the issue body to a summary that links the spec, keeping its "**Depends on:**" line. Do not add, remove or change any label, and do not promote it: the loop does that when its dependencies are closed.
EOF
      ;;
      to-spec) cat <<EOF
$common

Step: issue #$n is to-spec. Write or refresh its spec at docs/specs/$(printf '%04d' "$n")-<slug>.md using the template in docs/agents/architect.md, and its prototype under prototypes/ if it has UI (render it with python3 prototypes/render.py). Commit and push to main, update the issue body to a summary that links the spec, then switch the label from to-spec to to-dev.
EOF
      ;;
      promote) cat <<EOF
$common

Step: promote issue #$n, chosen by the loop (an open bug by priority, or the next open issue of AGENTS.md "Roadmap order" whose "Depends on:" issues are all closed; another issue may already be in flight, worked on by another developer loop). If it is a roadmap issue with no spec yet (no docs/specs/<NNNN>-*.md), first write its spec and, if it has UI, its prototype, using the template in docs/agents/architect.md (render prototypes with python3 prototypes/render.py; commit and push to main; update the issue body to a summary that links the spec, keeping its "Depends on:" line). Then add the label to-dev, post a short comment on it saying it is now in development and linking its spec (a bug issue is its own spec), and run scripts/board.sh $n "In Progress" to update the project board. Do nothing else.
EOF
      ;;
    esac
  }

  # Prints the issue the promote step should promote, or nothing: the open bug with the highest
  # priority (oldest first) that has no state label, else the first open issue of AGENTS.md
  # "Roadmap order" that has no state label and whose "Depends on:" issues are all closed.
  next_promotion() {
    local issues
    issues="$(open_issues)" || return 0
    first_bug "$issues" || first_roadmap_issue "$issues"
  }

  # One line per open issue: "<number> <started> <bug> <priority rank> <dependencies, comma-separated>".
  open_issues() {
    gh issue list --repo lukasborges/kondor --state open --limit 500 --json number,labels,body -q '
      .[] | [.labels[].name] as $l
      | "\(.number) \($l | any(. == "to-spec" or . == "to-dev" or . == "in-review"))"
        + " \($l | any(. == "bug"))"
        + " \(if ($l | index("priority: high")) then 0 elif ($l | index("priority: medium")) then 1 elif ($l | index("priority: low")) then 2 else 3 end)"
        + " \([.body | split("\n")[] | select(test("^\\W*Depends on\\W"; "i")) | scan("#([0-9]+)")[0]] | join(",") | if . == "" then "-" else . end)"'
  }

  first_bug() {
    awk '$2 == "false" && $3 == "true"' <<<"$1" | sort -k4,4n -k1,1n | awk '{ print $1; found = 1; exit } END { exit !found }'
  }

  first_roadmap_issue() {
    local issues="$1" n deps
    while read -r n; do
      deps="$(awk -v n="$n" '$1 == n && $2 == "false" { print $5; found = 1 } END { exit !found }' <<<"$issues")" || continue
      dependencies_closed "$deps" "$issues" && { echo "$n"; return 0; }
    done < <(roadmap_order)
    return 1
  }

  roadmap_order() {
    awk '/^### Roadmap order/ {on = 1; next} on && /^#/ {exit} on' "$control/AGENTS.md" \
      | grep -oE '#[0-9]+' | tr -d '#' | awk '!seen[$0]++'
  }

  # True when none of the comma-separated issues is still open.
  dependencies_closed() {
    local dep
    [[ "$1" == "-" ]] && return 0
    for dep in ${1//,/ }; do
      awk -v d="$dep" '$1 == d { found = 1 } END { exit !found }' <<<"$2" && return 1
    done
    return 0
  }

  # The first issue of AGENTS.md "Roadmap order" that is open, not started, and has no spec file
  # on main yet, or nothing.
  next_unspecified() {
    local issues n
    issues="$(open_issues)" || return 0
    while read -r n; do
      awk -v n="$n" '$1 == n && $2 == "false" { found = 1 } END { exit !found }' <<<"$issues" || continue
      compgen -G "$control/docs/specs/$(printf '%04d' "$n")-*.md" >/dev/null && continue
      echo "$n"
      return 0
    done < <(roadmap_order)
  }

  log_idle_once() {
    [[ -e "$state/idle" ]] && return 0
    touch "$state/idle"
    log "queue: nothing for the architect (no review or question, nothing to promote, every upcoming roadmap issue has a spec)"
  }

  # True when issue $1 has the approved label and its PR's build check has not finished yet.
  # The PR may be in the extensions repository (AGENTS.md → "Extensions repository").
  build_pending() {
    local n="$1" pr prrepo=lukasborges/kondor
    gh issue view "$n" --repo lukasborges/kondor --json labels -q '.labels[].name' 2>/dev/null \
      | grep -qx approved || return 1
    pr="$(gh pr list --repo lukasborges/kondor --state open --search "Closes #$n" \
      --json number -q '.[0].number' 2>/dev/null)"
    if [[ -z "$pr" ]]; then
      prrepo=lukasborges/kondor-extensions
      pr="$(gh pr list --repo "$prrepo" --state open --search "lukasborges/kondor#$n" \
        --json number -q '.[0].number' 2>/dev/null)"
    fi
    [[ -n "$pr" ]] || return 1
    gh pr view "$pr" --repo "$prrepo" --json statusCheckRollup \
      -q '.statusCheckRollup[] | select(.name == "build") | .status' 2>/dev/null \
      | grep -qvx COMPLETED
  }

  # True when the Claude run failed before doing any work (authentication, Cloudflare, network).
  # Such a run says nothing about the issue, so it must not count towards a no-progress pause.
  api_unavailable() {
    (( $1 != 0 )) && grep -qE 'Failed to authenticate|API Error' "$2"
  }

  step() {
    local dry="$1" next n st key count_file count run_log rc after
    ensure_control || return 0
    next="$(next_architect_step)"
    read -r n st <<<"$next"
    key="$n"
    if [[ "$n" == "promote" ]]; then
      st="promote"
      n="$(next_promotion)"
      next="promote $n"
      # Nothing to promote is not a failure: clear any no-progress pause so the next filed issue
      # is promoted right away.
      [[ -n "$n" ]] || rm -f "$state/paused-promote" "$state/no-progress-promote"
    fi
    if [[ -z "$n" ]]; then
      # Idle: write the spec of the next roadmap issue ahead of time, so its promotion is quick.
      n="$(next_unspecified)"
      st="prespec"; key="prespec"; next="prespec $n"
    fi
    if [[ -z "$n" ]]; then
      log_idle_once
      return 0
    fi
    rm -f "$state/idle"
    if [[ -e "$state/paused-$key" ]]; then
      log "queue: architect step '$st' on $key is paused (scripts/architect-loop.sh --resume $key)"
      return 0
    fi
    # An approved PR whose build check is still running is waiting for CI, not stuck: skip the
    # run (and the no-progress counter) until the check finishes.
    if [[ "$st" == "in-review" ]] && build_pending "$n"; then
      log "queue: #$n is approved, waiting for the CI build check"
      return 0
    fi
    if [[ "$dry" == 1 ]]; then
      log "dry-run: would run the architect: $st on $key"
      prompt_for "$n" "$st"
      return 0
    fi

    run_log="$state/run-$key-$st-$(date +%Y%m%d-%H%M%S).log"
    log "running architect: $st on #$n (log: $run_log)"
    local args=(-p --permission-mode auto --effort "$effort" --output-format text)
    [[ -n "$model" ]] && args+=(--model "$model")
    (cd "$control" && "$claude" "${args[@]}" "$(prompt_for "$n" "$st")") >"$run_log" 2>&1
    rc=$?
    if api_unavailable "$rc" "$run_log"; then
      log "architect run ($st on $key) could not reach the Claude API (rc=$rc), retrying next tick: $(head -c 200 "$run_log")"
      return 0
    fi
    ensure_control || return 0
    case "$st" in
      promote) after="promote $(next_promotion)" ;;
      prespec) after="prespec $(next_unspecified)" ;;
      *)       after="$(next_architect_step)" ;;
    esac
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
Environment=CMAKE_BUILD_PARALLEL_LEVEL=4
MemoryHigh=12G
MemoryMax=16G
Environment=PATH=$control/scripts/bin:$HOME/.local/bin:$HOME/.opencode/bin:/usr/local/bin:/usr/bin:/bin
Environment=KONDOR_REPO=$repo
Environment=KONDOR_ARCH_CONTROL=$control
Environment=KONDOR_ARCH_STATE=$state
Environment=KONDOR_ARCH_AUTOMERGE=$merge
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
      log "loop started (every ${interval}s, model ${model:-default}, effort $effort, merge=$merge, repo $repo, control $control)"
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
