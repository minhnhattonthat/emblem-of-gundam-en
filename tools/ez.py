"""ez.py: the game's EZ_TBL.BIN / EZ_DAT.BIN archive (see docs/re/archive.md).

EZ_TBL: 0x94-byte header, then 12-byte entries (key, data offset in EZ_DAT, (flags << 24) | unpacked size).
Flag 0x10 = LZ10-compressed (the stored block is a standard 0x10 LZ header + stream). Size 0 = directory marker.

    python -X utf8 tools/ez.py unpack     # -> work/ez/NNNN.bin (decompressed), work/ez/index.tsv"""
import struct
import sys
from pathlib import Path

import ndspy.lz10

ROOT = Path(__file__).resolve().parents[1]
HDR = 0x94


def entries(tbl):
    n = (len(tbl) - HDR) // 12
    return [struct.unpack_from("<3I", tbl, HDR + 12 * i) for i in range(n)]


def blocks(tbl, dat):
    """Yield (index, key, offset, stored_len, flags, unpacked_size, raw stored bytes)."""
    ents = entries(tbl)
    for i, (key, off, sz) in enumerate(ents):
        end = ents[i + 1][1] if i + 1 < len(ents) else len(dat)
        yield i, key, off, end - off, sz >> 24, sz & 0xFFFFFF, dat[off:end]


def repack(tbl, dat, new):
    """Rebuild (EZ_TBL, EZ_DAT) with entries {index: unpacked bytes} replaced; untouched blocks are copied as stored
    (padding included), so repack(tbl, dat, {}) is byte-identical. A new block keeps the old flags (LZ10 or raw)
    and its length mod 4, so every later offset keeps its alignment. The DAT header word 0x0C (offset of the name
    table, which is the last entry's offset) is moved with it.

    The size word is the *unpacked* length rounded **up to 16** -- every one of the original 4,146 entries has it that
    way, and the game relies on it: the whole-file loader (0x0203BD34) mallocs that many bytes and the decompressor
    writes in 16-byte units (docs/re/archive.md). Writing the exact length instead hangs the game at the developer
    menu, so pad the data itself to 16 as well (tools/insert.py does)."""
    tbl, out, delta = bytearray(tbl), bytearray(dat[:0x10]), 0
    for i, key, off, slen, fl, usz, raw in blocks(tbl, dat):
        struct.pack_into("<I", tbl, HDR + 12 * i + 4, off + delta)
        if i in new:
            if usz == 0:
                raise ValueError(f"entry {i} is a directory marker")
            data = new[i]
            comp = ndspy.lz10.compress(data) if fl == 0x10 else data
            raw = comp + bytes((slen - len(comp)) % 4)
            struct.pack_into("<I", tbl, HDR + 12 * i + 8, (fl << 24) | (len(data) + -len(data) % 16))
            delta += len(raw) - slen
        out += raw
    struct.pack_into("<I", out, 0x0C, struct.unpack_from("<I", dat, 0x0C)[0] + delta)
    return bytes(tbl), bytes(out)


if __name__ == "__main__" and sys.argv[1:] == ["unpack"]:
    fs = ROOT / "work" / "fs"
    tbl, dat = (fs / "EZ_TBL.BIN").read_bytes(), (fs / "EZ_DAT.BIN").read_bytes()
    out = ROOT / "work" / "ez"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, key, off, slen, fl, usz, raw in blocks(tbl, dat):
        if usz == 0:
            rows.append(f"{i}\t{key:#x}\t{off:#x}\t{slen}\t{fl:#x}\t0\tdir")
            continue
        data = ndspy.lz10.decompress(raw) if fl == 0x10 else raw[:usz]
        (out / f"{i:04d}.bin").write_bytes(data)
        rows.append(f"{i}\t{key:#x}\t{off:#x}\t{slen}\t{fl:#x}\t{len(data)}\t{data[:16].hex()}")
    (out / "index.tsv").write_text("\n".join(rows) + "\n")
    print(len(rows), "entries")
