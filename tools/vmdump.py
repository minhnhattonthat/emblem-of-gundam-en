"""Dump a BBQ script's type-6 bytecode as a word stream (docs/re/script.md).

    python -X utf8 tools/vmdump.py work/ez/0083.bin [--find HEX]..

Words are shown as hex, a 0x0E word joined to the next one as #N. Opcode meaning is a guess, not decoded: 0x0E
seems to start each operand; `2e 00 02 00, 0x44, 1` reads as "script group 1 index 0x44" (= file id 0x1044)."""
import struct
import sys

from bbq import sections


def code(d):
    s = [x for x in sections(d) if x["type"] == 6][0]
    b = d[s["data"]:s["data"] + s["size"]]
    return struct.unpack(f"<{len(b) // 4}I", b)


def tokens(w):
    i = 0
    while i < len(w):
        if w[i] == 0x0E and i + 1 < len(w):
            yield i, f"#{w[i + 1]:x}"
            i += 2
        else:
            yield i, f"{w[i]:x}"
            i += 1


if __name__ == "__main__":
    w = code(open(sys.argv[1], "rb").read())
    line, start = [], 0
    for i, t in tokens(w):
        if not line:
            start = i
        line.append(t)
        if not t.startswith("#") and (int(t, 16) & 0xFF00) or len(line) >= 16:
            print(f"{start * 4:05x}: " + " ".join(line))
            line = []
    if line:
        print(f"{start * 4:05x}: " + " ".join(line))
