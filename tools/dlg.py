"""dlg.py: `\\0DLG` textures (3D-layer images, docs/re/graphics.md §DLG) - parse, and redraw the staff roll in English.

    python -X utf8 tools/dlg.py preview      # work/gfx_en/credits_*.png (original | English)

DLG: u32 `\\0DLG`, u32 1, u32 total size, 2 x u32 0, u32 pixel bytes P, u32 palette bytes L; pixels at 0x1c, then
the BGR555 palette. The staff-roll pages 4137-4169 are one 256x192 4bpp texture each (16 colours: 0 transparent,
1 black outline, 2-15 a grey ramp). The roll scrolls the pages back to back, so every line keeps its rows: each ink
band (one Japanese line) is erased and its English drawn centred on the band's own centre, names in Liberation Serif
Bold 15 px, role captions 11 px (bands <= 14 rows tall), white with a 1 px black outline like the original.
Names: Hepburn without macrons, given name first (D2, D3); uncertain readings are listed in docs/status.md.
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts" / "LiberationSerif-Bold.ttf"
W, H = 256, 192

# one entry per ink band, top to bottom; None keeps the band, "" erases it
CREDITS = {
    4137: ["Scenario", "Yuri Shibamura", "Ukyo Kodachi", "Kiyomune Miwa", "Ko Shigenobu", "Ren Kanan",
           "Game Design", "Yuri Shibamura"],
    4139: ["Development Production", "MICROVISION Inc.", "Mao Yamamoto", "Yoshimasa Koyama", "Director",
           "Takahiro Suzuki"],
    4141: ["Planners", "Yoshimasa Koyama", "Takeru Sugaya", "Scripters", "Yoshimasa Koyama", "Takeru Sugaya",
           "Masahiro Fuke", "Yoshikazu Fujishita"],
    4143: ["Main Programmer", "Kentaro Nakamura", "Programmers", "Seiji Takeshita", "Yutaka Okajima",
           "Masakazu Shikata", "System Programmer", "Rintaro Hamano"],
    4145: ["Main Designer", "Kenichi Okayama", "Designers", "Takumi Nakajima", "Tsuyoshi Ono", "Special Thanks",
           "Yoshiaki Goto"],
    4147: ["Video Production Support", "Graphic Studio Danburi", "Isamu Kondo", "Shogo Sato", "Yoko Wakatsuki",
           "Ayako Kuno"],
    4149: ["Sound Production", "noisycroak Co., Ltd.", "", "Sound Producer", "Hideki Sakamoto", "Sound Director"],
    4151: ["Tsuyoshi Yukawa", "Composer / Sound Effects", "Yasushi Asada", "Character Graphics", None,
           "Art Director"],
    4153: ["Harutaka Ota", "Designers", "Tomo Kyozuka", "Koichiro Imai", "Hisanori Komatsu", "Production",
           "BEC Co., Ltd."],
    4155: ["Yoshihiro Okamoto", "Takeo Isogai", "Yuri Shibamura", "Shinsuke Kayumi", "Debug", "BEC Co., Ltd.",
           "Pole To Win Co., Ltd."],
    4157: ["Promotion", "Hirotaka Watanabe", "Go Kurosawa", "Masayuki Kimura", "Sales", "Fuyuki Nishizawa",
           "Hiroshi Saeki", "Naoki Kumada", "Masaki Hoshiai", "Hideyuki Yamazaki"],
    4159: ["Meyo Nozawa", "Shoya Yamazaki", "Aya Morioka", "Yota Ando", "Rie Komaki", "Tatsuaki Fujii",
           "Masayuki Hirano", "Makiko Tamura", "Wakako Hazama", "Sora Matsuda"],
    4161: ["Kenji Tsuchiya", "Kenichi Toida", "In Cooperation With", "SOTSU Co., Ltd.", "Retsu Tamura",
           "Homare Muto"],
    4163: ["SUNRISE Inc.", "Akihiro Morita", "Takeshi Mukai", "Koji Nakajima", "Yusuke Inui"],
    4165: ["Special Thanks", "Takashi Shoji", "Hidehisa Ichikawa", "Tomoaki Imanishi", "Hirofumi Inagaki",
           "Norihiko Ushimura", "Yoshito Kikuchi"],
    4167: ["Producer", "Kei Hirono", "Chief Producer"],
    4169: ["Yuji Tsuyuki", "Yoshitaka Goto", "Executive Producer", "Shin Unozawa"],
}


def parse(d):
    """(pixel bytes, [BGR555 colours]) of a DLG file."""
    assert d[:4] == b"\0DLG", d[:4]
    p, n = struct.unpack_from("<II", d, 0x14)
    return d[0x1c:0x1c + p], list(struct.unpack_from(f"<{n // 2}H", d, 0x1c + p))


def unpack4(pix, w):
    """4bpp linear texture -> rows of indices (low nibble = left pixel)."""
    v = [x for b in pix for x in (b & 15, b >> 4)]
    return [v[y * w:(y + 1) * w] for y in range(len(v) // w)]


def pack4(rows):
    v = [x for r in rows for x in r]
    return bytes(v[i] | v[i + 1] << 4 for i in range(0, len(v), 2))


def bands(rows):
    """[(y0, y1, x0, x1)] of each run of rows with ink (y1/x1 exclusive)."""
    out, y = [], 0
    while y < len(rows):
        if any(rows[y]):
            y0 = y
            while y < len(rows) and any(rows[y]):
                y += 1
            xs = [x for r in rows[y0:y] for x, v in enumerate(r) if v]
            out.append((y0, y, min(xs), max(xs) + 1))
        y += 1
    return out


def _lum(c):
    return ((c & 31) * 3 + (c >> 5 & 31) * 6 + (c >> 10 & 31)) / 310


def draw_line(rows, band, text, pal):
    """Erase the band and draw `text` centred on it: white fill, grey antialias ramp, 1 px black outline."""
    y0, y1, x0, x1 = band
    for y in range(y0, y1):
        rows[y][:] = [0] * W
    if not text:
        return
    size = 11 if y1 - y0 <= 14 else 15  # role captions are 13 rows tall, names 16-17
    font = ImageFont.truetype(str(FONT), size)
    l, _, r, _ = font.getbbox(text)
    _, t, _, b = font.getbbox("H")  # centre the cap height, so descenders don't lift the line
    m = Image.new("L", (W, H))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    ImageDraw.Draw(m).text((cx - (l + r) // 2, cy - (t + b) // 2), text, font=font, fill=255)
    a = m.load()
    ramp = sorted(range(2, 16), key=lambda i: _lum(pal[i]))
    lums = [_lum(pal[i]) for i in ramp]
    for y in range(max(0, y0 - 2), min(H, y1 + 2)):
        for x in range(W):
            v = a[x, y] / 255
            if v > 0.12:
                k = min(range(len(ramp)), key=lambda j: abs(lums[j] - v))
                rows[y][x] = ramp[k]
            elif any(a[x + dx, y + dy] > 96 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                     if 0 <= x + dx < W and 0 <= y + dy < H):
                rows[y][x] = 1


def credit_page(d, lines):
    pix, pal = parse(d)
    rows = unpack4(pix, W)
    bs = bands(rows)
    assert len(bs) == len(lines), (len(bs), len(lines))
    for band, text in zip(bs, lines):
        if text is not None:
            draw_line(rows, band, text, pal)
    new = pack4(rows)
    assert len(new) == len(pix)
    return d[:0x1c] + new + d[0x1c + len(pix):]


BPP = {2: 2, 3: 4, 4: 8}  # DS texture formats handled: 4-colour, 16-colour, 256-colour


def textures(lga, p):
    """Sub-textures of a DLG from its LGA's texture table: 16-byte records (u16 palette base in 8-colour units,
    u16 format, u16 id, u16 1, u16 S, u16 T (size 8<<n), u32 byte offset into the pixels), ids consecutive and
    offsets ascending. Height = bytes up to the next offset (rows past it are padding the DLG doesn't store)."""
    best = []
    for at in range(0, len(lga) - 16, 2):
        recs = []
        for q in range(at, len(lga) - 15, 16):
            pal, fmt, tid, _, s, t, off = struct.unpack_from("<HHHHHHI", lga, q)
            if fmt not in (1, 2, 3, 4, 6, 7) or s > 7 or t > 7 or off >= p or (recs and (
                    tid != recs[-1]["id"] + 1 or off <= recs[-1]["off"])):
                break
            recs.append({"id": tid, "fmt": fmt, "pal": pal * 8, "w": 8 << s, "off": off})
        if len(recs) > len(best):
            best = recs
    for k, r in enumerate(best):
        end = best[k + 1]["off"] if k + 1 < len(best) else p
        r["h"] = (end - r["off"]) * 8 // (BPP.get(r["fmt"], 8) * r["w"])
    return {r["id"]: r for r in best}


def _get(pix, r):
    b, w = BPP[r["fmt"]], r["w"]
    n = w * r["h"]
    raw = pix[r["off"]:r["off"] + n * b // 8]
    if b == 8:
        v = list(raw)
    elif b == 4:
        v = [x for c in raw for x in (c & 15, c >> 4)]
    else:
        v = [c >> s & 3 for c in raw for s in (0, 2, 4, 6)]
    return [v[y * w:(y + 1) * w] for y in range(r["h"])]


def _put(pix, r, rows):
    b = BPP[r["fmt"]]
    v = [x for row in rows for x in row]
    if b == 8:
        raw = bytes(v)
    elif b == 4:
        raw = bytes(v[i] | v[i + 1] << 4 for i in range(0, len(v), 2))
    else:
        raw = bytes(v[i] | v[i + 1] << 2 | v[i + 2] << 4 | v[i + 3] << 6 for i in range(0, len(v), 4))
    pix[r["off"]:r["off"] + len(raw)] = raw


def _rgb(c):
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3)


def relabel(d, lga, edits_, fonts=None):
    """Redraw text rects in sub-textures: [(tex id, (x, y, w, h), text, font px, style)]. The rect is cleared by
    interpolating each row between the pixels just left and right of it, then the text is drawn centred in the
    original's lightest colour, with a 1 px outline (style "outline") or a +1,+1 shadow ("shadow") in its darkest
    colour, and every pixel snapped to the nearest opaque colour of the texture's own palette slice."""
    pix, pal = parse(d)
    pix = bytearray(pix)
    texs = textures(lga, len(pix))
    for tid, rect, text, size, style in edits_:
        r = texs[tid]
        x, y, w, h = rect or (1, 1, r["w"] - 2, r["h"] - 2)  # None: the whole texture
        rows = _get(pix, r)
        n = 1 << BPP[r["fmt"]]
        cols = {i: _rgb(pal[r["pal"] + i]) for i in range(1, n) if r["pal"] + i < len(pal)}
        lum = lambda c: c[0] * 3 + c[1] * 6 + c[2]  # noqa: E731
        inside = [cols[rows[yy][xx]] for yy in range(y, y + h) for xx in range(x, x + w) if rows[yy][xx]]
        ink, dark = max(inside, key=lum), min(inside, key=lum)
        im = Image.new("RGB", (w, h))
        clear = set()  # rows with transparent pixels on both sides stay transparent behind the text
        for yy in range(h):
            a, b = rows[y + yy][x - 1], rows[y + yy][x + w]
            if (not a or not b) and style != "solid":  # one transparent side is enough (2199: a dash on the right)
                clear.add(yy)
            ca, cb = cols.get(a, (0, 0, 0)), cols.get(b, (0, 0, 0))
            period = int(style.split("p")[-1]) if "p" in style.replace("shadow", "") else 0
            for xx in range(w):
                if period:  # repeat the background pattern (a grid) from one period left of the rect
                    src = rows[y + yy][x + xx - period * ((xx // period) + 1)]
                    im.putpixel((xx, yy), cols.get(src, (0, 0, 0)))
                    continue
                t = (xx + 1) / (w + 1)
                im.putpixel((xx, yy), tuple(round(ca[k] * (1 - t) + cb[k] * t) for k in range(3)))
        m = Image.new("L", (w, h))
        if isinstance(size, int):  # TrueType, antialiased; shrinks until it fits the rect (outline/shadow included)
            for px_ in range(size, 7, -1):
                font = ImageFont.truetype(str(ROOT / "fonts" / "LiberationSans-Bold.ttf"), px_)
                l, _, rr, _ = font.getbbox(text)
                if rr - l + 4 <= w:
                    break
            _, t, _, bb = font.getbbox("H")
            pos = ((w - (rr - l)) // 2 - l, (h - (bb - t)) // 2 - t)
            ImageDraw.Draw(m).text(pos, text, font=font, fill=255)
        else:  # the game's own NFTR font (336 / 337), 1-bit, for small captions
            import gfx
            pts = gfx._text_mask(text, fonts[size])
            cap = [p for p in gfx._text_mask("H", fonts[size])]
            tw = max(p[0] for p in pts) + 1
            ct, cb = min(p[1] for p in cap), max(p[1] for p in cap)
            ox, oy = (w - tw) // 2, (h - (cb - ct + 1)) // 2 - ct
            for px_, py_ in pts:
                if 0 <= px_ + ox < w and 0 <= py_ + oy < h:
                    m.putpixel((px_ + ox, py_ + oy), 255)
        assert not text or (m.getbbox() and m.getbbox()[0] > 0 and m.getbbox()[2] < w), f"{text!r} does not fit {w} px"
        ma = m.load()
        under = Image.new("L", (w, h))
        ua = under.load()
        for yy in range(h):
            for xx in range(w):
                if style == "outline":
                    ua[xx, yy] = max(ma[xx + dx, yy + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                                     if 0 <= xx + dx < w and 0 <= yy + dy < h)
                elif style == "shadow" and xx and yy:
                    ua[xx, yy] = ma[xx - 1, yy - 1]
        im = Image.composite(Image.new("RGB", (w, h), dark), im, under)
        im = Image.composite(Image.new("RGB", (w, h), ink), im, m)
        keys = list(cols)
        for yy in range(h):
            for xx in range(w):
                if yy in clear and not ma[xx, yy] and not ua[xx, yy]:
                    rows[y + yy][x + xx] = 0
                    continue
                c = im.getpixel((xx, yy))
                rows[y + yy][x + xx] = min(keys, key=lambda i: sum((cols[i][k] - c[k]) ** 2 for k in range(3)))
        _put(pix, r, rows)
    return d[:0x1c] + bytes(pix) + d[0x1c + len(pix):]


def texture_image(d, lga, tid):
    pix, pal = parse(d)
    r = textures(lga, len(pix))[tid]
    im = Image.new("RGB", (r["w"], r["h"]), (255, 0, 255))
    for y, row in enumerate(_get(pix, r)):
        for x, v in enumerate(row):
            if v:
                im.putpixel((x, y), _rgb(pal[r["pal"] + v]))
    return im


# {DLG id: [(sub-texture id, (x, y, w, h), text, font px, style)]}: Japanese captions in 3D-layer UI textures
TEXT = {
    2233: [(t, (18, 2, 114, 19), s, 12, "shadow") for t, s in (  # win/lose condition screen banners (briefNN)
        (3, "Victory Conditions"), (4, "Victory Conditions"), (5, "Defeat Conditions"), (6, "Defeat Conditions"))],
    2139: [(t, (18, 1, 44, 14), s, (336,), "outline") for t, s in (  # bottom-bar buttons (64x16, A/B/X icon left)
        (1, "Next"), (2, "Back"), (3, "End"), (4, "Menu"), (5, "OK"), (6, "Start"), (7, "End"), (8, "Info"),
        (9, "Move"), (10, "Hold"))],
    2215: [(24, (10, 1, 21, 14), "End", (337,), "outline")],  # greyed-out B button
}
TEXT[2139].append((0, (3, 1, 90, 14), "Merit Points", (336,), "outline"))  # result bar, "pts" at right kept
TEXT.update({
    2235: [(5, (16, 4, 104, 22), "Total Merit", (336,), ""), (6, (16, 4, 104, 22), "Total Merit", (336,), ""),
           (7, (24, 3, 112, 18), "Merit Points", (336,), ""), (8, (24, 3, 112, 18), "Merit Points", (336,), ""),
           (9, (30, 0, 110, 16), "Points Earned", (336,), ""), (10, (30, 0, 110, 16), "Current Points", (336,), "")],
    2197: [(0, (2, 2, 106, 31), "Battle Start", 18, "outline")],
    2199: [(0, (2, 1, 106, 24), "Battle Result", 18, "outline")],
    2203: [(2, (3, 1, 150, 32), "Skill Activated", 20, "outline"), (3, (3, 1, 150, 32), "Unit Skill", 18, "outline")],
    2205: [(2, (3, 1, 150, 32), "Skill Activated", 20, "outline"),
           (3, (1, 1, 160, 32), "Character Skill", 18, "outline")],
    2179: [(0, None, "Chain", 16, "outline")],  # battle-forecast mode banners
    2181: [(0, None, "Advance", 16, "outline")],
    2183: [(0, None, "Retreat", 16, "outline"), (1, None, "Attacker", (336,), "outline")],
    2185: [(0, None, "Retreat", 16, "outline"), (1, None, "Defender", (336,), "outline")],
    2187: [(0, None, "Continue", 16, "outline")],
    2193: [(0, None, "WIPED", 24, "outline"), (1, None, "OUT", 24, "outline"), (15, (1, 1, 14, 14), "", 8, "solid")],  # 全|滅, 機
    2211: [(0, None, "Shot", 14, "outline"), (1, None, "Down", 14, "outline"), (12, None, "", 8, ""),  # 撃|破 N 機
           (13, None, "Lost", 14, "outline"), (14, None, "", 8, "")],  # 損|失
    2225: [(0, (30, 1, 196, 14), "Select Baton Route", (336,), "outline"),
           (10, (12, 1, 232, 14), "Where will you pass the baton of history?", (336,), "outline")],
    2227: [(12, (60, 1, 66, 14), "Scenario", (336,), "solid"), (13, (5, 1, 66, 14), "Chart", (336,), "solid")],
    2243: [(t, (2, 1, 252, 38), s, (336,), "") for t, s in (
        (3, "Saving..."), (4, "Save complete."), (8, "Creating system data..."), (9, "System data created."))],
    2245: [(6, (60, 6, 136, 36), "Retirement Notice", 20, "shadow p16"),  # unit retirement banner, grid kept
           (7, (60, 6, 136, 36), "Retirement Notice", 20, "shadow p16")],
})


def ids():
    return set(CREDITS) | set(TEXT)


def edits(tbl, dat, unpack):
    import gfx
    raw = unpack(tbl, dat, ids() | {i - 1 for i in TEXT} | {336, 337})
    fonts = {(f,): gfx._glyphs(f, raw[f]) for f in (336, 337)}
    out = {i: credit_page(raw[i], CREDITS[i]) for i in CREDITS}
    out.update({i: relabel(raw[i], raw[i - 1], e, fonts) for i, e in TEXT.items()})
    return out


def image(d, w=W):
    pix, pal = parse(d)
    im = Image.new("RGB", (w, len(pix) * 2 // w), (0, 0, 80))
    for y, r in enumerate(unpack4(pix, w)):
        for x, v in enumerate(r):
            if v:
                c = pal[v]
                im.putpixel((x, y), ((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
    return im


def preview():
    ez, dst = ROOT / "work" / "ez", ROOT / "work" / "gfx_en"
    dst.mkdir(parents=True, exist_ok=True)
    for i, lines in CREDITS.items():
        d = (ez / f"{i:04d}.bin").read_bytes()
        s = Image.new("RGB", (2 * W + 4, H), (255, 0, 255))
        s.paste(image(d), (0, 0))
        s.paste(image(credit_page(d, lines)), (W + 4, 0))
        s.save(dst / f"credits_{i}.png")
    print(len(CREDITS), "pages ->", dst)


def preview_text(only=None):
    """work/gfx_en/tex_<id>.png: every edited sub-texture, original left, English right, x3."""
    import gfx
    ez, dst = ROOT / "work" / "ez", ROOT / "work" / "gfx_en"
    fonts = {(f,): gfx._glyphs(f, (ez / f"{f:04d}.bin").read_bytes()) for f in (336, 337)}
    for i, e in TEXT.items():
        if only and i not in only:
            continue
        d, lga = (ez / f"{i:04d}.bin").read_bytes(), (ez / f"{i - 1:04d}.bin").read_bytes()
        n = relabel(d, lga, e, fonts)
        tids = sorted({x[0] for x in e})
        pairs = [(texture_image(d, lga, t), texture_image(n, lga, t)) for t in tids]
        W2 = max(a.width for a, _ in pairs)
        s = Image.new("RGB", (2 * W2 + 4, sum(a.height + 2 for a, _ in pairs)), (40, 40, 40))
        y = 0
        for a, b in pairs:
            s.paste(a, (0, y)); s.paste(b, (W2 + 4, y)); y += a.height + 2
        s.resize((s.width * 3, s.height * 3), Image.NEAREST).save(dst / f"tex_{i}.png")
    print("->", dst)


if __name__ == "__main__":
    if sys.argv[1:] == ["preview"]:
        preview()
    elif sys.argv[1:2] == ["text"]:
        preview_text({int(a) for a in sys.argv[2:]})
