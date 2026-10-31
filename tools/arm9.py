"""arm9.py: the ARM9's own Shift-JIS strings and their pointers (see docs/re/text.md).

The strings live NUL-terminated in the main code section's tail, file 0x72170-0x77140 (RAM 0x02072170 upward):
shop, team-building, save/load, options, turn prompts and the leftover debug menu. Every one is reached from a
4-byte literal pointer (ARM's literal pools; a pointer table for a few menus), stored in arm9 itself, so a string can
be extracted by scanning the region and told apart from the binary data around it by requiring a pointer to its start.

    python -X utf8 tools/arm9.py work/fs/arm9.bin    # print every string with its pointers"""
import struct
import sys
import unicodedata

BASE = 0x02000000
LO, HI = 0x72170, 0x77140  # file offsets of the string region (main section tail)


def valid(text):
    """True if text is something the game can draw: no controls but \\n, no private-use or unassigned codepoints."""
    for c in text:
        o = ord(c)
        if c == "\n":
            continue
        if o < 0x20 or o == 0x7F or 0xE000 <= o <= 0xF8FF:
            return False
        if unicodedata.category(c) in ("Cc", "Cs", "Cn", "Co"):
            return False
    return True


def decode(b):
    """cp932 bytes -> str, or None when they aren't SJIS text."""
    try:
        s = b.decode("cp932")
    except UnicodeDecodeError:
        return None
    return s if valid(s) else None


def runners(d, lo=LO, hi=HI):
    """Yield (offset, end, text or None) for every NUL-terminated run in the region."""
    off = lo
    while off < min(hi, len(d)):
        if d[off] == 0:
            off += 1
            continue
        end = d.find(b"\0", off)
        if end < 0:
            return
        yield off, end, decode(d[off:end])
        off = end + 1


def pointers(d, off):
    """File offsets of the 4-aligned words holding the RAM address BASE + off (empty if unreferenced)."""
    want = struct.pack("<I", BASE + off)
    out, at = [], d.find(want, 0, len(d) - 3)
    while at >= 0:
        if at % 4 == 0:
            out.append(at)
        at = d.find(want, at + 1)
    return out


def strings(d):
    """[(file offset, text)] for every string a pointer reaches, in address order. Runs below two bytes are
    binary data whose address a table happens to hold, not text."""
    return [(off, t) for off, end, t in runners(d) if t and end - off >= 2 and pointers(d, off)]


def replace(d, edits):
    """Return arm9 with {file offset: text} replaced in place. A replacement must not be longer than the original
    plus its NUL: growing an arm9 string needs the relocation the phase 5 marker build plans (ITCM tail)."""
    out = bytearray(d)
    byoff = {off: t for off, t in strings(d)}
    for off, text in edits.items():
        if off not in byoff:
            raise KeyError(f"{off:#x} is not a string start")
        old = d.find(b"\0", off) - off
        new = text.encode("cp932")
        if len(new) > old:
            raise ValueError(f"{BASE + off:#x}: {len(new)} bytes do not fit in {old}: {text!r}")
        out[off:off + old + 1] = new + bytes(old + 1 - len(new))
    return bytes(out)


if __name__ == "__main__":
    for off, text in strings(open(sys.argv[1], "rb").read()):
        print(f"{BASE + off:#09x} {[hex(p) for p in pointers(open(sys.argv[1], 'rb').read(), off)]} {text}")
