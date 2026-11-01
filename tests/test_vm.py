"""Script VM string pushes (docs/re/bbq.md §VM strings): the bytecode decodes cleanly in every table, Japanese text
needs no widening, and English that outgrows a push gets the smallest type that holds it, capped by the native call."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bbq  # noqa: E402
import build  # noqa: E402
import extract  # noqa: E402
import insert  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class VMStrings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, tbl, dat = extract._load(build.ROM.read_bytes())
        cls.tables = extract.bbq_files(tbl, dat)

    def test_decodes_and_japanese_fits(self):
        pushes = 0
        for i, (name, raw, strs) in self.tables.items():
            _, w = bbq.code_words(raw)
            for at, op, args in bbq.instructions(w):
                self.assertLessEqual(op & 0x3FF, 0x32, f"{name} word {at}: not an opcode")
                self.assertLessEqual((op >> 10) & 0x1F, 12, f"{name} word {at}: bad type")
                pushes += op & 0x3FF == 0 and (op >> 10) & 0x1F >= 8
            self.assertEqual(bbq.widen(raw, [s.encode("cp932") for s in strs]), (raw, []), name)
        self.assertGreater(pushes, 100000)

    def test_widen_grows_to_fit_and_stops_at_the_native(self):
        i = 191  # ST30STAGE: string 356 (敵全滅, victory) is pushed as str16 and handed to a str64 native
        name, raw, strs = self.tables[i]
        enc = [s.encode("cp932") for s in strs]
        _, w = bbq.code_words(raw)
        at = next(a for a, op, args in bbq.instructions(w)
                  if op & 0x3FF == 0 and (op >> 10) & 0x1F >= 8 and list(args[:1]) == [356])
        self.assertEqual((w[at] >> 10) & 0x1F, 8)
        for text, want in ((b"x" * 15, 8), (b"x" * 16, 9), (b"x" * 40, 10)):
            enc[356] = text
            new, bad = bbq.widen(raw, enc)
            self.assertEqual(bad, [])
            self.assertEqual((bbq.code_words(new)[1][at] >> 10) & 0x1F, want, len(text))
        enc[356] = b"x" * 64
        self.assertEqual(bbq.widen(raw, enc)[1], [(356, 65, 63)])

    def test_script_fits(self):
        insert.ez_edits({i: raw for i, (_, raw, _) in self.tables.items()})  # raises on a string too long


if __name__ == "__main__":
    unittest.main()
