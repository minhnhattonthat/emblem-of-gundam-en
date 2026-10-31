"""nftr.py: read an NFTR (RTFN) font: FINF metrics, CGLP glyph bitmaps, CWDH widths, CMAP code -> glyph.

    python -X utf8 tools/nftr.py work/ez/0336.bin [--sheet out.png]"""
import struct
import sys


def parse(d):
    assert d[:4] == b"RTFN", d[:4]
    hsize = struct.unpack_from("<H", d, 0xC)[0]
    f = {"cmap": {}, "widths": {}}
    off = hsize
    while off + 8 <= len(d):
        magic, size = d[off:off + 4], struct.unpack_from("<I", d, off + 4)[0]
        if size == 0:
            break
        b = off + 8
        if magic == b"FNIF":
            f["finf"] = struct.unpack_from("<BhB H B B B B", d, b)  # type, linefeed, alt, defwidth.., encoding
            f["encoding"] = d[b + 7]
        elif magic == b"PLGC":
            cw, ch, gsize, bl, mw, bpp, rot = struct.unpack_from("<BBHBBBB", d, b)
            f.update(cell_w=cw, cell_h=ch, glyph_size=gsize, bpp=bpp, glyph_off=b + 8)
            f["nglyphs"] = (size - 16) // gsize
        elif magic == b"HDWC":
            first, last = struct.unpack_from("<HH", d, b)
            for i in range(first, last + 1):
                f["widths"][i] = tuple(d[b + 8 + 3 * (i - first):b + 11 + 3 * (i - first)])
        elif magic == b"PAMC":
            lo, hi, typ = struct.unpack_from("<HHH", d, b)
            p = b + 12
            if typ == 0:
                g0 = struct.unpack_from("<H", d, p)[0]
                for c in range(lo, hi + 1):
                    f["cmap"][c] = g0 + c - lo
            elif typ == 1:
                for c in range(lo, hi + 1):
                    g = struct.unpack_from("<H", d, p + 2 * (c - lo))[0]
                    if g != 0xFFFF:
                        f["cmap"][c] = g
            else:
                n = struct.unpack_from("<H", d, p)[0]
                for k in range(n):
                    c, g = struct.unpack_from("<HH", d, p + 2 + 4 * k)
                    f["cmap"][c] = g
        off += size
    return f


def glyph(f, d, g):
    """Return rows of pixel values for glyph index g."""
    raw = d[f["glyph_off"] + g * f["glyph_size"]:][:f["glyph_size"]]
    bits = int.from_bytes(raw, "big")
    n = len(raw) * 8
    bpp, w = f["bpp"], f["cell_w"]
    px = [(bits >> (n - bpp * (i + 1))) & ((1 << bpp) - 1) for i in range(w * f["cell_h"])]
    return [px[r * w:(r + 1) * w] for r in range(f["cell_h"])]


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    f = parse(d)
    codes = sorted(f["cmap"])
    print({k: f[k] for k in ("cell_w", "cell_h", "bpp", "nglyphs", "encoding")}, "codes", len(codes),
          hex(codes[0]), hex(codes[-1]))
    print("sample", [hex(c) for c in codes[:10]], [hex(c) for c in codes[200:205]])
