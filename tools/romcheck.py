"""romcheck.py: what the build may change, checked per component (the pipeline's romdiff step).

The arm9 grows (relocated strings), so ndspy lays the filesystem out again and a flat byte diff of the two ROMs is
noise past the arm9. Instead, against the original:
  - every file but EZ_TBL.BIN / EZ_DAT.BIN, arm7, the overlays, banner and icon are byte-identical;
  - every EZ entry is identical unpacked, except the text tables script/ changed and the two fonts;
  - arm9 (romdiff.check): the main section differs only inside the string region and at the pointer words the
    relocation rewrote, plus the two autoload-params words; the ITCM block is the original + the moved strings;
    the DTCM block is identical; the autoload list differs only in the ITCM size.

    python -X utf8 tools/romcheck.py [BUILT]      # exit 1 on any unexpected change (default: build in memory)"""
import struct
import sys
from pathlib import Path

import ndspy.lz10
import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import build  # noqa: E402
import ez  # noqa: E402
import font  # noqa: E402
import romdiff  # noqa: E402

EZ_FILES = ("EZ_TBL.BIN", "EZ_DAT.BIN")


def entries(tbl, dat):
    out = {}
    for i, key, off, slen, fl, usz, raw in ez.blocks(tbl, dat):
        out[i] = (key, b"" if usz == 0 else ndspy.lz10.decompress(raw) if fl == 0x10 else raw[:usz])
    return out


def check_arm9(old, new):
    errs = []
    p0, l0, e0 = arm9.layout(old)
    p1, l1, e1 = arm9.layout(new)
    src0 = l0 - e0[1][1] - e0[0][1]  # ITCM source start; the main section ends here
    if l1 - e1[1][1] - e1[0][1] != src0:
        errs.append("arm9: the main section changed length")
    allowed = set(range(arm9.LO, arm9.HI))
    moved = {o for o, _ in arm9.strings(old)}
    for o in moved:
        for p in arm9.pointers(old, o):
            if new[p:p + 4] != old[p:p + 4]:
                if not arm9.ITCM_RAM <= struct.unpack_from("<I", new, p)[0] < arm9.ITCM_RAM + arm9.ITCM_LIMIT:
                    errs.append(f"arm9 {arm9.BASE + p:#x}: pointer rewritten outside ITCM")
                allowed.update(range(p, p + 4))
    allowed.update(range(p0, p0 + 8))
    e, _ = romdiff.check(old[:src0], new[:src0], allowed, [])
    errs += [f"arm9 main: {x}" for x in e]
    itcm0, itcm1 = old[src0:src0 + e0[0][1]], new[src0:src0 + e1[0][1]]
    if itcm1[:len(itcm0)] != itcm0:
        errs.append("arm9: the original ITCM code changed")
    if new[src0 + e1[0][1]:l1] != old[src0 + e0[0][1]:l0]:
        errs.append("arm9: the DTCM block changed")
    if e1[1:] != e0[1:] or e1[0][0] != e0[0][0] or e1[0][2] != e0[0][2]:
        errs.append("arm9: autoload entries changed beyond the ITCM size")
    if new[l1 + 12 * len(e1):] != old[l0 + 12 * len(e0):]:
        errs.append("arm9: bytes after the autoload list changed")
    return errs


def check(orig, built, text_ids):
    """Error lines; text_ids = EZ entries the script may change."""
    a, b = ndspy.rom.NintendoDSRom(orig), ndspy.rom.NintendoDSRom(built)
    errs = []
    for name in ("arm7", "iconBanner", "arm9OverlayTable", "arm7OverlayTable"):
        if getattr(a, name) != getattr(b, name):
            errs.append(f"{name} changed")
    if len(a.files) != len(b.files):
        errs.append("file count changed")
    ez_ids = {a.filenames.idOf(n) for n in EZ_FILES}
    for i, (x, y) in enumerate(zip(a.files, b.files)):
        if i not in ez_ids and x != y:
            errs.append(f"file {i} ({a.filenames.filenameOf(i)}) changed")
    ea = entries(*(a.getFileByName(n) for n in EZ_FILES))
    eb = entries(*(b.getFileByName(n) for n in EZ_FILES))
    if ea.keys() != eb.keys():
        errs.append("EZ entry count changed")
    ok = set(text_ids) | set(font.FONT_IDS)
    for i in ea:
        if ea[i] != eb.get(i) and i not in ok:
            errs.append(f"EZ entry {i} changed but is not a text table or font")
        if ea[i][0] != eb[i][0]:
            errs.append(f"EZ entry {i} key changed")
    return errs + check_arm9(a.arm9, b.arm9)


if __name__ == "__main__":
    import insert
    orig = build.ROM.read_bytes()
    if len(sys.argv) > 1:
        built = Path(sys.argv[1]).read_bytes()
    else:
        ez_new, a9 = build.script()
        built = build.build(ez_new, a9)
    errs = check(orig, built, insert.tables().keys())
    for e in errs:
        print(e)
    print(f"{len(errs)} unexpected changes")
    sys.exit(1 if errs else 0)
