"""textband.py: measure one line of drawn text in a shot -- its ink extent, the pitch, and how many glyphs fit.

The width gate reads budgets off shots instead of the engine's numbers (references/pipeline.md): the marker build
fills every text line with `TTT:IIII|0123456789...`, the box clips the ruler, and this prints where the ink starts
and stops. A shot is the emulator's 256x384 (both screens stacked).

    python -X utf8 tools/textband.py SHOT Y0 Y1 [--x0 X] [--x1 X] [--thr 160] [--all]

`--all` finds every text line in the image: rows with ink, grouped, each printed with its span. Without a band it
does the same over the whole shot.
"""
import argparse
import sys

from PIL import Image


def rows(px, lo, hi, x0, x1, thr):
    """(y, ink) per row."""
    out = []
    for y in range(lo, hi):
        xs = [x for x in range(x0, x1) if px[x, y] > thr]
        if xs:
            out.append((y, min(xs), max(xs), len(xs)))
    return out


def lines(px, lo, hi, x0, x1, thr, min_ink=4):
    """[(y0, y1, x_min, x_max)] for each group of consecutive ink rows (a text line)."""
    got = rows(px, lo, hi, x0, x1, thr)
    out = []
    for y, a, b, n in got:
        if n < min_ink:
            continue
        if out and y - out[-1][1] <= 2:
            o = out[-1]
            out[-1] = (o[0], y, min(o[2], a), max(o[3], b))
        else:
            out.append((y, y, a, b))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shot")
    ap.add_argument("band", nargs="*", type=int, metavar="Y0 Y1")
    ap.add_argument("--x0", type=int, default=0)
    ap.add_argument("--x1", type=int, default=256)
    ap.add_argument("--thr", type=int, default=160)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    im = Image.open(a.shot).convert("L")
    px = im.load()
    lo, hi = (a.band[0], a.band[1]) if len(a.band) == 2 else (0, im.size[1])
    for y0, y1, xmin, xmax in lines(px, lo, hi, a.x0, a.x1, a.thr):
        print(f"y {y0:3d}-{y1:3d}  x {xmin:3d}-{xmax:3d}  span {xmax - xmin + 1:3d} px")
    if len(a.band) == 2 and not a.all:
        ys = [y for y in range(lo, hi) if any(px[x, y] > a.thr for x in range(a.x0, a.x1))]
        if ys:
            xs = [x for x in range(a.x0, a.x1) if any(px[x, y] > a.thr for y in range(lo, hi))]
            print(f"band {lo}-{hi}: x {min(xs)}-{max(xs)} span {max(xs) - min(xs) + 1} px")


if __name__ == "__main__":
    sys.exit(main())
