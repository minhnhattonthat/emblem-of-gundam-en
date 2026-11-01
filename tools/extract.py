"""extract.py: the game's text -> script/ (JSON, one file per text table), plus the coverage check.

Two sources (docs/re/text.md):
- `.BBQ1.00` archive entries with a type-7 string table -> script/bbq/<ez index>_<name>.json, one string per id.
- arm9's own Shift-JIS strings -> script/arm9.json, keyed by RAM address.

    python -X utf8 tools/extract.py           # write script/ from the ROM
    python -X utf8 tools/extract.py --check   # report holes against the ROM, don't write (exit 1 if any)

Inserting is the reverse: build.py applies these files (see tools/insert.py). The roundtrip test is
tests/test_extract.py."""
import json
import struct
import sys
from pathlib import Path

import ndspy.lz10
import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import bbq  # noqa: E402
import ez  # noqa: E402

ROM = ROOT / "rom" / "Emblem of Gundam (Japan).nds"
SCRIPT = ROOT / "script"
BBQ_DIR = SCRIPT / "bbq"


def names(tbl, dat):
    """{EZ entry index: file name} from the name table at the end of EZ_DAT (an entry's key is its name's offset)."""
    base = struct.unpack_from("<I", dat, 0x0C)[0]
    out = {}
    for i, key, *_ in ez.blocks(tbl, dat):
        end = dat.find(b"\0", base + key)
        out[i] = dat[base + key:end].decode("ascii", "replace")
    return out


def unpack(tbl, dat, want=None):
    """{EZ entry index: unpacked bytes}, decompressed. `want` limits the work to those indices."""
    out = {}
    for i, key, off, slen, fl, usz, raw in ez.blocks(tbl, dat):
        if not usz or (want is not None and i not in want):
            continue
        out[i] = ndspy.lz10.decompress(raw) if fl == 0x10 else raw[:usz]
    return out


def stem(i, name):
    """script file name for an EZ entry: index + the archive name without .BBQ."""
    base = name[:-4] if name.upper().endswith(".BBQ") else name
    base = base.rsplit(".", 1)[0] or "unnamed"
    return f"{i:04d}_{base}"


def bbq_files(tbl, dat):
    """{ez index: (name, raw file bytes, strings)} for every entry that carries a type-7 string table."""
    nm = names(tbl, dat)
    # Text containers are named .BBQ (330 of them), plus DUMMY.TXT and one unnamed entry: 332 entries start with
    # .BBQ1.00 (docs/re/archive.md). Every other entry is graphics, sound or a 3D model, so don't decompress those.
    want = {i for i, n in nm.items() if n.upper().endswith((".BBQ", ".TXT")) or not n}
    data = unpack(tbl, dat, want)
    out = {}
    for i, d in sorted(data.items()):
        if d[:4] != b".BBQ":
            continue
        s7, strs = bbq.strtab(d)
        if s7 is None:
            continue
        out[i] = (nm.get(i, ""), d, [s.decode("cp932") for s in strs])
    return out


def arm9_text(arm9_bytes):
    """[(file offset, text)] of the arm9 strings a pointer reaches."""
    return arm9.strings(arm9_bytes)


def _load(rom_bytes):
    rom = ndspy.rom.NintendoDSRom(rom_bytes)
    tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    return rom, tbl, dat


def write_json(path, obj):
    """Write JSON with LF endings (Windows text mode would turn them into CRLF and churn the diff)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def dump(rom_bytes):
    """Write script/: one JSON per BBQ string table plus script/arm9.json. Returns what was written."""
    rom, tbl, dat = _load(rom_bytes)
    tables = bbq_files(tbl, dat)
    written = []
    seen = set()
    for i, (name, raw, strs) in tables.items():
        path = BBQ_DIR / f"{stem(i, name)}.json"
        seen.add(path.name)
        write_json(path, {"ez_index": i, "name": name, "strings": strs})
        written.append((path, len(strs)))
    for stale in BBQ_DIR.glob("*.json"):
        if stale.name not in seen:
            stale.unlink()
    strings = [{"at": f"{arm9.BASE + off:#x}", "text": t} for off, t in arm9_text(rom.arm9)]
    path = SCRIPT / "arm9.json"
    write_json(path, {
        "note": "arm9 strings, keyed by RAM address (file offset = at - 0x02000000). See docs/re/text.md.",
        "strings": strings,
    })
    written.append((path, len(strings)))
    return written


def check(rom_bytes):
    """Return a list of holes: (where, problem). Empty means every string in the ROM is in script/, back to the
    same bytes, and every byte of a string table is accounted for."""
    out = []
    rom, tbl, dat = _load(rom_bytes)
    tables = bbq_files(tbl, dat)
    want = {f"{stem(i, n)}.json" for i, (n, _, _) in tables.items()}
    have = {p.name for p in BBQ_DIR.glob("*.json")}
    for name in sorted(want - have):
        out.append((name, "missing from script/bbq"))
    for name in sorted(have - want):
        out.append((name, "in script/bbq but not in the ROM"))
    total = 0
    for i, (ezname, raw, strs) in tables.items():
        name = f"{stem(i, ezname)}.json"
        s7, _ = bbq.strtab(raw)
        total += len(strs)
        concat = b"".join(s.encode("cp932") + b"\0" for s in strs)
        pool = raw[s7["data"]:s7["data"] + s7["size"]]
        if pool[:len(concat)] != concat or not 0 <= len(pool) - len(concat) < 4:
            out.append((name, f"pool {len(pool)} bytes vs {len(concat)} of strings + padding"))
        path = BBQ_DIR / name
        if not path.is_file():
            continue
        got = json.loads(path.read_text(encoding="utf-8"))
        if got.get("ez_index") != i:
            out.append((name, f"ez_index {got.get('ez_index')}"))
        # text may differ from the ROM once translated (phase 6); the string count may not
        if len(got["strings"]) != len(strs):
            out.append((name, f"{len(got['strings'])} strings, ROM has {len(strs)}"))
    # arm9
    path = SCRIPT / "arm9.json"
    want9 = [(f"{arm9.BASE + off:#x}", t) for off, t in arm9_text(rom.arm9)]
    total += len(want9)
    if not path.is_file():
        out.append(("arm9.json", "missing"))
    else:
        got9 = [(s["at"], s["text"]) for s in json.loads(path.read_text(encoding="utf-8"))["strings"]]
        have9, wantd = dict(got9), dict(want9)
        for at in sorted(set(wantd) ^ set(have9)):
            out.append((f"arm9 {at}", "only in script" if at in have9 else f"missing: ROM {wantd[at]!r}"))
    print(f"{len(tables)} tables, {total} strings", flush=True)
    return out


if __name__ == "__main__":
    data = ROM.read_bytes()
    if "--check" in sys.argv:
        holes = check(data)
        for where, problem in holes[:40]:
            print(f"HOLE {where}: {problem}")
        print(f"{len(holes)} holes")
        sys.exit(1 if holes else 0)
    if sys.argv[1:] != ["--overwrite"]:  # a bare run (or `--help`) once replaced the whole translation with JP
        sys.exit("extract.py overwrites script/ with the ROM's Japanese: pass --overwrite (or --check)")
    for path, n in dump(data):
        print(f"{path.relative_to(ROOT)}: {n} strings")
