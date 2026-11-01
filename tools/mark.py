"""mark.py: the phase 5 marker build -- every text string replaced by its id plus a ruler, to check in-game that the
extraction covers everything the game draws, and to measure each text box's width (the width gate).

Marker text is `TTT:IIII|` + a ruler of `0123456789` repeated (each glyph is exactly 6 px wide with the VWF table:
ink 5 + the renderer's 1 px gap), so a shot shows the id first and the box clips the ruler at the variant's width.
Strings are classified first (tools/mark.py --report) and only real text is marked:

| class | rule | action |
|---|---|---|
| empty | `""` | left empty (317 strings must stay empty) |
| blank | only spaces | left as is |
| numeric | only digits, spaces and `+-./:%` | left as is (counters, per-cent signs) |
| key | half-width katakana with `&` (internal data keys, e.g. `ｶﾂ&ﾚﾂ&ｷｯｶ`) | left as is |
| text | everything else | marker + ruler; `\\n` line breaks and `$L`/`$P01`/`%` tokens are kept |

    python -X utf8 tools/mark.py --report                  # classes, counts, the samples worth a look
    python -X utf8 tools/mark.py --out work/marker/marker.nds --map work/marker/map.tsv
    python -X utf8 tools/mark.py --torture 85 1 --out work/marker/torture.nds   # glyph torture line instead

The arm9 strings are marked in place (they cannot grow yet, docs/re/text.md): `a<index>` when the slot allows it,
else the shortest suffix that fits; a string too short for two characters is left alone and reported.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import bbq  # noqa: E402
import build  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import ndspy.rom  # noqa: E402

RULER = ("0123456789" * 3)[:30]
TOKEN = re.compile(r"\$[A-Z]\d{0,2}|%[-+ 0-9.]*[a-zA-Z%]")
NUMERIC = re.compile(r"^[\s0-9+\-./:%]+$")
KEY = re.compile(r"^[\uff61-\uff9f&\s]*&[\uff61-\uff9f&\s]*$")  # half-width katakana + '&' internal keys
PATH = re.compile(r"^(\./|/|[A-Za-z]:\\)|\.(bin|dat|sdat|bbq|agl|narc|pak)$", re.I)  # file names arm9 passes to the loader
TORTURE = "".join(chr(c) for c in range(0x20, 0x7F)) + "  \"'`~"  # printable ASCII, then awkward repeats


def marker(table, index):
    return f"{table:03d}:{index:04d}"


def classify(text):
    """(class, why) for one string."""
    if text == "":
        return "empty", ""
    if not text.strip():
        return "blank", ""
    if NUMERIC.match(text):
        return "numeric", ""
    if PATH.search(text):
        return "path", ""
    if KEY.match(text):
        return "key", ""
    return "text", ""


def marked(text, table, index, ruler=RULER):
    """The marker text for one string: id + the tokens it must keep, `|` + ruler on each original line."""
    lines = text.split("\n")
    out = []
    for k, line in enumerate(lines):
        if line == "":
            out.append("")
            continue
        toks = "".join(m.group(0) for m in TOKEN.finditer(line))
        out.append((marker(table, index) if k == 0 else "") + toks + ("|" + ruler if ruler else ""))
    return "\n".join(out)


def arm9_mark(index, text, move=False):
    """Marker for an arm9 string. In place it must fit the original slot (bytes excluding the NUL); with `move` the
    marker can be as long as we like (it goes into the ITCM tail, arm9.relocate)."""
    if move:
        return f"a{index}"
    room = len(text.encode("cp932"))
    for cand in (f"a{index}", f"a{index % 100:02d}", f"{index % 10}"):
        if len(cand) <= room and room >= 2:
            return cand
    return None


def plan(tables, arm9_strings, ruler=RULER, arm9_mark_on=True, arm9_range=None, move=False):
    """{ez index: [new strings]} and {arm9 offset: marker}, plus the class counts and odd cases."""
    counts, odd, bbq_plan, a9_plan = {}, [], {}, {}
    lo, hi = arm9_range or (0, len(arm9_strings))
    for i, (name, raw, strs) in sorted(tables.items()):
        new = list(strs)
        for k, s in enumerate(strs):
            cls, _ = classify(s)
            counts[cls] = counts.get(cls, 0) + 1
            if cls == "text":
                new[k] = marked(s, i, k, ruler)
            elif cls in ("blank", "numeric", "key"):
                odd.append((i, k, cls, s))
        if new != strs:
            bbq_plan[i] = new
    for k, (off, s) in enumerate(arm9_strings):
        if not arm9_mark_on or not lo <= k < hi:
            continue
        cls, _ = classify(s)
        counts[cls] = counts.get(cls, 0) + 1
        if cls != "text":
            continue
        m = arm9_mark(k, s, move)
        if m is None:
            odd.append(("arm9", k, "too-short", f"{arm9.BASE + off:#x} {s!r}"))
        else:
            a9_plan[off] = m
    return bbq_plan, a9_plan, counts, odd


def build_marked(out, map_path=None, ruler=RULER, only=None, arm9_mark_on=True, arm9_range=None, move=False):
    rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
    tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    tables = extract.bbq_files(tbl, dat)
    if only:
        keep = re.compile(only)
        tables = {i: t for i, t in tables.items() if keep.search(t[0]) or keep.search(f"{i:04d}")}
    strings9 = arm9.strings(rom.arm9)
    bbq_plan, a9_plan, counts, odd = plan(tables, strings9, ruler, arm9_mark_on, arm9_range, move)

    ez = {}
    for i, new in bbq_plan.items():
        raw = tables[i][1]
        rebuilt = bbq.rebuild(raw, [s.encode("cp932") for s in new])
        ez[i] = rebuilt + bytes(-len(rebuilt) % 16)
    ez.update(font.edits(tbl, dat, extract.unpack))
    if move:  # writable buffers cannot move (arm9.BUFFERS): they keep their Japanese in a moved-marker build
        a9_plan = {o: t for o, t in a9_plan.items() if o not in arm9.BUFFERS}
    a9 = arm9.relocate(rom.arm9, a9_plan) if move and a9_plan else arm9.replace(rom.arm9, a9_plan)
    data = build.build(ez, a9)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)

    mapping = []
    for i, new in sorted(bbq_plan.items()):
        name = tables[i][0]
        for k, s in enumerate(tables[i][2]):
            if classify(s)[0] == "text":
                mapping.append((marker(i, k), i, name, k, s))
    mapping += [("a%d" % k, 0, "arm9", k, s) for k, (off, s) in enumerate(strings9) if off in a9_plan]
    if map_path:
        p = Path(map_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("marker\tez\tname\tindex\tjp\n")
            for m, i, name, k, s in mapping:
                f.write(f"{m}\t{i}\t{name}\t{k}\t{s!r}\n")
    return out, len(mapping), counts, odd


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "work" / "marker" / "marker.nds"))
    ap.add_argument("--map", default=str(ROOT / "work" / "marker" / "map.tsv"))
    ap.add_argument("--report", action="store_true", help="print the class counts and the odd cases, build nothing")
    ap.add_argument("--ruler", type=int, default=len(RULER), help="digits per line after the id (0 = id only)")
    ap.add_argument("--only", default="", help="mark only tables whose name or index matches this regex")
    ap.add_argument("--no-arm9", action="store_true", help="leave the arm9 strings alone (bisecting a hang)")
    ap.add_argument("--arm9-range", default="", metavar="LO:HI", help="mark only arm9 strings in this index range")
    ap.add_argument("--arm9-move", action="store_true",
                    help="move the arm9 markers into the ITCM tail (arm9.relocate) instead of fitting them in place")
    ap.add_argument("--torture", nargs=2, type=int, metavar=("EZ", "INDEX"),
                    help="write the glyph torture line into one string instead of markers")
    a = ap.parse_args()

    if a.report:
        rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        tables = extract.bbq_files(tbl, dat)
        _, _, counts, odd = plan(tables, arm9.strings(rom.arm9))
        print(json.dumps(counts, indent=1, sort_keys=True))
        by = {}
        for i, k, cls, s in odd:
            by.setdefault(cls, []).append((i, k, s))
        for cls, items in sorted(by.items()):
            print(f"\n{cls}: {len(items)}")
            for i, k, s in items[:25]:
                print(f"  {i}:{k} {s!r}")
        return

    if a.torture:
        rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
        tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
        tables = extract.bbq_files(tbl, dat)
        i, k = a.torture
        name, raw, strs = tables[i]
        new = list(strs)
        per = 32
        lines = [TORTURE[n:n + per] for n in range(0, len(TORTURE), per)]
        new[k:k + len(lines)] = lines
        rebuilt = bbq.rebuild(raw, [s.encode("cp932") for s in new])
        ez = {i: rebuilt + bytes(-len(rebuilt) % 16)}
        ez.update(font.edits(tbl, dat, extract.unpack))
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(build.build(ez, None))
        print(out)
        adv = font.advances(font.proportional(extract.unpack(tbl, dat, {336})[336], font.GLYPHS.get(336)))
        for ln in lines:
            print(f"  {font.width(ln, adv)} px  {ln!r}")
        return

    rng = tuple(int(x) for x in a.arm9_range.split(":")) if a.arm9_range else None
    out, n, counts, odd = build_marked(a.out, a.map, ("0123456789" * 4)[:a.ruler], a.only, not a.no_arm9, rng,
                                       a.arm9_move)
    print(f"{out}: {n} markers; classes {counts}; map {a.map}")


if __name__ == "__main__":
    main()
