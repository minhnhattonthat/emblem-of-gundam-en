"""Graphics text (tools/gfx.py): every redrawn stage card keeps its logo pixels, fits its NCGR, keeps its size."""
import sys
import unittest
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import extract  # noqa: E402
import gfx  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Cards(unittest.TestCase):
    def test_cards(self):
        rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        new = gfx.edits(tbl, dat, extract.unpack)
        self.assertEqual(set(new), gfx.ids())
        old = extract.unpack(tbl, dat, gfx.ids())
        for cid, _ in gfx.jobs():
            self.assertEqual(len(new[cid]), len(old[cid]) + -len(old[cid]) % 16)
            a = gfx.index_image(*gfx.parse(old[cid], old[cid + 2])).crop((0, 144, 256, 192))
            b = gfx.index_image(*gfx.parse(new[cid], new[cid + 2])).crop((0, 144, 256, 192))
            self.assertEqual(list(a.getdata()), list(b.getdata()), f"card {cid}: logo rows changed")
            top_a = gfx.index_image(*gfx.parse(old[cid], old[cid + 2])).crop((0, 0, 256, 128))
            top_b = gfx.index_image(*gfx.parse(new[cid], new[cid + 2])).crop((0, 0, 256, 128))
            self.assertNotEqual(list(top_a.getdata()), list(top_b.getdata()), f"card {cid}: caption unchanged")
        for i in gfx.dlg.CREDITS:  # staff roll textures: same size, redrawn, one English line per Japanese line
            self.assertEqual(len(new[i]), len(old[i]))
            self.assertNotEqual(new[i], old[i], f"credits {i} unchanged")
            rows = gfx.dlg.unpack4(gfx.dlg.parse(new[i])[0], gfx.dlg.W)
            want = sum(1 for t in gfx.dlg.CREDITS[i] if t is None or t)
            self.assertEqual(len(gfx.dlg.bands(rows)), want, f"credits {i}: lines merged or lost")


if __name__ == "__main__":
    unittest.main()
