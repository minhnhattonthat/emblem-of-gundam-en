import hashlib
import struct
import sys
import unittest
from pathlib import Path

import ndspy.lz10
import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import ez  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Identity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = build.ROM.read_bytes()
        rom = ndspy.rom.NintendoDSRom(cls.orig)
        cls.tbl, cls.dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))

    def test_build_without_edits_is_byte_identical(self):
        self.assertEqual(hashlib.sha1(build.build()).hexdigest(), hashlib.sha1(self.orig).hexdigest())

    def test_repack_with_edits_keeps_every_other_entry(self):
        # 1: STAGETABLE.BBQ (LZ10), recompressed and grown; 14 sits before an odd-offset empty entry
        old = {i: (b, fl, usz) for i, _, _, _, fl, usz, b in ez.blocks(self.tbl, self.dat)}
        dec = lambda b, fl, usz: ndspy.lz10.decompress(b) if fl == 0x10 else b[:usz]
        new = {1: dec(*old[1]) + b"x" * 5, 14: dec(*old[14]) + b"yz"}
        tbl, dat = ez.repack(self.tbl, self.dat, new)
        got = {i: (b, fl, usz) for i, _, _, _, fl, usz, b in ez.blocks(tbl, dat)}
        self.assertEqual(len(got), len(old))
        for i, (b, fl, usz) in got.items():
            if i in new:
                self.assertEqual(dec(b, fl, usz), new[i])
                self.assertEqual(usz, len(new[i]) + -len(new[i]) % 16)  # the loader's 16-byte buffer rule
            else:
                self.assertEqual(b, old[i][0], i)
        old_offs = [e[1] for e in ez.entries(self.tbl)]
        for o, n in zip(old_offs, (e[1] for e in ez.entries(tbl))):
            self.assertEqual(o % 4, n % 4)
        self.assertEqual(struct.unpack_from("<I", dat, 0x0C)[0], ez.entries(tbl)[-1][1])


if __name__ == "__main__":
    unittest.main()
