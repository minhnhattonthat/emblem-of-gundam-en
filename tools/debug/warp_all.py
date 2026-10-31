"""Warp to every scene in tools/debug/scenes.lua from a cold boot; keep a proof shot and a savestate of each.

    python -X utf8 tools/debug/warp_all.py [ROM] [--only REGEX] [--jobs 4] [--frames 300] [--out work/qa/warps]

Per scene: work/qa/warps/<scene>/final.png (the proof), work/states/<scene>.dst, then a contact sheet of all
finals per group (work/qa/warps/sheet_<group>.png) and summary.tsv. A scene passes when warp.lua logged
WARP_DONE and the final frame is not a flat colour. Exit 1 if any scene failed. Regenerate after any code,
font or graphics change (states keep the old code and VRAM)."""
import argparse
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

sys.path.insert(0, os.path.join(SKILL, "scripts"))
import sheet  # noqa: E402

DEBUG = os.path.join(ROOT, "tools", "debug")


def scene_names():
    """Scene names in scenes.lua: the stNN_<phase> loop plus every `SCENES.name =` line."""
    src = open(os.path.join(DEBUG, "scenes.lua"), encoding="utf-8").read()
    names = [f"st{k:02d}_{ph}" for k in range(68) if k != 6 for ph in ("open", "battle", "end", "prep")]
    assert "return k ~= 6 end" in src and '"st%02d_prep"' in src, "scenes.lua stage loops changed: update scene_names()"
    names += re.findall(r"^SCENES\.(\w+) =", src, re.M)
    return names


def group(name):
    return name.split("_")[1] if re.match(r"st\d\d_", name) else "misc"


def run(rom, name, out, frames):
    d = os.path.join(out, name)
    state = os.path.join(ROOT, "work", "states", name + ".dst")
    os.makedirs(os.path.dirname(state), exist_ok=True)
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), rom, "--out", d,
           "--script", os.path.join(DEBUG, "scenes.lua"), "--script", os.path.join(DEBUG, "warp.lua"),
           "--var", f"SCENE='{name}'", "--frames", str(frames), "--state-out", state, "--timeout", "300"]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    log = os.path.join(d, "log.txt")
    text = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
    m = re.search(r"WARP_DONE f(\d+) script (\w+)", text)
    final = os.path.join(d, "final.png")
    blank = not os.path.exists(final) or sheet.is_blank(sheet.read_png(final))
    if os.path.exists(final):  # named copy, so sheet tiles are labelled with the scene
        os.makedirs(os.path.join(out, "shots"), exist_ok=True)
        shutil.copyfile(final, os.path.join(out, "shots", name + ".png"))
    ok = r.returncode == 0 and m is not None and not blank
    why = "" if ok else (f"exit {r.returncode}" if r.returncode else "no WARP_DONE" if not m else "flat final frame")
    return name, ok, m.group(1) if m else "", m.group(2) if m else "", why


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=os.path.join(ROOT, "rom", "Emblem of Gundam (Japan).nds"))
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "warps"))
    a = ap.parse_args()
    names = [n for n in scene_names() if re.search(a.only, n)]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda n: run(os.path.abspath(a.rom), n, a.out, a.frames), names))
    with open(os.path.join(a.out, "summary.tsv"), "w", encoding="utf-8") as f:
        f.write("scene\tok\twarp_frame\tscript\tproblem\n")
        for r in res:
            f.write("\t".join([r[0], "ok" if r[1] else "FAIL", *r[2:]]) + "\n")
    for g in sorted({group(n) for n in names}):
        shots = [os.path.join(a.out, "shots", n + ".png") for n in names if group(n) == g]
        shots = [s for s in shots if os.path.exists(s)]
        if shots:
            sheet.make(shots, out=os.path.join(a.out, f"sheet_{g}.png"), cols=6, limit=24)
    bad = [r for r in res if not r[1]]
    print(f"{len(res) - len(bad)}/{len(res)} scenes ok; summary {os.path.join(a.out, 'summary.tsv')}")
    for r in bad:
        print("FAIL", r[0], r[4])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
