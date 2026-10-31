"""fsls.py: list the NitroFS of the original ROM (path, size, magic) and optionally unpack it to work/fs/.

    python -X utf8 tools/fsls.py [--unpack]"""
import sys
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Emblem of Gundam (Japan).nds"


def files(rom):
    for fid, data in enumerate(rom.files):
        name = rom.filenames.filenameOf(fid)
        if name is not None:
            yield fid, name, data


if __name__ == "__main__":
    rom = ndspy.rom.NintendoDSRom.fromFile(ROM)
    unpack = "--unpack" in sys.argv
    for fid, name, data in files(rom):
        print(f"{fid:5d} {len(data):9d} {data[:4].hex()} {data[:4]!r:12} {name}")
        if unpack:
            p = ROOT / "work" / "fs" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    print(f"arm9 {len(rom.arm9)} arm7 {len(rom.arm7)} overlays9 {len(rom.arm9OverlayTable)}")
    if unpack:
        (ROOT / "work" / "fs" / "arm9.bin").write_bytes(rom.arm9)
        for i, ov in rom.loadArm9Overlays().items():
            (ROOT / "work" / "fs" / f"overlay9_{i:04d}.bin").write_bytes(ov.data)
