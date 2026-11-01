"""stress.py: a width/length stress ROM -- the translated script with chosen strings overridden, to measure a field's
px clip or byte cap in-game (references/pipeline.md §Width gate).

    python -X utf8 tools/stress.py 3:3=ABC.. 4:8=@abc [--out work/marker/stress.nds]
    python -X utf8 tools/stress.py 4:8=@ruler       # `@ruler` = `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz`

Ids are `EZ:INDEX` (BBQ), `EZ:*` (all nonempty text in that table), or `a9:XXXXXXXX` (arm9 RAM address). Distinct letters show both a px clip (where the ink
stops) and a byte cap (which letter is last) in one shot."""
import argparse
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402

RULER = string.ascii_uppercase + string.ascii_lowercase


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edits", nargs="+", help="ID=TEXT; TEXT @ruler = A-Za-z")
    ap.add_argument("--out", default=str(ROOT / "work" / "marker" / "stress.nds"))
    a = ap.parse_args()
    script, a9 = insert.tables(), insert.arm9_texts()
    for e in a.edits:
        sid, _, text = e.partition("=")
        text = text.replace("@ruler", RULER).replace("\\n", "\n")
        if sid.startswith("a9:"):
            if sid == "a9:*":
                import arm9
                import mark
                # Formatter templates and generated team names are copied into small native buffers.
                # Stress literal UI labels only; targeted IDs remain available for a specific buffer test.
                import re
                a9 = {off: text if off not in arm9.BUFFERS and mark.classify(s)[0] == "text"
                      and not re.search(r"[%$]|(?:Team|Character|Unit) [A-Z]$", s) else s
                      for off, s in a9.items()}
            else:
                a9[int(sid[3:], 16) - 0x02000000] = text
        else:
            table, index = sid.split(":")
            t = int(table)
            if index == "*":
                import mark
                script[t] = [text if mark.classify(s)[0] == "text" else s for s in script[t]]
            else:
                script[t][int(index)] = text
    import ndspy.rom
    rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
    tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    text = extract.bbq_files(tbl, dat)
    ez = insert.ez_edits({i: raw for i, (_, raw, _) in text.items()}, script)
    ez.update(font.edits(tbl, dat, extract.unpack))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build.build(ez, insert.arm9_edit(rom.arm9, a9)))
    print(out)


if __name__ == "__main__":
    main()
