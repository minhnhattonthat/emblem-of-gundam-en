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


def ids():
    return set(CREDITS)


def edits(tbl, dat, unpack):
    raw = unpack(tbl, dat, ids())
    return {i: credit_page(raw[i], CREDITS[i]) for i in CREDITS}


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


if __name__ == "__main__":
    if sys.argv[1:] == ["preview"]:
        preview()
