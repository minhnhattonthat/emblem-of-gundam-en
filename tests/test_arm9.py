"""Phase 5 gates: growing arm9 strings -- in place when they fit, else into the ITCM autoload tail (arm9.relocate).

The relocation is only valid if the autoload layout still parses, the ITCM section grows by exactly the data, the
autoload list stays 4-aligned (the game loads it with LDR), the old slot is zeroed and every pointer to a moved
string is rewritten.
"""
import struct
import sys
import unittest
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import build  # noqa: E402
import insert  # noqa: E402


def refs(d, ram):
    """File offsets of the 4-aligned words holding `ram`."""
    want = struct.pack("<I", ram)
    out, at = [], d.find(want)
    while at >= 0:
        if at % 4 == 0:
            out.append(at)
        at = d.find(want, at + 1)
    return out


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Grow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arm9 = ndspy.rom.NintendoDSRom(build.ROM.read_bytes()).arm9
        cls.strings = arm9.strings(cls.arm9)
        cls.params, cls.list_off, cls.ents = arm9.layout(cls.arm9)

    def test_layout(self):
        params, lst, ents = self.params, self.list_off, self.ents
        self.assertEqual(lst % 4, 0)
        self.assertEqual(ents[0][0], arm9.ITCM_RAM)
        self.assertLessEqual(ents[0][1], arm9.ITCM_LIMIT)
        self.assertEqual(struct.unpack_from("<I", self.arm9, params)[0], arm9.BASE + lst)
        self.assertEqual(struct.unpack_from("<I", self.arm9, params + 4)[0], arm9.BASE + lst + 12 * len(ents))
        self.assertGreater(arm9.itcm_room(self.arm9), 20000)

    def test_relocate_one_string(self):
        off = 0x76D98  # ステージを選択, the scenario-chart footer
        self.assertIn(off, {o for o, _ in self.strings})
        text = "STAGE SELECT FROM THE ITCM TAIL"
        new = arm9.relocate(self.arm9, {off: text})
        params, lst, ents = arm9.layout(new)
        self.assertIsNotNone(params)
        self.assertEqual(lst % 4, 0)
        grew = len(new) - len(self.arm9)
        self.assertEqual(ents[0][1] - self.ents[0][1], grew)
        self.assertEqual(arm9.itcm_room(new), arm9.itcm_room(self.arm9) - grew)
        # the string is the last thing in the new ITCM data
        tail = lst - ents[1][1] - len(text.encode("cp932")) - 1
        self.assertEqual(new[tail:tail + len(text) + 1], text.encode("cp932") + b"\0")
        # the old slot is zeroed and no literal still holds it
        self.assertEqual(new[off:off + 15], bytes(15))
        self.assertEqual(refs(new, arm9.BASE + off), [])
        self.assertTrue(refs(new, arm9.ITCM_RAM + self.ents[0][1]), "no pointer to the moved string")
        # everything before the insertion point differs only at the params, the old slot and literals that held it
        allowed = set(range(self.params, self.params + 8)) | set(range(off, off + 15))
        for p in refs(self.arm9, arm9.BASE + off):
            allowed |= {p, p + 1, p + 2, p + 3}
        changed = {i for i in range(0x782A0) if new[i] != self.arm9[i]}
        self.assertLessEqual(changed, allowed)
        self.assertGreater(len(changed), 0)

    def test_relocate_overflow_is_refused(self):
        with self.assertRaises(ValueError):
            arm9.relocate(self.arm9, {self.strings[0][0]: "A" * (arm9.itcm_room(self.arm9) + 1)})

    def test_buffer_move_is_refused(self):
        with self.assertRaises(ValueError):
            arm9.relocate(self.arm9, {0x746FC: "Not set"})

    def test_every_write_destination_is_a_buffer(self):
        """A string whose address the code passes as r0 to strcpy/strncpy/memset is a RAM buffer: it must be in
        BUFFERS so relocate refuses it (moving 未設定 at 0x020746FC blanked the stage-info panel)."""
        writers = {0x020102EC, 0x020103B4, 0x0200DF60}  # strcpy, strncpy (zero-fills), memset
        starts = {arm9.BASE + off for off, _ in self.strings}
        d, found = self.arm9, set()
        for off in range(0, arm9.LO, 4):
            w = struct.unpack_from("<I", d, off)[0]
            if w & 0x0F7F0000 != 0x051F0000 or w >> 28 == 0xF or (w >> 12) & 0xF != 0:
                continue  # want LDR r0, [pc, #imm]
            lit = off + 8 + (w & 0xFFF if w & 0x00800000 else -(w & 0xFFF))
            val = struct.unpack_from("<I", d, lit)[0]
            if val not in starts:
                continue
            for k in range(1, 5):  # the call follows within a few instructions
                nxt = struct.unpack_from("<I", d, off + 4 * k)[0]
                if (nxt >> 24) & 0xF == 0xB:
                    tgt = arm9.BASE + off + 4 * k + 8 + (((nxt & 0xFFFFFF) ^ 0x800000) - 0x800000) * 4
                    if tgt in writers:
                        found.add(val - arm9.BASE)
                    break
        self.assertTrue(found)
        self.assertLessEqual(found, arm9.BUFFERS)

    def test_all_strings_moved_at_once_still_fits(self):
        moves = {off: f"a{k}" for k, (off, _) in enumerate(self.strings) if off not in arm9.BUFFERS}
        new = arm9.relocate(self.arm9, moves)
        params, lst, ents = arm9.layout(new)
        self.assertLessEqual(ents[0][1], arm9.ITCM_LIMIT)
        self.assertEqual(len(new), len(self.arm9) + ents[0][1] - self.ents[0][1])
        tail = lst - ents[1][1]
        self.assertIn(b"a350\0", new[:tail])  # the last marker landed in the ITCM tail
        self.assertEqual(refs(new, arm9.BASE + self.strings[0][0]), [])
        self.assertTrue(refs(new, arm9.ITCM_RAM + self.ents[0][1]))

    def test_insert_edit_picks_in_place_or_move(self):
        off_small = self.strings[0][0]
        out = insert.arm9_edit(self.arm9, {off_small: "A", 0x76D98: "STAGE SELECT FROM THE ITCM TAIL"})
        self.assertEqual(out[off_small:off_small + 2], b"A\0")
        self.assertIsNotNone(arm9.layout(out))
        self.assertGreater(len(out), len(self.arm9))
        same = {off: t for off, t in self.strings}
        self.assertEqual(insert.arm9_edit(self.arm9, same), self.arm9)


if __name__ == "__main__":
    unittest.main()
