import os
import subprocess
import sys
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / "scripts" / "bench-adblock.py"
IMPORT_ONLY = (
    "import runpy, sys;"
    "runpy.run_path(sys.argv[1], run_name='bench')"
)


class BenchAdblockImportTest(unittest.TestCase):
    def test_script_imports_kondor_without_pythonpath(self) -> None:
        environment = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        result = subprocess.run(
            [sys.executable, "-c", IMPORT_ONLY, str(SCRIPT)],
            cwd=REPOSITORY,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
