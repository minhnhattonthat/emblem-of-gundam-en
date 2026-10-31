"""nitro2d.py: NCLR / NCGR / NSCR parse + render (PIL), and a survey of every archive image into contact sheets.

    python -X utf8 tools/nitro2d.py survey     # work/ez -> work/gfx/NNNN.png + work/gfx/sheet_XX.png + index.tsv"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def block(d):
    return d[0x10:]  # first block after the 0x10 generic header


def nclr(d):
    b = block(d)
    bpp_code, = struct.unpack_from("<I", b, 8)
    size, off = struct.unpack_from("<II", b, 16)
    raw = b[8 + off:8 + off + size] if off else b[0x18:0x18 + size]
    cols = []
    for i in range(len(raw) // 2):
        c = raw[2 * i] | raw[2 * i + 1] << 8
        cols.append(((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31))
    return cols, 4 if bpp_code == 3 else 8


def ncgr(d):
    b = block(d)
    h, w, fmt, mapping, linear, size, off = struct.unpack_from("<HHIIIII", b, 8)
    bpp = 4 if fmt == 3 else 8
    data = b[8 + off:8 + off + size] if off else b[0x20:0x20 + size]
    return {"w": w, "h": h, "bpp": bpp, "linear": linear & 0xFF, "data": data}


def tiles(g):
    tb = 8 * g["bpp"]
    out = []
    for t in range(len(g["data"]) // tb):
        raw = g["data"][t * tb:(t + 1) * tb]
        if g["bpp"] == 4:
            px = [v for byte in raw for v in (byte & 15, byte >> 4)]
        else:
            px = list(raw)
        out.append(px)
    return out


def render_tiles(g, pal, cols=32):
    ts = tiles(g)
    if g["linear"] and g["w"] not in (0xFFFF, 0):
        # linear: rows of pixels
        wpx = g["w"] * 8
        px = [p for t in ts for p in t]
        hpx = len(px) // wpx
        im = Image.new("RGB", (wpx, max(hpx, 1)))
        im.putdata([pal[p % len(pal)] for p in px[:wpx * hpx]] or [(0, 0, 0)])
        return im
    if g["w"] not in (0xFFFF, 0) and g["w"] * g["h"] == len(ts):
        cols = g["w"]
    rows = (len(ts) + cols - 1) // cols
    im = Image.new("RGB", (cols * 8, max(rows, 1) * 8))
    for i, t in enumerate(ts):
        tile = Image.new("RGB", (8, 8))
        tile.putdata([pal[p % len(pal)] for p in t])
        im.paste(tile, ((i % cols) * 8, (i // cols) * 8))
    return im


def nscr_render(sd, g, pal, bpp):
    b = block(sd)
    wpx, hpx, _fmt, size = struct.unpack_from("<HHII", b, 8)
    ent = struct.unpack_from(f"<{size // 2}H", b, 0x14)
    ts = tiles(g)
    im = Image.new("RGB", (wpx, hpx))
    cw = wpx // 8
    for i, e in enumerate(ent):
        x, y = (i % cw) * 8, (i // cw) * 8  # this game's 512-wide NSCRs are stored row-major (checked by eye)
        if y >= hpx:
            continue
        t, hf, vf, p = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
        if t >= len(ts):
            continue
        base = p * 16 if bpp == 4 else 0
        tile = Image.new("RGB", (8, 8))
        tile.putdata([pal[(base + v) % len(pal)] for v in ts[t]])
        if hf:
            tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
        if vf:
            tile = tile.transpose(Image.FLIP_TOP_BOTTOM)
        im.paste(tile, (x, y))
    return im


def survey():
    ez = ROOT / "work" / "ez"
    out = ROOT / "work" / "gfx"
    out.mkdir(parents=True, exist_ok=True)
    rows = (ez / "index.tsv").read_text().splitlines()
    magic = {}
    for r in rows:
        f = r.split("\t")
        magic[int(f[0])] = f[6][:8]
    imgs, index, skipped = [], [], []
    last_pal = None
    ids = sorted(magic)
    for i in ids:
        if magic[i] != "5247434e":
            continue
        d = (ez / f"{i:04d}.bin").read_bytes()
        try:
            g = ncgr(d)
        except Exception as e:  # noqa: BLE001
            skipped.append(f"{i} ncgr parse {e}")
            continue
        # palette: next NCLR within 3 entries after, else before
        pal, pi = None, None
        for j in list(range(i + 1, i + 4)) + list(range(i - 1, i - 4, -1)):
            if magic.get(j) == "524c434e":
                pal, _ = nclr((ez / f"{j:04d}.bin").read_bytes())
                pi = j
                break
        if pal is None:
            pal = [(k * 17, k * 17, k * 17) for k in range(16)] * 16
            skipped.append(f"{i} no palette nearby, greyscale")
        scr = next((j for j in range(i + 1, i + 4) if magic.get(j) == "5243534e"), None)
        if scr is not None:
            im = nscr_render((ez / f"{scr:04d}.bin").read_bytes(), g, pal, g["bpp"])
            kind = f"nscr {scr}"
        else:
            im = render_tiles(g, pal)
            kind = "tiles"
        im.save(out / f"{i:04d}.png")
        imgs.append((i, im))
        index.append(f"{i}\t{kind}\tpal {pi}\t{im.size[0]}x{im.size[1]}\tbpp{g['bpp']} linear{g['linear']}")
    (out / "index.tsv").write_text("\n".join(index) + "\n")
    (out / "skipped.txt").write_text("\n".join(skipped) + "\n")
    # contact sheets: each image scaled to fit 256x192 cell, 4 x 4 per sheet, labelled
    # 1:1 pixels so small glyphs stay readable; images bigger than a cell are cropped (full PNG is in work/gfx/)
    per, cw, ch = 6, 512, 268
    for s in range(0, len(imgs), per):
        sheet = Image.new("RGB", (cw * 2, ch * 3), (40, 0, 40))
        dr = ImageDraw.Draw(sheet)
        for k, (i, im) in enumerate(imgs[s:s + per]):
            im2 = im.crop((0, 0, min(im.size[0], cw), min(im.size[1], ch - 12)))
            x, y = (k % 2) * cw, (k // 2) * ch
            sheet.paste(im2, (x, y + 12))
            dr.text((x + 2, y), f"{i:04d} {im.size[0]}x{im.size[1]}", fill=(255, 255, 0))
        sheet.save(out / f"sheet_{s // per:03d}.png")
    print(len(imgs), "images,", len(skipped), "notes; sheets", (len(imgs) + per - 1) // per)


if __name__ == "__main__" and sys.argv[1:] == ["survey"]:
    survey()
