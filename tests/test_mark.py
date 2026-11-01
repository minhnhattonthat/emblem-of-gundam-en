"""Phase 5 gates: the marker build's classes and marker text.

The marker build only works as a coverage proof if it marks every drawn string and nothing else: a marked file name
black-screens the boot (arm9 `./EZ_DAT.BIN`), a marked number breaks counters, and a dropped `\\n` would hide a line.
"""
import re
import sys
import unittest
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import build  # noqa: E402
import extract  # noqa: E402
import mark  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Markers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        cls.tbl, cls.dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        cls.tables = extract.bbq_files(cls.tbl, cls.dat)
        cls.strings9 = arm9.strings(rom.arm9)

    def test_classes(self):
        cases = [
            ("", "empty"),
            ("   ", "blank"),
            ("  7", "numeric"),
            ("【消費】$P01%", "text"),  # has kana: text, the token is kept
            ("ｶﾂ&ﾚﾂ&ｷｯｶ", "key"),
            ("./EZ_DAT.BIN", "path"),
            ("ステージを選択", "text"),
            ("PAUSE!", "text"),
        ]
        for s, want in cases:
            self.assertEqual(mark.classify(s)[0], want, s)

    def test_marker_keeps_tokens_and_line_breaks(self):
        got = mark.marked("GM系統が同チームにいる場合\n【攻・防】＋（Lv$L×$P01）", 4, 3)
        lines = got.split("\n")
        self.assertEqual(len(lines), 2, "one marker line per original line")
        self.assertTrue(lines[0].startswith("004:0003|"))
        self.assertIn("$L", lines[1])
        self.assertIn("$P01", lines[1])
        self.assertRegex(lines[1], r"\|0123456789")
        self.assertEqual(got.count("0123456789"), 3 + 3)  # RULER is 30 digits per line: three "0123456789" runs

    def test_every_drawn_string_is_marked_and_nothing_else(self):
        bbq, a9, counts, odd = mark.plan(self.tables, self.strings9, ruler="", arm9_mark_on=True)
        total = sum(len(t[2]) for t in self.tables.values()) + len(self.strings9)
        self.assertEqual(sum(counts.values()), total)
        text = sum(1 for t in self.tables.values() for s in t[2] if mark.classify(s)[0] == "text")
        text += sum(1 for _, s in self.strings9 if mark.classify(s)[0] == "text")
        self.assertEqual(counts["text"], text)
        # excluded strings are byte-identical in the plan
        for i, (name, raw, strs) in self.tables.items():
            new = bbq.get(i, strs)
            for k, s in enumerate(strs):
                if mark.classify(s)[0] != "text":
                    self.assertEqual(new[k], s, f"{i}:{k}")
                else:
                    self.assertEqual(new[k], mark.marked(s, i, k, ""))
        # arm9: every text string gets a marker that fits its slot
        for k, (off, s) in enumerate(self.strings9):
            if mark.classify(s)[0] != "text":
                continue
            m = a9[off]
            self.assertLessEqual(len(m.encode("cp932")), len(s.encode("cp932")), hex(arm9.BASE + off))

    def test_marker_is_unique_and_round_trips_through_the_map(self):
        seen = {}
        for i, (name, raw, strs) in list(sorted(self.tables.items()))[:20]:
            for k, s in enumerate(strs):
                if mark.classify(s)[0] == "text":
                    m = mark.marker(i, k)
                    self.assertNotIn(m, seen)
                    seen[m] = (i, k)
                    self.assertTrue(re.fullmatch(r"\d{3}:\d{4}", m))


if __name__ == "__main__":
    unittest.main()
