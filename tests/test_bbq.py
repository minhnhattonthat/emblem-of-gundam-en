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
