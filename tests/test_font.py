"""Phase 5 gates: the VWF advance table and the pixel-width model the marker build and the later lint use.

The model was measured in-game (docs/re/font.md): the renderer moves the pen by the glyph's CWDH advance plus 1 px.
"""
import struct
import sys
import unittest
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import nftr  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Vwf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        cls.tbl, cls.dat = (cls.rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        cls.orig = extract.unpack(cls.tbl, cls.dat, set(font.FONT_IDS))
        cls.new = {i: font.proportional(d) for i, d in cls.orig.items()}

    def test_length_and_kana_untouched(self):
        for i, d in self.orig.items():
            self.assertEqual(len(self.new[i]), len(d), f"font {i}")
            a, b = nftr.parse(d), nftr.parse(self.new[i])
            self.assertEqual(a["cell_w"], b["cell_w"])
            self.assertEqual(a["glyph_off"] + 1, b["glyph_off"] + 1)  # no chunk moved
            for code in range(0x8140, 0x8300):  # a slice of SJIS space: advances must not change
                if code in a["cmap"] and a["cmap"][code] in a["widths"]:
                    self.assertEqual(a["widths"][a["cmap"][code]], b["widths"][b["cmap"][code]], f"font {i} {code:#x}")

    def test_advance_is_the_ink_width(self):
        for i, d in self.orig.items():
            f, g = nftr.parse(d), nftr.parse(self.new[i])
            table = font.advances(self.new[i])
            for c in font.PRINTABLE:
                if c not in f["cmap"]:
                    continue
                ink = font.ink_width(f, d, f["cmap"][c])
                want = font.SPACE_ADVANCE if c == 0x20 else max(1, ink)
                self.assertEqual(table[c][2], want, f"font {i} {chr(c)!r}")

    def test_width_model_matches_the_measured_pitch(self):
        # in-game (font 0336, the one the dialogue/menu screens draw): default ASCII advance 6 -> 7 px pitch; a test
        # that set 2 -> 3 px and 10 -> 11 px (font.py header, docs/re/font.md). 0337 is assumed the same renderer.
        table = font.advances(self.orig[336])
        self.assertEqual(table[ord("i")][2], 6)
        self.assertEqual(font.width("ii", table), 2 * 7)
        adv = dict(table)
        adv[ord("i")] = (3, 1, 2)
        self.assertEqual(font.width("ii", adv), 2 * 3)
        adv[ord("i")] = (1, 5, 10)
        self.assertEqual(font.width("ii", adv), 2 * 11)
        for i in font.FONT_IDS:
            t = font.advances(self.orig[i])
            self.assertEqual(font.width("ii", t), 2 * (t[ord("i")][2] + 1), f"font {i}")

    def test_build_installs_the_vwf_table(self):
        ez_new, _ = build.script()
        rom = ndspy.rom.NintendoDSRom(build.build(ez_new, None))
        tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        import extract

        got = extract.unpack(tbl, dat, set(font.FONT_IDS))
        for i in font.FONT_IDS:
            self.assertEqual(font.advances(got[i]), font.advances(font.proportional(self.orig[i])), f"font {i}")


if __name__ == "__main__":
    unittest.main()
