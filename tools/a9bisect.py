"""a9bisect.py: find which arm9 string edits break a screen -- builds ROMs that each apply one group of the changed
arm9 strings (BBQ English, the rest of arm9 Japanese), warps each to a scene and reports whether a probe region of
the final shot has text ink.

    python -X utf8 tools/a9bisect.py --scene map --region 4,146,196,14 [--groups 8] [--only HEX,HEX..]

Region is x,y,w,h in native 256x384 pixels; a group "has ink" when >= --min pixels are brighter than --thr. Narrow
down by rerunning with --only set to the guilty group's addresses."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import build  # noqa: E402
import insert  # noqa: E402


def ink(png, region, thr):
    from PIL import Image
    im = Image.open(png).convert("L")
    x, y, w, h = region
    return sum(1 for i in range(x, x + w) for j in range(y, y + h) if im.getpixel((i, j)) > thr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--groups", type=int, default=8)
    ap.add_argument("--only", default="")
    ap.add_argument("--thr", type=int, default=200)
    ap.add_argument("--min", type=int, default=20)
    ap.add_argument("--frames", type=int, default=900)
    a = ap.parse_args()
    region = tuple(int(v) for v in a.region.split(","))
    import ndspy.rom
    rom = ndspy.rom.NintendoDSRom(build.ROM.read_bytes())
    old = dict(arm9.strings(rom.arm9))
    edits = {off: t for off, t in insert.arm9_texts().items() if old.get(off) != t}
    if a.only:
        keep = {int(h, 16) - arm9.BASE for h in a.only.split(",")}
        edits = {k: v for k, v in edits.items() if k in keep}
    offs = sorted(edits)
    n = max(1, -(-len(offs) // a.groups))
    groups = [offs[i:i + n] for i in range(0, len(offs), n)]
    ez, _ = build.script()
    work = ROOT / "work" / "bisect"
    work.mkdir(parents=True, exist_ok=True)
    for k, g in enumerate(groups):
        out = work / f"g{k}.nds"
        out.write_bytes(build.build(ez, insert.arm9_edit(rom.arm9, {o: edits[o] for o in g})))
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "debug" / "warp_all.py"), str(out),
                        "--only", f"^{a.scene}$", "--frames", str(a.frames), "--out", str(work / f"g{k}")],
                       check=False, capture_output=True)
        px = ink(work / f"g{k}" / a.scene / "final.png", region, a.thr)
        addrs = ",".join(f"{arm9.BASE + o:08x}" for o in g)
        print(f"g{k} ink={px:4d} {'OK ' if px >= a.min else 'BAD'} {addrs}", flush=True)


if __name__ == "__main__":
    main()
