"""Message pages that borrow a line from another page (tools/pages.py): the borrowed line keeps its speech shape."""
import sys
import unittest
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import extract  # noqa: E402
import pages  # noqa: E402


class Shape(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(pages.shape("　一体何をやっておるのか！」", '"What on earth are they doing!"'),
                         ["opening quote", "continuation indent"])
        self.assertEqual(pages.shape("　一体何をやっておるのか！」", ' What on earth are they doing!"'), [])
        self.assertEqual(pages.shape("「３」だ。", 'is "3."'), [])  # inline quote
        self.assertEqual(pages.shape("　　　健闘を祈る。", "Good luck."), [])  # centred, not speech

    @unittest.skipUnless(build.ROM.is_file(), "no ROM")
    def test_script(self):
        rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        want = {int(f.name[:4]) for f in pages.files()}
        bad = pages.shape_problems(extract.unpack(tbl, dat, want))
        self.assertEqual(bad, [], "\n".join("\t".join(map(str, r)) for r in bad[:20]))


if __name__ == "__main__":
    unittest.main()
