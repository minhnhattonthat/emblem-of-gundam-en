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
import layout  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class RomCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = build.ROM.read_bytes()
        ez_new, a9 = build.script()
        cls.built = build.build(ez_new, a9)

    def test_build_changes_only_what_it_may(self):
        self.assertEqual(romcheck.check(self.orig, self.built, insert.tables().keys()), [])

    def test_rejects_boot_address_checksum_and_gap_corruption(self):
        rom = ndspy.rom.NintendoDSRom(self.built)
        rom.arm9EntryAddress += 4
        self.assertTrue(any("arm9EntryAddress" in e for e in
                            romcheck.check_container(self.orig, self.built, b=rom)))
        for offset in (0x15e, 0x1100):
            with self.subTest(offset=offset):
                changed = bytearray(self.built)
                changed[offset] ^= 1
                errors = romcheck.check_container(self.orig, bytes(changed))
                self.assertTrue(errors, errors)
                if offset == 0x15e:
                    self.assertTrue(any("canonical packing" in e for e in errors), errors)

    def test_native_literal_copies_use_terminated_helper_and_stay_bounded(self):
        old = ndspy.rom.NintendoDSRom(self.orig).arm9
        texts = insert.arm9_texts()
        plans = {off: after for off, _, after, _ in layout.arm9_writes(old, texts)}
        for off, source, _, _, _ in layout.STRING_COPIES:
            call = struct.unpack_from("<I", plans[off], 8)[0]
            displacement = (call & 0xffffff) << 2
            if displacement & 0x2000000:
                displacement -= 0x4000000
            self.assertEqual(0x02000000 + off + 16 + displacement, 0x020102ec)
            self.assertLessEqual(len(texts[source].encode("cp932")) + 1, 256)
            self.assertNotIn(struct.pack("<I", 0x1afffff7), plans[off])  # original loop is gone
        with self.assertRaisesRegex(ValueError, "native destination"):
            layout.arm9_writes(old, {0x72550: "i" * 256})

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
