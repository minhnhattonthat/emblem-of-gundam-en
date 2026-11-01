"""build.py: original ROM + script/ -> build/eog_en.nds.

Applies the translation (tools/insert.py): each BBQ string table whose text changed is rebuilt (type 7 is the last
section, so its index and pool just grow or shrink), arm9 strings are replaced in place, then the EZ archive is
repacked and saved with ndspy. Finally it undoes the two things ndspy.save() changes on its own
(docs/re/archive.md): the size word it writes into the zero gap at 0x1000 and the 0xFF padding back to the
cartridge size.

    python -X utf8 tools/build.py [--out PATH] [--no-script]"""
import sys
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import ez  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import gfx  # noqa: E402
import insert  # noqa: E402

ROM = ROOT / "rom" / "Emblem of Gundam (Japan).nds"
OUT = ROOT / "build" / "eog_en.nds"


def build(ez_new=None, arm9_new=None):
    """Return the built ROM bytes; ez_new = {EZ entry index: unpacked bytes}, arm9_new = arm9 bytes or None."""
    orig = ROM.read_bytes()
    rom = ndspy.rom.NintendoDSRom(orig)
    t, d = (rom.filenames.idOf(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    rom.files[t], rom.files[d] = ez.repack(rom.files[t], rom.files[d], ez_new or {})
    if arm9_new is not None:
        rom.arm9 = arm9_new
    out = bytearray(rom.save())
    out[0x1000:0x1004] = orig[0x1000:0x1004]
    if len(out) > len(orig):
        sys.exit(f"ROM grew past the cartridge size: {len(out):#x} > {len(orig):#x}")
    return bytes(out + b"\xff" * (len(orig) - len(out)))


def script(orig=None):
    """(ez_new, arm9_new) from script/; both empty/None when nothing changed. `--no-script` skips this, so the
    identity build never sees the font table either."""
    rom = ndspy.rom.NintendoDSRom(orig or ROM.read_bytes())
    tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    text = extract.bbq_files(tbl, dat)
    ez_new = insert.ez_edits({i: raw for i, (_, raw, _) in text.items()})
    ez_new.update(font.edits(tbl, dat, extract.unpack))  # VWF: per-glyph advances, docs/re/font.md
    ez_new.update(gfx.edits(tbl, dat, extract.unpack))  # graphics text: stage title cards, docs/re/graphics.md
    arm9_new = insert.arm9_edit(rom.arm9)
    return ez_new, (arm9_new if arm9_new != rom.arm9 else None)


if __name__ == "__main__":
    check_rom.check()
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    if "--no-script" in sys.argv:
        data = build()
    else:
        ez_new, arm9_new = script()
        n = len([i for i in ez_new if i not in font.FONT_IDS and i not in gfx.ids()])
        print(f"{n} text tables changed, arm9 {'changed' if arm9_new else 'unchanged'}, "
              f"VWF font table in {len(font.FONT_IDS)} fonts, {len(gfx.ids() & set(ez_new))} graphics entries")
        data = build(ez_new, arm9_new)
        import romcheck
        errors = romcheck.check(ROM.read_bytes(), data, insert.tables().keys(), out.parent / "writes")
        if errors:
            sys.exit("ROM integrity check failed:\n" + "\n".join(errors[:50]))
        print("ROM integrity: exact component writes and relocated string targets verified")
    out.write_bytes(data)
    print(out)
