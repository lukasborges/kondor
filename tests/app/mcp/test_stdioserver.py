import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
INITIALIZE = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
TOOLS_LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
INVALID_ARGUMENT_STATUS = 2
PARSE_ERROR = -32700
EXPECTED_TOOLS = {
    *["list_pages", "new_tab", "navigate", "go_back", "go_forward", "reload", "snapshot"],
    *["click", "hover", "type_text", "press_key", "scroll", "screenshot", "evaluate"],
}


def run_mcp(
    arguments: list[str], lines: list[str], profile: Path
) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONPATH": str(REPOSITORY / "src"),
        "QT_QPA_PLATFORM": "offscreen",
        "XDG_CONFIG_HOME": str(profile / "config"),
        "XDG_DATA_HOME": str(profile / "data"),
        "XDG_CACHE_HOME": str(profile / "cache"),
    }
    return subprocess.run(
        [sys.executable, "-m", "kondor", "--mcp", *arguments],
        input="".join(line + "\n" for line in lines),
        capture_output=True,
        text=True,
        env=environment,
        timeout=60,
        check=False,
    )


def test_answers_initialize_and_lists_the_tools_on_stdout_only(tmp_path: Path) -> None:
    lines = [json.dumps(INITIALIZE), json.dumps(TOOLS_LIST)]

    completed = run_mcp([], lines, tmp_path)

    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert completed.returncode == 0
    assert responses[0]["result"]["serverInfo"]["name"] == "kondor"
    assert {tool["name"] for tool in responses[1]["result"]["tools"]} == EXPECTED_TOOLS


def test_answers_a_parse_error_for_garbage_and_exits_at_end_of_input(tmp_path: Path) -> None:
    completed = run_mcp([], ["not json"], tmp_path)

    assert json.loads(completed.stdout)["error"]["code"] == PARSE_ERROR
    assert completed.returncode == 0


def test_refuses_other_options(tmp_path: Path) -> None:
    completed = run_mcp(["--private"], [], tmp_path)

    assert completed.returncode == INVALID_ARGUMENT_STATUS
    assert completed.stdout == ""


def test_refuses_an_unknown_profile(tmp_path: Path) -> None:
    completed = run_mcp(["--profile", "nobody"], [], tmp_path)

    assert completed.returncode == 1
    assert completed.stdout == ""
