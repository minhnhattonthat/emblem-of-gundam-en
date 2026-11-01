"""The phase 7 text lint (tools/lint.py) over script/: no errors. Warnings (boxes not measured yet) are allowed."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import build  # noqa: E402
import lint  # noqa: E402


@unittest.skipUnless(build.ROM.is_file() or batches.JP_CACHE.is_file(), "no ROM")
class Lint(unittest.TestCase):
    def test_script_is_clean(self):
        errs, _ = lint.lint()
        self.assertEqual(errs, [], "\n" + "\n".join(errs[:30]))

    def test_catches(self):
        jp = {"0086_ST00STAGE": ["「見える」", "敵全滅", "　次へ"], "arm9": []}
        cur = {"0086_ST00STAGE": ["\"I see %d\"", "W" * 40, "見え"], "arm9": {}}
        errs, _ = lint.lint(jp, cur, set())
        text = "\n".join(errs)
        self.assertIn("codes", text)
        self.assertIn("> story_dialogue", text)
        self.assertIn("Japanese left", text)


if __name__ == "__main__":
    unittest.main()
