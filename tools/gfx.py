"""gfx.py: graphics text (docs/re/graphics.md) -> English, for build.py.

Stage title cards (68, EZ 1111 + 3k: NCGR 8bpp 256 tiles, NCLR k+1, NSCR k+2): the caption above the series logo is
redrawn from the stage name in script/ (`STkkSTAGE` string 351, so a wording change there follows automatically),
in the caption's own palette ramp, then the card is re-tiled (dedup) into the same 256-tile NCGR. The logo and
everything below tile row 16 keep their pixels.

    python -X utf8 tools/gfx.py preview      # work/gfx_en/<id>.png + work/gfx_en/cards_N.png sheets (EN | JP)
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import nitro2d  # noqa: E402
import dlg  # noqa: E402

FONTS = ROOT / "fonts"
CARDS = tuple(range(1111, 1313, 3))
CAPTION_ROWS = 16  # tile rows 0-15 hold the caption, the series logo starts at row 16 on every card
SERIF = {1231, 1234, 1237, 1240, 1303}  # 0083 cards: the caption is a dark Mincho on white
KEEP = {1129}  # "06": unused test stage, digits only
COLS, VIS_W, VIS_H = 64, 256, 192  # NSCR 512x512 stored row-major; the card shows the top-left 256x192
MAX_W, SIZE = 244, 20


def stage_name(k):
    p = next((ROOT / "script" / "bbq").glob(f"*_ST{k:02d}STAGE.json"))
    return json.loads(p.read_text(encoding="utf-8"))["strings"][351]


def parse(ncgr, nscr):
    """(tile list of 64-index lists, NSCR entries list, data offsets) of one card."""
    g = nitro2d.ncgr(ncgr)
    b = nitro2d.block(nscr)
    size, = struct.unpack_from("<I", b, 16)
    ent = list(struct.unpack_from(f"<{size // 2}H", b, 0x14))
    return nitro2d.tiles(g), ent


def index_image(ts, ent):
    im = Image.new("P", (VIS_W, VIS_H))
    px = im.load()
    for r in range(VIS_H // 8):
        for c in range(VIS_W // 8):
            e = ent[r * COLS + c]
            assert e >> 12 == 0, "8bpp cards use palette 0"
            t, hf, vf = ts[e & 0x3FF], e >> 10 & 1, e >> 11 & 1
            for k, v in enumerate(t):
                x, y = k % 8, k // 8
                px[c * 8 + (7 - x if hf else x), r * 8 + (7 - y if vf else y)] = v
    return im


def layout(text, font_path):
    """(font, lines): one line at SIZE if it fits, else two balanced lines (one size for every card)."""
    f = ImageFont.truetype(str(font_path), SIZE)
    if f.getlength(text) <= MAX_W:
        return f, [text]
    words = text.split()
    best = min((max(f.getlength(" ".join(words[:i])), f.getlength(" ".join(words[i:]))), i)
               for i in range(1, len(words)))
    lines = [" ".join(words[:best[1]]), " ".join(words[best[1]:])]
    while max(f.getlength(x) for x in lines) > MAX_W:
        f = ImageFont.truetype(str(font_path), f.size - 1)
    return f, lines


def card(ncgr, nscr, nclr, text, serif=False):
    """(new ncgr bytes, new nscr bytes, preview RGB image)."""
    ts, ent = parse(ncgr, nscr)
    pal, _ = nitro2d.nclr(nclr)
    im = index_image(ts, ent)
    px = im.load()
    cap_h = CAPTION_ROWS * 8
    counts = Counter(px[x, y] for y in range(cap_h) for x in range(VIS_W))
    bg = counts.most_common(1)[0][0]
    # a two-line caption's second line dips into rows 16-17: its ink there touches the ink of row 15, the logo's
    # doesn't, so flood-fill down from row 15 and clear what is reached
    seen = [(x, cap_h - 1) for x in range(VIS_W) if px[x, cap_h - 1] != bg]
    todo, dip = list(seen), set()
    while todo:
        x, y = todo.pop()
        for nx in (x - 1, x, x + 1):
            for ny in (y, y + 1):
                if 0 <= nx < VIS_W and cap_h <= ny < cap_h + 16 and (nx, ny) not in dip and px[nx, ny] != bg:
                    dip.add((nx, ny))
                    todo.append((nx, ny))
    ys = [y for y in range(cap_h) for x in range(VIS_W) if px[x, y] != bg] + [y for _, y in dip]
    cy = (min(ys) + max(ys) + 1) / 2  # the Japanese block's centre
    for x, y in dip:
        px[x, y] = bg
    ramp = [i for i in counts if i != bg]
    fg = max(ramp, key=lambda i: sum(abs(a - b) for a, b in zip(pal[i], pal[bg])))  # the ink: furthest from bg
    # draw: coverage mask, then blend bg -> fg and snap to the caption's own ramp
    f, lines = layout(text, FONTS / ("LiberationSerif-Bold.ttf" if serif else "LiberationSans-Bold.ttf"))
    mask = Image.new("L", (VIS_W, cap_h), 0)
    d = ImageDraw.Draw(mask)
    asc, desc = f.getmetrics()
    lh = f.size + 6  # tighter than the Japanese 42 px, so the second line stays clear of the logo
    cap_top, cap_bot = f.getbbox("H")[1], f.getbbox("H")[3]
    for n, ln in enumerate(lines):
        mid = cy + (n - (len(lines) - 1) / 2) * lh
        x = (VIS_W - f.getlength(ln)) / 2
        d.text((round(x), round(mid - (cap_top + cap_bot) / 2)), ln, font=f, fill=255)
    cand = ramp + [bg]
    snap = []
    for a in range(256):
        want = [pal[bg][k] + (pal[fg][k] - pal[bg][k]) * a / 255 for k in range(3)]
        snap.append(min(cand, key=lambda i: sum((pal[i][k] - want[k]) ** 2 for k in range(3))))
    mpx = mask.load()
    for y in range(cap_h):
        for x in range(VIS_W):
            px[x, y] = snap[mpx[x, y]]
    # re-tile: tile 0 stays (the entries outside the visible area point at it), then unique tiles in screen order
    tiles, index = [ts[0]], {tuple(ts[0]): 0}
    new_ent = list(ent)
    for r in range(VIS_H // 8):
        for c in range(VIS_W // 8):
            t = tuple(px[c * 8 + k % 8, r * 8 + k // 8] for k in range(64))
            if t not in index:
                index[t] = len(tiles)
                tiles.append(list(t))
            new_ent[r * COLS + c] = index[t]
    if len(tiles) > len(ts):
        raise ValueError(f"{text!r}: {len(tiles)} tiles > {len(ts)}")
    g = nitro2d.block(ncgr)
    size, off = struct.unpack_from("<II", g, 24)
    data_at = 0x10 + (8 + off if off else 0x20)
    out_g = bytearray(ncgr)
    blob = bytes(v for t in tiles for v in t)
    out_g[data_at:data_at + size] = blob + bytes(size - len(blob))
    out_s = bytearray(nscr)
    struct.pack_into(f"<{len(new_ent)}H", out_s, 0x10 + 0x14, *new_ent)
    return bytes(out_g), bytes(out_s), _rgb(im, pal)


def _rgb(im, pal):
    flat = [v for c in pal[:256] for v in c]
    im = im.copy()
    im.putpalette(flat)
    return im.convert("RGB")


def jobs():
    """[(card id, english caption)] for every card that gets redrawn."""
    return [(cid, stage_name(k)) for k, cid in enumerate(CARDS) if cid not in KEEP]


# ---- UI labels: Japanese drawn into a screen's tiles, redrawn in place with the game's own font -----------------
# {NCGR id: [(x, y, w, h, font id, text)]} in NSCR pixels (tools/gfxgrid.py shows the grid). These screens give every
# visible cell its own tile, so a label's tiles are edited in place (labels() refuses a tile used outside the rect).
# Per rect: each pixel row's most common index is its background, the most common other index is the ink, and the
# index most often right of/below the ink is its shadow (drawn at +1,+1). Text is centred.
LABELS = {
    375: [  # stage info (top screen during a battle)
        (91, 1, 78, 15, 336, "Stage Info"), (222, 22, 30, 12, 337, "Turn"),
        (145, 73, 42, 15, 337, "Supplies"), (145, 121, 42, 15, 337, "Supplies"), (214, 146, 38, 15, 337, "Supplies"),
        (2, 162, 44, 13, 337, "Weapon"), (50, 162, 44, 13, 337, "Attack"), (98, 162, 44, 13, 337, "Defense"),
        (153, 163, 35, 12, 337, "Terrain"),
    ],
    378: [  # battle forecast (left half palette 0, right half palette 1: the two sides)
        (90, 113, 80, 14, 336, "Battle Forecast"),
        (15, 130, 35, 13, 337, "Before"), (63, 130, 35, 13, 337, "After"),
        (143, 130, 35, 13, 337, "Before"), (191, 130, 35, 13, 337, "After"),
        (100, 155, 24, 19, 337, "units"), (228, 155, 24, 19, 337, "units"),
    ],
    444: [  # team info (terrain strip 隠蔽/水/空/宇 at 168,80 not done: 16 px boxes)
        (95, 1, 68, 15, 336, "Team Info"), (164, 33, 28, 16, 337, "Units"), (235, 34, 16, 14, 337, ""),
        (205, 145, 44, 15, 337, "Supplies"),
        (4, 163, 38, 11, 337, "Weapon"), (56, 163, 34, 11, 337, "Attack"), (102, 163, 38, 11, 337, "Defense"),
        (153, 163, 38, 11, 337, "Terrain"),
        # bottom-left screen of the 512x512 atlas = prep 編成チーム情報 (two teams side by side); D18 short forms
        (78, 257, 100, 14, 336, "Team Formation"),
        # the same labels and terrain strip also sit in the top-left screen, drawn from the same tiles (twins)
        *[(x, y0 + y, 28, 13, 337, s) for x, y0 in ((2, 256), (130, 256), (2, 24)) for y, s in (
            (17, "Atk"), (33, "Def"), (49, "Move"), (65, "Cost"), (81, "Supply"))],
        *[(x0 + 16 * k, y0, 16, 13, 337, s, "v", f"c{x0 - 4}", "W") for x0, y0 in ((40, 353), (168, 353), (168, 81)) for k, s in enumerate(
            ("Lnd", "Rgh", "Wtr", "Air", "Spc"))],
        # top-right screen = ユニット情報 (map_unit), bottom-right = キャラクター情報 (map_chara)
        (346, 1, 78, 15, 336, "Unit Info", "h", "W"), (336, 257, 104, 15, 336, "Character Info", "h", "W"),
        *[(258, 33 + 16 * k, 28, 13, 337, s) for k, s in enumerate(("Atk", "Def", "Move", "Cost", "Supply", "Mob"))],
        *[(424 + 16 * k, 81, 16, 13, 337, s, "v", "c420", "W") for k, s in enumerate(("Lnd", "Rgh", "Wtr", "Air", "Spc"))],
    ],
    360: [  # title: the katakana reading under the English logo goes (D16), © 創通・サンライズ -> SOTSU・SUNRISE
        (86, 112, 92, 12, 337, ""), (168, 179, 86, 12, 337, "SOTSU・SUNRISE", "l"),
    ],
    372: [(86, 124, 82, 11, 337, "")],  # extras top screen: the faded title art, its katakana reading goes too (D16)
    2121: [  # staff roll "Produced by" card
        (18, 95, 220, 20, ("LiberationSerif-Bold.ttf", 15), "BANDAI NAMCO Games Inc."),
    ],
    450: [  # scenario menu
        (74, 1, 112, 14, 336, "Scenario Menu"), (8, 177, 172, 14, 336, "See how the scenario unfolds"),
        (216, 177, 30, 14, 336, "Back"),
    ],
}


def _glyphs(fid, d):
    import nftr
    f = nftr.parse(d)
    out = {}
    for c in list(range(0x21, 0x7F)) + [0x8145]:  # ASCII + ・ (Shift-JIS 8145, the official "SOTSU・SUNRISE")
        if c in f["cmap"]:
            rows = nftr.glyph(f, d, f["cmap"][c])
            xs = [x for r in rows for x, v in enumerate(r) if v]
            if xs:
                out[chr(c) if c < 0x80 else "・"] = [r[min(xs):max(xs) + 1] for r in rows]
    if fid == 337:  # the font's own 4 px W and M have solid middles and read as H ("Heapon", visual QA): 5 px
        w5 = ["#...#"] * 4 + ["#.#.#"] * 3 + ["##.##", "#...#"]
        ink = [k for k, r in enumerate(out["H"]) if any(r)]
        for ch, rows in (("W", w5), ("M", w5[::-1])):
            out[ch] = [[0] * 5 for _ in out["H"]]
            for k, row in zip(ink, rows):
                out[ch][k] = [int(c == "#") for c in row]
    return out


def _text_mask(text, glyphs):
    """[(x, y)] ink pixels of text, advance = ink width + 1, space 3 (the build's VWF table, tools/font.py)."""
    pts, x = [], 0
    for ch in text:
        if ch == " ":
            x += 3
            continue
        g = glyphs[ch]
        pts += [(x + gx, gy) for gy, r in enumerate(g) for gx, v in enumerate(r) if v]
        x += len(g[0]) + 1
    return pts


def label_edits(cid, ncgr, nscr, nclr, fonts):
    """New NCGR bytes for one screen with its LABELS redrawn; fonts = {font id: glyphs} (_glyphs)."""
    pal, _ = nitro2d.nclr(nclr)
    g = nitro2d.ncgr(ncgr)
    ts = nitro2d.tiles(g)
    b = nitro2d.block(nscr)
    wpx, _, _, size = struct.unpack_from("<HHII", b, 8)
    ent = list(struct.unpack_from(f"<{size // 2}H", b, 0x14))
    cols = wpx // 8
    refs = Counter(e & 0x3FF for e in ent)
    free = list(range(max(refs) + 1, len(ts)))  # never-referenced slots past the last used tile
    ncol = 256 if g["bpp"] == 8 else 16

    def colour_at(x, y):
        if (x, y) in px:
            return px[x, y]
        e = ent[(y // 8) * cols + x // 8]
        k = (7 - y % 8 if e >> 11 & 1 else y % 8) * 8 + (7 - x % 8 if e >> 10 & 1 else x % 8)
        return pal[((e >> 12) * ncol + ts[e & 0x3FF][k]) % len(pal)]

    def rect_cells(x0, y0, w, h):
        return [(cx, cy) for cy in range(y0 // 8, (y0 + h - 1) // 8 + 1) for cx in range(x0 // 8, (x0 + w - 1) // 8 + 1)]

    # twin rects: same text, and each cell at the same place in its rect (2-team screens draw both columns from
    # one set of tiles): a tile referenced only from twins is edited once, in place, and the later twin skipped
    twin = Counter()
    for x0, y0, w, h, fid, text, *_ in LABELS[cid]:
        for cx, cy in rect_cells(x0, y0, w, h):
            twin[ent[cy * cols + cx], text, cx - x0 // 8, cy - y0 // 8] += 1
    assigned = {}  # twin key -> the entry its first rect was drawn into
    for x0, y0, w, h, fid, text, *align in LABELS[cid]:
        cells = rect_cells(x0, y0, w, h)
        tid = {c: ent[c[1] * cols + c[0]] for c in cells}
        key = {c: (e, text, c[0] - x0 // 8, c[1] - y0 // 8) for c, e in tid.items()}
        if all(key[c] in assigned for c in cells):  # a twin already drawn: point at its tiles
            for c in cells:
                refs[tid[c] & 0x3FF] -= 1
                refs[assigned[key[c]] & 0x3FF] += 1
                ent[c[1] * cols + c[0]] = assigned[key[c]]
            continue
        # work in RGB: cells may sit on different (extended) palette slots, so raw indices don't compare
        idx, px = {}, {}
        for (cx, cy), e in tid.items():
            for k, v in enumerate(ts[e & 0x3FF]):
                x, y = k % 8, k // 8
                xy = cx * 8 + (7 - x if e >> 10 & 1 else x), cy * 8 + (7 - y if e >> 11 & 1 else y)
                idx[xy], px[xy] = v, pal[((e >> 12) * ncol + v) % len(pal)]
        # a tile used outside these cells, or flipped, gets a fresh slot; the others are edited in place
        for c, e in tid.items():
            if e >> 10 & 3 or refs[e & 0x3FF] > twin[key[c]]:  # used by something other than its twins
                if not free:
                    raise ValueError(f"{cid} {c}: no free tile slot for a shared tile")
                refs[e & 0x3FF] -= 1
                tid[c] = (e & 0xF000) | free.pop(0)
                refs[tid[c] & 0x3FF] += 1
                ent[c[1] * cols + c[0]] = tid[c]
            assigned[key[c]] = tid[c]
        before = dict(px)
        box = {(x, y): px[x, y] for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
        # "v": glyphs touch the left/right edges (16 px terrain cells), so only the top/bottom rows are background
        ring = {v for (x, y), v in box.items() if y in (y0, y0 + h - 1) or ("v" not in align and x in (x0, x0 + w - 1))}
        inks = Counter(v for v in box.values() if v not in ring)
        if not inks:
            raise ValueError(f"{cid}: no ink in {(x0, y0, w, h)}")
        lum = sum  # noqa: E731  (an RGB tuple's brightness)
        ring_lum = sum(lum(v) for v in ring) / len(ring)
        top = inks.most_common(1)[0][1]
        # 11 px labels sit on gradient bars whose inner shades beat the ink in count: take the strongest contrast
        # there; the 9 px labels are two-tone (fill + highlight): take the most common, the fill
        ink = max((i for i, n in inks.items() if n >= top * 0.3), key=lambda i: abs(lum(i) - ring_lum)) \
            if fid == 336 else max(inks, key=lum) if "v" in align else inks.most_common(1)[0][0]
        sh = Counter(box.get((x + dx, y + dy)) for (x, y), v in box.items() if v == ink for dx, dy in ((1, 0), (0, 1)))
        sh = [(n, i) for i, n in sh.items() if i in inks and i != ink]
        shadow = max(sh)[1] if sh and max(sh)[0] > inks[ink] // 4 else None
        if "W" in align:  # white ink (cells whose own colours have no clean fill/ink split)
            ink, shadow = (248, 248, 248), None
        cfl = [a for a in align if a[:1] == "c"]  # "c<X>": erase each row with the colour of clean column X
        if cfl:
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    px[x, y] = colour_at(int(cfl[0][1:]), y)
        elif "h" in align:  # title bar whose glyph strokes reuse the bar's glow colours: each column takes its most
            # common saturated colour (the glow is a horizontal gradient only; the glyphs are white/grey), then the
            # median of 5 columns drops what is left of glyph stems
            sat = lambda c: max(c) - min(c) >= 0.6 * max(max(c), 1)  # noqa: E731
            col = [(Counter(px[x, y] for y in range(y0 + 1, y0 + h - 1) if sat(px[x, y]))
                    or Counter([px[x, y0 + 1]])).most_common(1)[0][0] for x in range(x0, x0 + w)]
            col = [sorted(col[max(i - 2, 0):i + 3], key=sum)[len(col[max(i - 2, 0):i + 3]) // 2] for i in range(w)]
            for y in range(y0 + 1, y0 + h - 1):
                for x in range(x0, x0 + w):
                    px[x, y] = col[x - x0]
        elif not text or "b" in align:  # erase over artwork: blend each column from the row above the box to below
            def soft(x, y):  # 7 px horizontal average: a single bright pixel above/below would streak down
                cs = [colour_at(min(max(i, 0), wpx - 1), y) for i in range(x - 3, x + 4)]
                return tuple(sum(c[k] for c in cs) / len(cs) for k in range(3))
            for x in range(x0, x0 + w):
                a, c = soft(x, y0 - 1), soft(x, y0 + h)
                for y in range(y0, y0 + h):
                    t = (y - y0 + 1) / (h + 1)
                    px[x, y] = tuple(round(u + (v - u) * t) for u, v in zip(a, c))
        for y in range(y0, y0 + h) if text and "b" not in align and "h" not in align and not cfl else ():  # ink takes its row's nearest bg
            row = [px[x, y] for x in range(x0, x0 + w)]
            bgx = [k for k, v in enumerate(row) if v not in inks]
            for k, v in enumerate(row):
                if v in inks:  # a row that is all ink (glyph across a whole 16 px cell) takes the box's top row
                    px[x0 + k, y] = row[min(bgx, key=lambda j: abs(j - k))] if bgx else px[x0 + k, y0]
        if isinstance(fid, tuple):  # (ttf name in fonts/, px size): antialiased, coverage blended in RGB
            f = ImageFont.truetype(str(FONTS / fid[0]), fid[1])
            m = Image.new("L", (int(f.getlength(text)) + 4, fid[1] * 2), 0)
            ImageDraw.Draw(m).text((0, 0), text, font=f, fill=255)
            cov = {(x, y): a / 255 for (x, y), a in zip(((i % m.width, i // m.width) for i in range(m.width * m.height)), m.getdata()) if a}
            pts = list(cov)
        else:
            pts = _text_mask(text, fonts[fid])  # "" = erase only
            cov = dict.fromkeys(pts, 1.0)
        if pts:
            tw = max(p[0] for p in pts) + 1 + (shadow is not None)
            ys = [p[1] for p in pts]
            th = max(ys) - min(ys) + 1 + (shadow is not None)
            if tw > w:
                raise ValueError(f"{cid}: {text!r} {tw}px > {w}px")
            ox = x0 + (1 if align == ["l"] else (w - tw) // 2)
            oy = y0 + (h - th) // 2 - min(ys)
        for colour, d in ((shadow, 1), (ink, 0)):
            if colour is None or not pts:
                continue
            for x, y in pts:
                xy, a = (ox + x + d, oy + y + d), cov[x, y]
                px[xy] = colour if a == 1 else tuple(round(u + (v - u) * a) for u, v in zip(px[xy], colour))
        near = {}
        for (cx, cy), e in tid.items():
            q = (e >> 12) * ncol
            for k in range(64):  # a changed pixel takes the nearest colour of its own cell's palette slot
                xy = (cx * 8 + k % 8, cy * 8 + k // 8)
                if px[xy] != before[xy]:
                    key = (q, px[xy])
                    if key not in near:
                        near[key] = min(range(ncol), key=lambda i: sum(
                            (a - b) ** 2 for a, b in zip(pal[(q + i) % len(pal)], px[xy])))
                    idx[xy] = near[key]
            ts[e & 0x3FF] = [idx[cx * 8 + k % 8, cy * 8 + k // 8] for k in range(64)]
    gb = nitro2d.block(ncgr)
    size, off = struct.unpack_from("<II", gb, 24)
    data_at = 0x10 + (8 + off if off else 0x20)
    out = bytearray(ncgr)
    blob = bytes(v for t in ts for v in t) if g["bpp"] == 8 else bytes(t[k] | t[k + 1] << 4 for t in ts for k in range(0, 64, 2))
    out[data_at:data_at + len(blob)] = blob
    out_s = bytearray(nscr)
    struct.pack_into(f"<{len(ent)}H", out_s, 0x10 + 0x14, *ent)
    return bytes(out), bytes(out_s)


def ids():
    """EZ entries edits() may change (tools/romcheck.py)."""
    return {c + d for c in CARDS + tuple(LABELS) if c not in KEEP for d in (0, 2)} | dlg.ids()


def edits(tbl, dat, unpack):
    """{ez index: bytes} for build.py."""
    want = {i + d for i, _ in jobs() for d in range(3)} | {i + d for i in LABELS for d in range(3)} | {336, 337}
    raw = unpack(tbl, dat, want)
    fonts = {f: _glyphs(f, raw[f]) for f in (336, 337)}
    out = {}
    for cid in LABELS:
        g, s = label_edits(cid, raw[cid], raw[cid + 2], raw[cid + 1], fonts)
        out[cid], out[cid + 2] = g + bytes(-len(g) % 16), s + bytes(-len(s) % 16)
    for cid, text in jobs():
        g, s, _ = card(raw[cid], raw[cid + 2], raw[cid + 1], text, cid in SERIF)
        out[cid], out[cid + 2] = g + bytes(-len(g) % 16), s + bytes(-len(s) % 16)  # EZ size word rule
    out.update(dlg.edits(tbl, dat, unpack))  # 3D-layer textures: staff roll
    return out


def preview():
    ez = ROOT / "work" / "ez"
    dst = ROOT / "work" / "gfx_en"
    dst.mkdir(parents=True, exist_ok=True)
    pairs = []
    raw = {i + d: (ez / f"{i + d:04d}.bin").read_bytes() for i, _ in jobs() for d in range(3)}
    for cid, text in jobs():
        _, _, im = card(raw[cid], raw[cid + 2], raw[cid + 1], text, cid in SERIF)
        im.save(dst / f"{cid:04d}.png")
        pairs.append((cid, im, Image.open(ROOT / "work" / "gfx" / f"{cid:04d}.png").crop((0, 0, VIS_W, VIS_H))))
    per = 8
    for s in range(0, len(pairs), per):
        sheet = Image.new("RGB", (2 * VIS_W + 4, per * (VIS_H + 2)), (255, 0, 255))
        for k, (cid, a, b) in enumerate(pairs[s:s + per]):
            sheet.paste(a, (0, k * (VIS_H + 2)))
            sheet.paste(b.convert("RGB"), (VIS_W + 4, k * (VIS_H + 2)))
        sheet.save(dst / f"cards_{s // per}.png")
    print(len(pairs), "cards ->", dst)
    fonts = {f: _glyphs(f, (ez / f"{f:04d}.bin").read_bytes()) for f in (336, 337)}
    for cid in LABELS:
        rd = lambda i: (ez / f"{i:04d}.bin").read_bytes()  # noqa: E731
        pal, _ = nitro2d.nclr(rd(cid + 1))
        new, scr = label_edits(cid, rd(cid), rd(cid + 2), rd(cid + 1), fonts)
        a = nitro2d.nscr_render(scr, nitro2d.ncgr(new), pal, nitro2d.ncgr(new)["bpp"]).crop((0, 0, 256, 192))
        b = nitro2d.nscr_render(rd(cid + 2), nitro2d.ncgr(rd(cid)), pal, nitro2d.ncgr(new)["bpp"]).crop((0, 0, 256, 192))
        sheet = Image.new("RGB", (516, 192), (255, 0, 255))
        sheet.paste(a, (0, 0))
        sheet.paste(b, (260, 0))
        sheet.resize((516 * 3, 576), Image.NEAREST).save(dst / f"ui_{cid:04d}.png")
    print(len(LABELS), "UI screens ->", dst)


if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    preview()
