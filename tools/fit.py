"""fit.py: pixel width of English lines in the game's VWF font (0336), against a box budget from tbl/windows.json.

    python -X utf8 tools/fit.py "First line / second line" [--box story_dialogue]
    python -X utf8 tools/fit.py --refresh        # rebuild tbl/vwf336.json from the ROM (after a font change)

Lines split on ` / ` or a real newline. Width = sum(advance + 1) per glyph (docs/re/font.md); the advance table is
cached in tbl/vwf336.json so translators and the lint run without the ROM.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tbl" / "vwf336.json"
WINDOWS = ROOT / "tbl" / "windows.json"
FULLWIDTH = 12  # kana/kanji advance in font 0336 (pitch 13)


def table():
    return {int(k): v for k, v in json.loads(CACHE.read_text(encoding="utf-8")).items()}


def refresh():
    sys.path.insert(0, str(ROOT / "tools"))
    import ndspy.rom
    import build
    import extract
    import font
    rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
    tbl, dat = (rom.getFileByName(n) for n in ("EZ_TBL.BIN", "EZ_DAT.BIN"))
    d = font.proportional(extract.unpack(tbl, dat, {336})[336], font.GLYPHS.get(336))
    CACHE.write_text(json.dumps({c: v[2] for c, v in font.advances(d).items()}, indent=0), encoding="utf-8")


_T = None


def px(line):
    """Drawn width of one line in px (pen advance, including each glyph's 1 px gap)."""
    global _T
    if _T is None:
        _T = table()
    return sum(_T.get(ord(ch), FULLWIDTH) + 1 for ch in line)


def boxes():
    return json.loads(WINDOWS.read_text(encoding="utf-8"))["variants"]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--box", default="story_dialogue")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if a.refresh:
        refresh()
        print("wrote", CACHE)
        sys.exit(0)
    box = boxes()[a.box]
    lines = a.text.replace(" / ", "\n").split("\n")
    bad = 0
    for ln in lines:
        w = px(ln)
        over = w > box["px"]
        bad += over
        print(f"{w:4d}/{box['px']} {'OVER ' if over else ''}{ln}")
    if len(lines) > box.get("lines", 99):
        print(f"OVER: {len(lines)} lines, box holds {box['lines']}")
        bad += 1
    sys.exit(1 if bad else 0)
