"""Phase 7 ROM check: the translated build changes only the text tables, fonts and the arm9 string machinery."""
import sys
import unittest
import struct
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

    def test_rejects_non_string_inside_string_region(self):
        old = ndspy.rom.NintendoDSRom(self.orig).arm9
        new = bytearray(ndspy.rom.NintendoDSRom(self.built).arm9)
        new[0x722a0] ^= 1
        self.assertTrue(any("0722A0" in e for e in romcheck.check_arm9(old, bytes(new))))

    def test_rejects_pointer_into_original_itcm_code(self):
        old = ndspy.rom.NintendoDSRom(self.orig).arm9
        new = bytearray(ndspy.rom.NintendoDSRom(self.built).arm9)
        struct.pack_into("<I", new, 0x72078, 0x01ff8001)
        self.assertTrue(any("pointer to string" in e for e in romcheck.check_arm9(old, bytes(new))))

    def test_rejects_bytecode_change_in_text_table(self):
        a, b = (ndspy.rom.NintendoDSRom(x) for x in (self.orig, self.built))
        old, new = (romcheck.entries(*(r.getFileByName(n) for n in romcheck.EZ_FILES))[89][1] for r in (a, b))
        changed = bytearray(new)
        changed[0x15f8] ^= 1
        self.assertTrue(romcheck.check_bbq(old, bytes(changed), insert.tables()[89]))

    def test_rejects_overlapping_or_stale_write_plan(self):
        overlapping = [(0, b"ab", b"XY", "text"), (1, b"bc", b"YZ", "pointer")]
        self.assertTrue(any("overlaps" in e for e in romcheck.checked_writes(b"abc", b"XYZ", overlapping, "test")))
        stale = [(0, b"def", b"XYZ", "stale preimage")]
        self.assertTrue(any("expects orig" in e for e in romcheck.checked_writes(b"abc", b"XYZ", stale, "test")))


if __name__ == "__main__":
    unittest.main()
