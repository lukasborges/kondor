#!/usr/bin/env bash
# Put an issue on the "Kondor Roadmap" project board and set its Status.
#
#   scripts/board.sh <issue-number> [Todo|"In Progress"|Blocked|Done]   # default: Todo
#
# Adding is idempotent (an issue already on the board keeps its item). A closed issue always goes
# to Done, whatever status is asked, so a late call never moves a finished card back.
set -euo pipefail

OWNER="lukasborges"
REPO="lukasborges/kondor-browser"
PROJECT=1

n="${1:?usage: scripts/board.sh <issue-number> [Todo|\"In Progress\"|Blocked|Done]}"
status="${2:-Todo}"
[[ "$(gh issue view "$n" --repo "$REPO" --json state --jq .state)" == CLOSED ]] && status=Done

project_id="$(gh project view "$PROJECT" --owner "$OWNER" --format json --jq .id)"
read -r field_id option_id < <(gh project field-list "$PROJECT" --owner "$OWNER" --format json \
  --jq ".fields[] | select(.name==\"Status\") | \"\(.id) \(.options[] | select(.name==\"$status\") | .id)\"")
[[ -n "${option_id:-}" ]] || { echo "unknown status: $status" >&2; exit 1; }

item_id="$(gh project item-add "$PROJECT" --owner "$OWNER" \
  --url "https://github.com/$REPO/issues/$n" --format json --jq .id)"
gh project item-edit --project-id "$project_id" --id "$item_id" \
  --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null
echo "#$n -> $status"
