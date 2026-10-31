"""build.py: original ROM -> build/eog_en.nds.

Repacks EZ_TBL/EZ_DAT with replaced entries (none yet: the identity build) and saves with ndspy, then undoes the two
things ndspy.save() changes on its own (docs/re/archive.md): the size word it writes into the zero gap at 0x1000 and
the 0xFF padding back to the cartridge size.

    python -X utf8 tools/build.py [--out PATH]"""
import sys
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import ez  # noqa: E402

ROM = ROOT / "rom" / "Emblem of Gundam (Japan).nds"
OUT = ROOT / "build" / "eog_en.nds"


def build(ez_new=None):
    """Return the built ROM bytes; ez_new = {EZ entry index: unpacked bytes}."""
    orig = ROM.read_bytes()
    rom = ndspy.rom.NintendoDSRom(orig)
    t, d = (rom.filenames.idOf(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    rom.files[t], rom.files[d] = ez.repack(rom.files[t], rom.files[d], ez_new or {})
    out = bytearray(rom.save())
    out[0x1000:0x1004] = orig[0x1000:0x1004]
    if len(out) > len(orig):
        sys.exit(f"ROM grew past the cartridge size: {len(out):#x} > {len(orig):#x}")
    return bytes(out + b"\xff" * (len(orig) - len(out)))


if __name__ == "__main__":
    check_rom.check()
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build())
    print(out)
