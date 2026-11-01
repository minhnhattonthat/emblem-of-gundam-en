"""Phase 7 ROM check: the translated build changes only the text tables, fonts and the arm9 string machinery."""
import sys
import unittest
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import insert  # noqa: E402
import romcheck  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class RomCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = build.ROM.read_bytes()
        ez_new, a9 = build.script()
        cls.built = build.build(ez_new, a9)

    def test_build_changes_only_what_it_may(self):
        self.assertEqual(romcheck.check(self.orig, self.built, insert.tables().keys()), [])

    def test_catches_a_stray_arm9_write(self):
        new = bytearray(ndspy.rom.NintendoDSRom(self.built).arm9)
        new[0x1000] ^= 0xFF
        old = ndspy.rom.NintendoDSRom(self.orig).arm9
        self.assertTrue(any("0x001000" in e for e in romcheck.check_arm9(old, bytes(new))))


if __name__ == "__main__":
    unittest.main()
