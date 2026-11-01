"""ncer.py: render the OBJ cells of an NCER over its NCGR/NCLR (EZ ids NCGR, NCGR+1 = NCLR, NCGR+3 = NCER).

    python -X utf8 tools/ncer.py 344 [--zoom 3]   # work/ez -> work/gfx/cells_0344.png (cell number above each)"""
import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw

import nitro2d

ROOT = Path(__file__).resolve().parents[1]
SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
         (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
         (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def cells(d):
    """[[(x, y, w, h, tile, pal, hflip, vflip), ...] per cell] (tile in 4bpp/8bpp tile units, 1D mapping)."""
    b = d[0x10:]
    n, kind, off, mapping = struct.unpack_from("<HHII", b, 8)
    base = 8 + off
    esz = 16 if kind == 1 else 8
    oam0 = base + n * esz
    out = []
    for i in range(n):
        cnt, _attr, o = struct.unpack_from("<HHI", b, base + i * esz)
        objs = []
        for k in range(cnt):
            a0, a1, a2 = struct.unpack_from("<HHH", b, oam0 + o + 6 * k)
            w, h = SIZES[(a0 >> 14, a1 >> 14)]
            y = a0 & 0xFF
            y -= 256 if y >= 128 else 0
            x = a1 & 0x1FF
            x -= 512 if x >= 256 else 0
            objs.append((x, y, w, h, (a2 & 0x3FF) << (mapping & 7), a2 >> 12, a1 >> 12 & 1, a1 >> 13 & 1))
        out.append(objs)
    return out


def render(cid, zoom=3):
    ez = ROOT / "work" / "ez"
    g = nitro2d.ncgr((ez / f"{cid:04d}.bin").read_bytes())
    pal, _ = nitro2d.nclr((ez / f"{cid + 1:04d}.bin").read_bytes())
    ts = nitro2d.tiles(g)
    ims = []
    for objs in cells((ez / f"{cid + 3:04d}.bin").read_bytes()):
        if not objs:
            ims.append(Image.new("RGB", (8, 8), (40, 0, 40)))
            continue
        x0, y0 = min(o[0] for o in objs), min(o[1] for o in objs)
        x1, y1 = max(o[0] + o[2] for o in objs), max(o[1] + o[3] for o in objs)
        im = Image.new("RGB", (x1 - x0, y1 - y0), (40, 0, 40))
        for x, y, w, h, t, p, hf, vf in objs:
            o = Image.new("RGB", (w, h))
            base = p * 16 if g["bpp"] == 4 else 0
            for k in range(w // 8 * h // 8):
                if t + k >= len(ts):
                    break
                tile = Image.new("RGB", (8, 8))
                tile.putdata([pal[(base + v) % len(pal)] if v else (40, 0, 40) for v in ts[t + k]])
                o.paste(tile, (k % (w // 8) * 8, k // (w // 8) * 8))
            if hf:
                o = o.transpose(Image.FLIP_LEFT_RIGHT)
            if vf:
                o = o.transpose(Image.FLIP_TOP_BOTTOM)
            im.paste(o, (x - x0, y - y0))
        ims.append(im)
    cols, cw = 8, max(i.width for i in ims) * zoom + 8
    ch = max(i.height for i in ims) * zoom + 14
    sheet = Image.new("RGB", (cols * cw, (len(ims) + cols - 1) // cols * ch), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    for n, im in enumerate(ims):
        x, y = n % cols * cw, n // cols * ch
        d.text((x, y), str(n), fill=(255, 255, 0))
        sheet.paste(im.resize((im.width * zoom, im.height * zoom), Image.NEAREST), (x, y + 12))
    out = ROOT / "work" / "gfx" / f"cells_{cid:04d}.png"
    sheet.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cid", type=int, nargs="+")
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    for c in a.cid:
        print(render(c, a.zoom))
