""".BBQ1.00 table files (see docs/re/bbq.md): sections and the string table.

Header: 0x00 '.BBQ1.00', 0x08 u32 timestamp, 0x0C u32 1, 0x10 u32 0x18 (descriptor table offset), 0x14 u32 nsec,
then nsec descriptors of 5 u32 at 0x18 + 20*i: (type, index_off, count, data_off, data_size); both offsets are
relative to the descriptor's own start. Type 7 is the string table: count u32 offsets (into the pool) + a pool of
NUL-terminated Shift-JIS strings.

    python -X utf8 tools/bbq.py FILE        # print sections and the first strings"""
import struct
import sys


def sections(d):
    assert d[:8] == b".BBQ1.00", d[:8]
    base, n = struct.unpack_from("<2I", d, 0x10)
    out = []
    for i in range(n):
        at = base + 20 * i
        typ, io, cnt, do, dsz = struct.unpack_from("<5I", d, at)
        out.append({"type": typ, "at": at, "index": at + io, "count": cnt, "data": at + do, "size": dsz})
    return out


def strtab(d):
    """Return (section, list of raw bytes strings) for the type-7 section, or (None, [])."""
    for s in sections(d):
        if s["type"] == 7:
            offs = struct.unpack_from(f"<{s['count']}I", d, s["index"])
            pool = d[s["data"]:s["data"] + s["size"]]
            return s, [pool[o:pool.index(b"\0", o)] for o in offs]
    return None, []


def rebuild(d, strs):
    """Return the file with its type-7 pool replaced by `strs` (raw bytes per string, no NUL), any length.

    The type-7 section is last, so only its index + pool move: the index keeps its offset, the pool is padded to a
    multiple of 4 like the original, and the file's trailing bytes (24 zero bytes) are kept. The descriptor's size
    word is updated; the count must not change (one string per id)."""
    s = next(s for s in sections(d) if s["type"] == 7)
    if len(strs) != s["count"]:
        raise ValueError(f"string count changed: {len(strs)} != {s['count']}")
    pool, offs = b"", []
    for b in strs:
        if b"\0" in b:
            raise ValueError(f"NUL inside a string: {b!r}")
        offs.append(len(pool))
        pool += b + b"\0"
    pool += bytes(-len(pool) % 4)
    index = struct.pack(f"<{len(offs)}I", *offs)
    out = bytearray(d[:s["index"]] + index + pool + d[s["data"] + s["size"]:])
    struct.pack_into("<I", out, s["at"] + 16, len(pool))
    return bytes(out)


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    for s in sections(d):
        print({k: hex(v) for k, v in s.items()})
    _, strs = strtab(d)
    for i, s in enumerate(strs[:20]):
        print(i, s.decode("cp932", "backslashreplace"))
