# Turns Claude Code's stream-json output into a readable, live run log:
#   claude -p --output-format stream-json --verbose … | jq -rj --unbuffered -f scripts/claude-progress.jq

def stamp: now | strflocaltime("%H:%M:%S ");

def tool_summary:
  .input.description // .input.command // .input.file_path // .input.pattern // .input.url // "";

def assistant_lines:
  .message.content[]?
  | if .type == "text" then stamp + .text + "\n"
    elif .type == "tool_use" then stamp + "→ " + .name + ": " + (tool_summary | tostring | .[0:200]) + "\n"
    else empty end;

if .type == "assistant" then assistant_lines
elif .type == "result" then "\n=== Report ===\n" + (.result // "") + "\n"
else empty end
