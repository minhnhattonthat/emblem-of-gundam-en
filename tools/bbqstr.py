"""Print every string of a BBQ file's string table with its index.

    python -X utf8 tools/bbqstr.py work/ez/0000.bin [FROM [TO]]"""
import sys

from bbq import strtab

if __name__ == "__main__":
    _, strs = strtab(open(sys.argv[1], "rb").read())
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else len(strs)
    for i in range(lo, min(hi, len(strs))):
        print(i, strs[i].decode("cp932", "backslashreplace").replace("\n", "\\n"))
