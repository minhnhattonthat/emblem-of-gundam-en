"""Story-pass chapter files (tools/story.py): pages in display order, borrowed lines in place, speakers attached."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import build  # noqa: E402
import story  # noqa: E402


@unittest.skipUnless(build.ROM.is_file() and (story.EZ / "0093.bin").is_file(), "no ROM / work/ez")
class Chapter(unittest.TestCase):
    def test_pages(self):
        jp, cur = batches.jp_tables(), batches.current()
        text = story.chapter(["0093_ST02STAGE", "0096_ST03STAGE"], jp, cur)
        self.assertIn("   [page in game 605,606,465,607: Right now, Team A / has the Gundam. / The Saberfish", text)
        self.assertIn("   Right now, Team A / has the Gundam. / is its second unit.\n", text)  # every line kept
        self.assertIn(">> 0096:0010 | Kai | 「うわっ", text)  # the name label names the speech after it
        self.assertNotIn("| アムロ\n", text)  # labels are not entries


if __name__ == "__main__":
    unittest.main()
