import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from staging import dictionaries


def convert_with(tool: str | None, hunspell: tuple[str, ...]) -> str:
    errors = io.StringIO()
    with tempfile.TemporaryDirectory() as directory, redirect_stderr(errors), \
            mock.patch.object(dictionaries, "locate", return_value=tool), \
            mock.patch.object(dictionaries, "HUNSPELL_DIRECTORIES", hunspell):
        dictionaries.convert_dictionaries(Path(directory), ("xx_YY",))
    return errors.getvalue()


class DictionaryStepTest(unittest.TestCase):
    def test_skips_a_missing_tool_with_the_warning(self):
        self.assertIn(dictionaries.MISSING_TOOL, convert_with(None, ()))

    def test_skips_a_missing_dictionary_with_the_warning(self):
        message = convert_with("/bin/true", ("/nonexistent",))
        self.assertIn("no xx_YY spell checking", message)

    def test_converts_into_a_bdic_named_with_a_dash(self):
        with tempfile.TemporaryDirectory() as directory:
            hunspell = Path(directory) / "hunspell"
            hunspell.mkdir()
            (hunspell / "xx_YY.dic").write_text("0\n")
            out = Path(directory) / "out"
            with mock.patch.object(dictionaries, "locate", return_value="/bin/cp"), \
                    mock.patch.object(dictionaries, "HUNSPELL_DIRECTORIES", (str(hunspell),)):
                dictionaries.convert_dictionaries(out, ("xx_YY",))
            self.assertTrue((out / "qtwebengine_dictionaries" / "xx-YY.bdic").exists())


if __name__ == "__main__":
    unittest.main()
