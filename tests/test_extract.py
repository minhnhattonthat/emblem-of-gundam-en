"""Phase 4 gates: script/ -> ROM roundtrip and coverage.

- Every extracted string re-encodes to the bytes the ROM holds, and rejoining a table's strings gives its pool back.
- extract.check() finds no holes: every string table and arm9 string in the ROM has its script/ entry.
- Every pointer that lands on a text run is accounted for, so no arm9 string was missed.
- Building without edits stays byte-identical (the insert path cannot corrupt what it does not touch)."""
import inspect
import sys
import unittest
from pathlib import Path

import ndspy.lz10
import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import bbq  # noqa: E402
import build  # noqa: E402
import ez  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Extract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        cls.tbl, cls.dat = (cls.rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        cls.tables = extract.bbq_files(cls.tbl, cls.dat)

    def test_every_string_reencodes_to_the_rom_bytes(self):
        checked = 0
        for i, (name, raw, strs) in self.tables.items():
            s7, orig = bbq.strtab(raw)
            for k, text in enumerate(strs):
                self.assertEqual(text.encode("cp932"), orig[k], f"{name} #{k}")
                checked += 1
        self.assertEqual(checked, 66451)

    def test_pool_is_the_index_plus_the_strings(self):
        for i, (name, raw, strs) in self.tables.items():
            s7, _ = bbq.strtab(raw)
            pool = b"".join(s.encode("cp932") + b"\0" for s in strs)
            self.assertEqual(pool + bytes(-len(pool) % 4), raw[s7["data"]:s7["data"] + s7["size"]], name)

    def test_rebuild_is_byte_identical_and_separable(self):
        # rebuild keeps everything before the type-7 index and after the pool, and its index matches the strings
        for i, (name, raw, strs) in self.tables.items():
            got = bbq.rebuild(raw, [s.encode("cp932") for s in strs])
            self.assertEqual(got, raw, name)
            s7, back = bbq.strtab(got)
            self.assertEqual([s.decode("cp932") for s in back], strs, name)

    def test_rebuild_grows_and_shrinks_a_table(self):
        i = 1
        raw, strs = self.tables[i][1], self.tables[i][2]
        grown = bbq.rebuild(raw, [b"This stage name is much longer than the Japanese one"] + [s.encode("cp932") for s in strs[1:]])
        self.assertGreater(len(grown), len(raw))
        self.assertEqual([s.decode("cp932") for s in bbq.strtab(grown)[1]][0], "This stage name is much longer than the Japanese one")
        short = bbq.rebuild(grown, [b"A"] + [s.encode("cp932") for s in strs[1:]])
        self.assertEqual([s.decode("cp932") for s in bbq.strtab(short)[1]], ["A"] + strs[1:])

    def test_size_word_is_the_length_rounded_up_to_16(self):
        # the whole-file loader mallocs this many bytes and the decompressor writes 16 bytes at a time; every one of
        # the archive's 4,146 entries reports align16, and a replaced entry must keep that up (docs/re/archive.md)
        for i, key, off, slen, fl, usz, raw in ez.blocks(self.tbl, self.dat):
            if i not in self.tables or fl != 0x10:
                continue
            real = len(ndspy.lz10.decompress(raw))
            self.assertEqual(usz, real + -real % 16, f"entry {i}")

    def test_insert_pads_a_changed_table_to_16_and_keeps_it_loadable(self):
        ez_new = insert.ez_edits({i: raw for i, (_, raw, _) in self.tables.items()}, {1: ["A"] + self.tables[1][2][1:]})
        self.assertEqual(list(ez_new), [1])
        new = ez_new[1]
        self.assertEqual(len(new) % 16, 0)
        tbl, dat = ez.repack(self.tbl, self.dat, ez_new)
        got = {i: (b, fl, usz) for i, _, _, _, fl, usz, b in ez.blocks(tbl, dat)}
        raw = ndspy.lz10.decompress(got[1][0])
        self.assertEqual(usz := got[1][2], len(raw) + -len(raw) % 16)
        self.assertEqual([s.decode("cp932") for s in bbq.strtab(raw)[1]][0], "A")

    def test_coverage_has_no_holes(self):
        self.assertEqual(extract.check(build.ROM.read_bytes()), [])

    def test_arm9_strings_are_pointed_at_and_reencode(self):
        found = arm9.strings(self.rom.arm9)
        # 351 + 6 glued to binary data with no NUL before them + 2 below the old 0x72170 bound (phase 7)
        self.assertEqual(len(found), 359)
        self.assertIn(0x72150, dict(found))  # ユニットの売却, found by jp_left
        self.assertIn(0x73CBC, dict(found))  # セーブをしますか？ after a pointer table
        for off, text in found:
            end = self.rom.arm9.find(b"\0", off)
            self.assertEqual(text.encode("cp932"), self.rom.arm9[off:end], f"{arm9.BASE + off:#x}")
            self.assertTrue(arm9.pointers(self.rom.arm9, off), f"{arm9.BASE + off:#x} has no pointer")

    def test_no_arm9_text_run_is_left_out(self):
        # every 4-aligned pointer into the region that starts a drawable string of two bytes or more is extracted
        have = {off for off, _ in arm9.strings(self.rom.arm9)}
        for off, end, text in arm9.runners(self.rom.arm9):
            if len(text or "") >= 2 and (end - off) >= 2 and arm9.pointers(self.rom.arm9, off):
                self.assertIn(off, have, f"{arm9.BASE + off:#x} {text!r}")

    def test_arm9_in_place_replace(self):
        off, text = arm9.strings(self.rom.arm9)[0]
        end = self.rom.arm9.find(b"\0", off)
        out = arm9.replace(self.rom.arm9, {off: "A"})
        self.assertEqual(out[off:end + 1], b"A" + bytes(end - off))
        self.assertEqual(out[end + 1:], self.rom.arm9[end + 1:])
        with self.assertRaises(ValueError):
            arm9.replace(self.rom.arm9, {off: text * 4})

    def test_no_script_build_is_byte_identical(self):
        # script/ holds the translation from phase 6 on, so only the --no-script path can be compared to the ROM
        self.assertEqual(build.build(None, None), build.ROM.read_bytes())


if __name__ == "__main__":
    unittest.main()
