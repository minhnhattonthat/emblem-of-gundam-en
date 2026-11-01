"""font.py: the game's two NFTR fonts, and the proportional (VWF) advance table the build installs.

What the phase 5 engine spike measured in-game (docs/re/font.md):
- the renderer takes each glyph's **CWDH advance** and adds a 1 px gap, so the pen moves `advance + 1` per glyph
  (ASCII default advance 6 -> 7 px pitch; full-width kana advance 12 -> 13 px). It does *not* use a fixed cell, so a
  per-glyph advance table is a real VWF.
- both fonts (0336 11x11, 0337 9x9) are drawn somewhere: 0336 for dialogue, narration and menu text, 0337 for the
  small screen labels.

`proportional()` sets each printable ASCII glyph's advance to its ink width (a 1 px gap is the renderer's own), and
leaves kana and everything else alone: pitch becomes ink + 1 px instead of 7 px, ~25 % more characters per line.

    python -X utf8 tools/font.py                  # the advance table both fonts get, with the old values
    python -X utf8 tools/font.py --sheet out.png  # ASCII glyph sheet of both fonts
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import nftr  # noqa: E402

FONT_IDS = (336, 337)
PRINTABLE = range(0x20, 0x7F)
SPACE_ADVANCE = 3  # the space glyph has no ink; 3 + the renderer's 1 px gap = a 4 px word gap
# redrawn glyphs, rows from the top of the cell: 0336's own > and < are 11 px tall parens ("->" read as "-)",
# visual QA); chevrons with the tip on the "-" row
_CHEVRON = ["", "", "#", ".#", "..#", "...#", "..#", ".#", "#"]
# ' and " are 3 px diagonals that read as acute accents ("Let´s", playtest): straight ticks instead
_TICKS = {"'": ["#", "#"], '"': ["#.#", "#.#"]}
GLYPHS = {336: {">": _CHEVRON, "<": [r.ljust(4, ".")[::-1] if r else r for r in _CHEVRON], **_TICKS}, 337: _TICKS}


def _chunks(d):
    """(magic, offset of the chunk body, size) for every chunk, in file order."""
    hsize = struct.unpack_from("<H", d, 0xC)[0]
    off, out = hsize, []
    while off + 8 <= len(d):
        magic, size = d[off:off + 4], struct.unpack_from("<I", d, off + 4)[0]
        if size == 0:
            break
        out.append((magic, off + 8, size))
        off += size
    return out


def _cwdh(d):
    """(first glyph, body offset) of the CWDH chunk."""
    for magic, body, _ in _chunks(d):
        if magic == b"HDWC":
            return struct.unpack_from("<H", d, body)[0], body
    raise ValueError("font has no CWDH chunk")


def ink_width(f, d, g):
    """Width in pixels of glyph g's ink (0 when the glyph is blank)."""
    xs = [x for row in nftr.glyph(f, d, g) for x, v in enumerate(row) if v]
    return max(xs) - min(xs) + 1 if xs else 0


def advances(d):
    """{codepoint: (left, width, advance)} for the printable ASCII the CWDH table covers."""
    f = nftr.parse(d)
    return {c: f["widths"][f["cmap"][c]] for c in PRINTABLE if c in f["cmap"] and f["cmap"][c] in f["widths"]}


def proportional(d, glyphs=None):
    """Font bytes with every printable ASCII advance set to its ink width. Same length; kana untouched.
    glyphs = {char: rows of "#"/"."} redraws those glyphs first (1 bpp fonts)."""
    f = nftr.parse(d)
    first, body = _cwdh(d)
    out = bytearray(d)
    for ch, rows in (glyphs or {}).items():
        assert f["bpp"] == 1, f["bpp"]
        w, h, size = f["cell_w"], f["cell_h"], f["glyph_size"]
        bits = 0
        for r in range(h):
            row = rows[r] if r < len(rows) else ""
            for c in range(w):
                bits = bits << 1 | (c < len(row) and row[c] == "#")
        at = f["glyph_off"] + f["cmap"][ord(ch)] * size
        out[at:at + size] = (bits << (size * 8 - w * h)).to_bytes(size, "big")
    d = bytes(out)
    for c in PRINTABLE:
        g = f["cmap"].get(c)
        if g is None or g not in f["widths"]:
            continue
        adv = ink_width(f, d, g) if c != 0x20 else SPACE_ADVANCE
        if struct.unpack_from("<H", d, body)[0] <= g <= struct.unpack_from("<H", d, body + 2)[0]:
            out[body + 8 + 3 * (g - first) + 2] = max(1, adv)
            # The renderer draws the glyph at pen + CWDH left; with the advance cut to the ink width that left
            # offset pushes the ink under the next glyph's cell ('in' drew as 'n' in-game). Ink starts at column 0
            # in this font, so left = 0 puts it at the pen.
            out[body + 8 + 3 * (g - first)] = 0
    return bytes(out)


def width(text, table, halfwidth=0):
    """Pixel width of `text` on a line: sum(advance + 1) for ASCII, the font's own advance + 1 for anything else.
    `table` is advances() (ASCII only); a codepoint outside it counts as `halfwidth` (a full-width glyph: 12/10)."""
    total = 0
    for ch in text:
        o = ord(ch)
        if o in table:
            total += table[o][2] + 1
        else:
            total += halfwidth + 1
    return total


def edits(tbl, dat, unpack):
    """{ez index: font bytes} with the proportional table, for build.py. `unpack` is extract.unpack."""
    fonts = unpack(tbl, dat, set(FONT_IDS))
    return {i: proportional(f, GLYPHS.get(i)) + bytes(-len(f) % 16) for i, f in fonts.items()}


if __name__ == "__main__":
    if "--sheet" in sys.argv:
        from PIL import Image

        out = sys.argv[sys.argv.index("--sheet") + 1]
        rows = []
        for fid in FONT_IDS:
            d = (ROOT / "work" / "ez" / f"{fid:04d}.bin").read_bytes()
            f = nftr.parse(d)
            cw, ch, scale = f["cell_w"], f["cell_h"], 3
            per = 24
            codes = list(PRINTABLE)
            rows.append((fid, cw, ch, scale, per, codes, f, d))
        im = Image.new("L", (24 * (11 + 3) * 3, 2 * 2 * (12 + 3) * 3), 32)
        px = im.load()
        for n, (fid, cw, ch, scale, per, codes, f, d) in enumerate(rows):
            for k, c in enumerate(codes):
                g = f["cmap"].get(c)
                if g is None:
                    continue
                ox = (k % per) * (cw + 3) * scale
                oy = (n * 2 + k // per) * (ch + 3) * scale
                for y, row in enumerate(nftr.glyph(f, d, g)):
                    for x, v in enumerate(row):
                        if v:
                            for dy in range(scale):
                                for dx in range(scale):
                                    px[ox + x * scale + dx, oy + y * scale + dy] = 255
        im.save(out)
        print(out)
        sys.exit()
    for fid in FONT_IDS:
        d = (ROOT / "work" / "ez" / f"{fid:04d}.bin").read_bytes()
        f = nftr.parse(d)
        old = advances(d)
        new = proportional(d, GLYPHS.get(fid))
        n = nftr.parse(new)
        print(f"font {fid}: {f['cell_w']}x{f['cell_h']}, encoding {f['encoding']}")
        print("  old advances", {chr(c): t[2] for c, t in list(old.items())[:8]})
        print("  new advances", {chr(c): advances(new)[c][2] for c in list(old)[:8]})
        before = sum(t[2] + 1 for t in old.values())
        after = sum(t[2] + 1 for t in advances(new).values())
        print(f"  all printable ASCII: {before} px -> {after} px ({after / before:.0%})")
