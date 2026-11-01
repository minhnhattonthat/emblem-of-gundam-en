"""gfxgrid.py: an NCGR+NCLR+NSCR screen at zoom with an 8 px tile grid and tile coordinates, to read label rects.

    python -X utf8 tools/gfxgrid.py 375 [--crop x,y,w,h] [--zoom 3] [--out work/gfx/grid_0375.png]
Ids are EZ entries (work/ez/NNNN.bin): NCGR = id, NCLR = id+1, NSCR = id+2."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import nitro2d  # noqa: E402

a = sys.argv[1:]
cid = int(a[0])
opt = lambda k, d: a[a.index(k) + 1] if k in a else d  # noqa: E731
ez = ROOT.parent / "work" / "ez"
rd = lambda i: (ez / f"{i:04d}.bin").read_bytes()  # noqa: E731
g = nitro2d.ncgr(rd(cid))
pal, bpp = nitro2d.nclr(rd(cid + 1))
im = nitro2d.nscr_render(rd(cid + 2), g, pal, g["bpp"])
x, y, w, h = map(int, opt("--crop", f"0,0,{im.width},{im.height}").split(","))
z = int(opt("--zoom", "3"))
im = im.crop((x, y, x + w, y + h)).resize((w * z, h * z), Image.NEAREST)
d = ImageDraw.Draw(im)
for tx in range(0, w, 8):
    d.line([(tx * z, 0), (tx * z, h * z)], fill=(255, 0, 255) if (x + tx) % 32 == 0 else (90, 0, 90))
for ty in range(0, h, 8):
    d.line([(0, ty * z), (w * z, ty * z)], fill=(255, 0, 255) if (y + ty) % 32 == 0 else (90, 0, 90))
for tx in range(0, w, 32):
    for ty in range(0, h, 32):
        d.text((tx * z + 1, ty * z + 1), f"{x + tx},{y + ty}", fill=(255, 255, 0))
out = opt("--out", str(ROOT.parent / "work" / "gfx" / f"grid_{cid:04d}.png"))
im.save(out)
print(out)
