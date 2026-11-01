"""Read-only ARM9 disassembly with resolved PC-relative literal words.

    python -X utf8 tools/armdump.py 02049a10 02049b1c [--rom build/eog_en.nds]

Addresses are main-RAM addresses, not ITCM addresses. The default is the pinned original ROM.
"""
import argparse
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
import ndspy.rom

import build
import check_rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=lambda x: int(x, 16))
    parser.add_argument("end", type=lambda x: int(x, 16))
    parser.add_argument("--rom", type=Path, default=build.ROM)
    args = parser.parse_args()
    if args.rom == build.ROM:
        check_rom.check()
    data = ndspy.rom.NintendoDSRom(args.rom.read_bytes()).arm9
    base = 0x02000000
    if not base <= args.start < args.end <= base + len(data):
        parser.error("range is outside the ARM9 main section")
    for instruction in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[args.start-base:args.end-base], args.start):
        word = struct.unpack("<I", instruction.bytes)[0]
        literal = ""
        if word & 0x0f7f0000 == 0x051f0000:
            address = instruction.address + 8 + ((word & 4095) if word & 0x800000 else -(word & 4095))
            if base <= address <= base + len(data) - 4:
                literal = f" ; [{address:08x}]={struct.unpack_from('<I', data, address-base)[0]:08x}"
        print(f"{instruction.address:08x} {word:08x} {instruction.mnemonic:8} {instruction.op_str}{literal}")


if __name__ == "__main__":
    main()
