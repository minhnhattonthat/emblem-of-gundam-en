import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bbq  # noqa: E402

EZ = ROOT / "work" / "ez"


@unittest.skipUnless((EZ / "0000.bin").is_file(), "run tools/ez.py unpack first")
class BBQStrings(unittest.TestCase):
    def test_pool_is_concatenation(self):
        n = 0
        for f in sorted(EZ.glob("*.bin")):
            d = f.read_bytes()
            if d[:4] != b".BBQ":
                continue
            s7, strs = bbq.strtab(d)
            if s7 is None:
                continue
            pool = b"".join(s + b"\0" for s in strs)
            self.assertEqual(pool, d[s7["data"]:s7["data"] + len(pool)], f.name)
            self.assertLessEqual(len(pool), s7["size"], f.name)
            n += len(strs)
        self.assertEqual(n, 66451)


class TutorialBox(unittest.TestCase):
    def test_x_lowered_to_fit(self):
        # one fn-201 page: line 0 pushed (str32 + native), then Y=12, X=7, call; 30 bytes -> 208 px -> X 6
        L = 0x41c
        w = [0x12400, L, 0, 0x1280e, L, 0xa, 0x10c00, L, 12, 0x10c00, L, 8, 0xc12, L,
             0x10c00, L, 7, 0x10c00, L, 8, 0xc12, L, 0x2002e, L, bbq.TUTOR_FN, 6]
        out, bad = bbq.tutorial_box_words(w, [b"your own forces, starting with"])
        self.assertEqual((out[16], bad), (6, []))
        out, bad = bbq.tutorial_box_words(w, [b"short"])
        self.assertEqual(out, w)  # fits where the Japanese put it
        out, bad = bbq.tutorial_box_words(w, [b"x" * 37])
        self.assertEqual((out[16], len(bad)), (1, 1))
