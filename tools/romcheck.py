"""romcheck.py: what the build may change, checked per component (the pipeline's romdiff step).

The arm9 grows (relocated strings), so ndspy lays the filesystem out again and a flat byte diff of the two ROMs is
noise past the arm9. Instead, against the original:
  - every file but EZ_TBL.BIN / EZ_DAT.BIN, arm7, the overlays, banner and icon are byte-identical;
  - every EZ entry is identical unpacked, except exact planned text, VM type/layout, font and graphics writes;
  - ARM9 string slots, every relocated pointer and its exact target content, and the autoload splice match an
    independent plan against the clean original. There is no blanket permission for the surrounding string region.
  - romdiff checks expected preimages, final bytes and overlaps. The CLI/build records component plans in build/writes.

    python -X utf8 tools/romcheck.py [BUILT]      # exit 1 on any unexpected change (default: build in memory)"""
import struct
import sys
from pathlib import Path

import ndspy.lz10
import ndspy.rom
import ndspy.fnt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import bbq  # noqa: E402
import build  # noqa: E402
import ez  # noqa: E402
import font  # noqa: E402
import gfx  # noqa: E402
import insert  # noqa: E402
import layout  # noqa: E402
import extract  # noqa: E402
import romdiff  # noqa: E402

EZ_FILES = ("EZ_TBL.BIN", "EZ_DAT.BIN")


def entries(tbl, dat):
    out = {}
    for i, key, off, slen, fl, usz, raw in ez.blocks(tbl, dat):
        out[i] = (key, b"" if usz == 0 else ndspy.lz10.decompress(raw) if fl == 0x10 else raw[:usz])
    return out


def checked_writes(old, new, writes, label, logs=None):
    """No blanket ranges. Each planned write names its clean-original preimage and final bytes."""
    errors, _ = romdiff.check(old, new, set(), writes)
    if logs is not None:
        logs.extend(writes)
    return [f"{label}: {e}" for e in errors]


def write(old, off, data, name):
    return off, old[off:off + len(data)].ljust(len(data), b"\xff"), data, name


def check_arm9(old, new, texts=None, logs=None):
    """Independently plan exact string slots, references, and autoload metadata from the clean ARM9."""
    texts = insert.arm9_texts() if texts is None else texts
    originals = dict(arm9.strings(old))
    params, lst, ents = arm9.layout(old)
    itcm_end = lst - ents[1][1]
    writes, pool = [], bytearray()
    edits = {off: text for off, text in texts.items() if originals.get(off) != text}
    writes.extend(layout.arm9_writes(old, edits))
    for off, text in texts.items():
        if off not in originals:
            return [f"arm9: unknown string start {off:#x}"]
        if originals[off] == text:
            continue
        size = len(originals[off].encode("cp932")) + 1
        data = text.encode("cp932") + b"\0"
        if len(data) <= size:
            writes.append(write(old, off, data.ljust(size, b"\0"), f"string {off:#x}"))
        else:
            if off in arm9.BUFFERS:
                return [f"arm9: writable buffer {off:#x} cannot move"]
            target = arm9.ITCM_RAM + ents[0][1] + len(pool)
            pool.extend(data)
            writes.append(write(old, off, bytes(size), f"vacated string {off:#x}"))
            for slot in arm9.pointers(old, off):
                writes.append(write(old, slot, struct.pack("<I", target), f"pointer to string {off:#x}"))
    pool.extend(bytes(-len(pool) % 4))
    if ents[0][1] + len(pool) > arm9.ITCM_LIMIT:
        return ["arm9: relocated text exceeds ITCM"]
    if pool:
        writes.append(write(old, params, struct.pack("<2I", arm9.BASE + lst + len(pool),
                            arm9.BASE + lst + len(pool) + len(ents) * 12), "autoload pointers"))
        # Variable-sized splice: validate the complete moved DTCM/list suffix, including its original code.
        tail = bytearray(pool + old[itcm_end:])
        struct.pack_into("<I", tail, len(pool) + lst - itcm_end + 4, ents[0][1] + len(pool))
        writes.append(write(old, itcm_end, bytes(tail), "text pool + unchanged DTCM + autoload size"))
    errors = checked_writes(old, new, writes, "arm9", logs)
    if len(new) != len(old) + len(pool):
        errors.append("arm9: unexpected length")
    return errors


def check_bbq(old, new, texts, logs=None, index=0):
    """Only type-7 index/pool, the stage-name field, and approved VM type bits may change."""
    encoded = [s.encode("cp932") for s in texts]
    sec, original_text = bbq.strtab(old)
    expected = insert.ez_edits({index: old}, {index: texts}).get(index, old)
    prefix = expected[:sec["index"]]
    writes = []
    for off, before, after, name in (layout.OPERANDS.get(index, []) if encoded != original_text else []):
        writes.append((off, struct.pack("<I", before), struct.pack("<I", after), name))
    # Descriptor size is the only header word that changes when replacing the final section.
    off = sec["at"] + 16
    if prefix[off:off + 4] != old[off:off + 4]:
        writes.append(write(old, off, prefix[off:off + 4], "string pool size"))
    vm, words = bbq.code_words(old)
    if vm:
        for idx, op, args in bbq.instructions(words):
            off = vm["data"] + idx * 4
            changed = struct.unpack_from("<I", prefix, off)[0]
            if op != changed:
                if (op ^ changed) & ~0x7C00 or op & 0x3FF or not 8 <= ((op >> 10) & 31) <= 12:
                    return ["unapproved VM instruction change in insertion plan"]
                writes.append(write(old, off, struct.pack("<I", changed), "VM string operand type"))
    stage = next((s for s in bbq.sections(old) if s["type"] == 5), None)
    if stage:
        lo, hi = struct.unpack_from("<2I", old, stage["index"]) if stage["count"] > 1 else (0, stage["size"])
        if hi - lo == 84:
            off = stage["data"] + lo
            name = old[off:off + bbq.NAME_FIELD].split(b"\0")[0]
            data = encoded[original_text.index(name)].ljust(bbq.NAME_FIELD, b"\0")
            if data != old[off:off + bbq.NAME_FIELD]:
                writes.append(write(old, off, data, "stage-name record"))
    # A shorter component is padded with FF only for the byte checker; its logical length is checked separately.
    extent = max(len(old), len(expected))
    writes.append(write(old, sec["index"], expected[sec["index"]:].ljust(extent - sec["index"], b"\xff"),
                        "type-7 index/pool + original tail/alignment"))
    errors = checked_writes(old, new.ljust(extent, b"\xff"), writes, "BBQ", logs)
    if len(new) != len(expected):
        errors.append("BBQ text component has unexpected length")
    return errors


def asset_writes(old, expected):
    """Exact changed spans in the approved font/graphics rendering, never spans from the candidate ROM."""
    extent = max(len(old), len(expected))
    a, b = old.ljust(extent, b"\xff"), expected.ljust(extent, b"\xff")
    writes, i = [], 0
    while i < extent:
        if a[i] == b[i]:
            i += 1
            continue
        start = i
        while i < extent and a[i] != b[i]:
            i += 1
        writes.append(write(old, start, b[start:i], "approved font/graphics rendering"))
    return writes


def check_container(orig, built, a=None, b=None):
    """Preserve metadata and reject corruption in header checksums, layout and unparsed padding."""
    a = ndspy.rom.NintendoDSRom(orig) if a is None else a
    b = ndspy.rom.NintendoDSRom(built) if b is None else b
    errors = []
    for name, value in vars(a).items():
        if name not in {"arm9", "files", "filenames"} and value != getattr(b, name):
            errors.append(f"ROM {name} changed")
    if ndspy.fnt.save(a.filenames) != ndspy.fnt.save(b.filenames):
        errors.append("ROM filenames changed")
    canonical = bytearray(b.save())
    canonical[0x1000:0x1004] = orig[0x1000:0x1004]  # same two normalization steps as build.py
    canonical.extend(b"\xff" * max(0, len(orig) - len(canonical)))
    if len(built) != len(orig):
        errors.append("ROM cartridge size changed")
    if canonical != built:
        errors.append("ROM header/checksums, file layout or padding differs from canonical packing")
    return errors


def check(orig, built, text_ids, writes_dir=None):
    """Error lines; text_ids = EZ entries the script may change."""
    a, b = ndspy.rom.NintendoDSRom(orig), ndspy.rom.NintendoDSRom(built)
    errs, logs = check_container(orig, built, a, b), {"arm9": []}
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
    scripts = insert.tables()
    tbl, dat = (a.getFileByName(n) for n in EZ_FILES)
    assets = font.edits(tbl, dat, extract.unpack)
    assets.update(gfx.edits(tbl, dat, extract.unpack))
    for i in ea:
        if i not in eb:
            continue
        if ea[i][0] != eb[i][0]:
            errs.append(f"EZ entry {i} key changed")
        old, new = ea[i][1], eb[i][1]
        if i in text_ids:
            log = logs.setdefault(f"ez_{i:04d}", [])
            errs.extend(f"EZ entry {i}: {e}" for e in check_bbq(old, new, scripts[i], log, index=i))
        elif i in assets:
            expected = assets[i]
            log = logs.setdefault(f"ez_{i:04d}", [])
            extent = max(len(old), len(expected))
            errs.extend(checked_writes(old, new.ljust(extent, b"\xff"), asset_writes(old, expected), f"EZ entry {i}", log))
            if len(new) != len(expected):
                errs.append(f"EZ entry {i}: font/graphics length differs from approved rendering")
        elif new != old:
            errs.append(f"EZ entry {i}: unexpected change")
    errs.extend(check_arm9(a.arm9, b.arm9, logs=logs["arm9"]))
    if writes_dir is not None:
        dest = Path(writes_dir)
        dest.mkdir(parents=True, exist_ok=True)
        for component, writes in logs.items():
            (dest / f"{component}.txt").write_text(
                "# Component offsets; clean-original preimage; FF pads resized components for romdiff.\n" +
                "".join(f"{off:X} {before.hex()} {after.hex()} {name}\n" for off, before, after, name in writes),
                encoding="utf-8")
    return errs


if __name__ == "__main__":
    import insert
    orig = build.ROM.read_bytes()
    if len(sys.argv) > 1:
        built = Path(sys.argv[1]).read_bytes()
    else:
        ez_new, a9 = build.script()
        built = build.build(ez_new, a9)
    errs = check(orig, built, insert.tables().keys(), ROOT / "build" / "writes")
    for e in errs:
        print(e)
    print(f"{len(errs)} unexpected changes")
    sys.exit(1 if errs else 0)
