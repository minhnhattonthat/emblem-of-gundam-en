"""release.py: build -> checks -> xdelta patch -> verify -> zip. Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.0] [--force]

Gates, in order: build, tools/check.py, smoke boot, leftover Japanese (script/ + arm9 text bank), qa_gate.py check
on every work/qa/**/manifest.tsv (visual tour + story pass), no unticked line in docs/polish.md, debug menu off
(boot script literal untouched). Then xdelta3 patch, re-applied to the clean original and compared, and
release/EmblemOfGundam_EN_v<version>.zip (patch + README.txt). Refuses to overwrite a version without --force.
"""
import argparse
import hashlib
import re
import shutil
import struct
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
PY = [sys.executable, "-X", "utf8"]
BOOT_LITERAL = 0x02022DAC - 0x02000000  # master flow script id; the debug warp writes 0x1000 here (docs/re/debug.md)
BOOT_SCRIPT = 0x1042


def run(*cmd, **kw):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    if subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw).returncode:
        sys.exit(f"release: failed: {' '.join(str(c) for c in cmd)}")


def skill():
    return Path(subprocess.check_output(PY + [ROOT / "tools/skill.py"], text=True).strip())


def hashes(data):
    return {"size": len(data), "crc32": f"{zlib.crc32(data):08X}", "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest()}


def jp_left(built):
    import batches
    import ndspy.rom
    left = [f"{stem}:{i:04d}" for stem, strs in batches.current().items() if stem != "arm9"
            for i, s in enumerate(strs) if batches.is_text(s)]
    left += [f"a9:{at}" for at, s in batches.current()["arm9"].items() if batches.is_text(s)]
    if left:
        sys.exit(f"release: {len(left)} Japanese strings left in script/: {left[:10]}")
    work = ROOT / "work" / "release"
    work.mkdir(parents=True, exist_ok=True)
    (work / "arm9_en.bin").write_bytes(ndspy.rom.NintendoDSRom(built).arm9)
    import arm9
    import build
    (work / "arm9_jp.bin").write_bytes(ndspy.rom.NintendoDSRom(build.ROM.read_bytes()).arm9)
    out = subprocess.run(PY + [skill() / "scripts/jp_left.py", work / "arm9_en.bin", "--orig", work / "arm9_jp.bin",
                               "--sjis", "--range", f"{arm9.LO:x}-78000"], cwd=ROOT, capture_output=True, text=True)
    print(out.stdout.strip())
    m = re.search(r"(\d+) Japanese runs", out.stdout)
    if out.returncode or not m or m.group(1) != "0":
        sys.exit("release: jp_left found untouched Japanese in the arm9 text bank (or failed)")


def gates():
    qa = skill() / "scripts/qa_gate.py"
    manifests = sorted((ROOT / "work/qa").rglob("manifest.tsv"))
    if not manifests:
        sys.exit("release: no work/qa/**/manifest.tsv")
    for m in manifests:
        run(*PY, qa, "check", m.relative_to(ROOT), (m.parent / "verdicts").relative_to(ROOT))
    open_ = [ln for ln in (ROOT / "docs/polish.md").read_text(encoding="utf-8").splitlines()
             if ln.startswith("- [ ]")]
    if open_:
        sys.exit(f"release: docs/polish.md has {len(open_)} unticked lines, first: {open_[0]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    a = ap.parse_args()
    import build
    rel = ROOT / "release"
    name = f"EmblemOfGundam_EN_v{a.version}"
    patch, zpath = rel / f"{name}.xdelta", rel / f"{name}.zip"
    if not a.force and (patch.exists() or zpath.exists()):
        sys.exit(f"release: {zpath.name} exists; pass --force to overwrite")
    if not shutil.which("xdelta3"):
        sys.exit("release: xdelta3 not on PATH")

    run(*PY, "tools/build.py")
    run(*PY, "tools/check.py")
    run(*PY, skill() / "scripts/emu.py", build.OUT, "--out", "work/qa/smoke", "--route", "tools/routes/boot.txt",
        "--smoke")
    built, orig = build.OUT.read_bytes(), build.ROM.read_bytes()
    jp_left(built)
    gates()
    import ndspy.rom
    lit = struct.unpack_from("<I", ndspy.rom.NintendoDSRom(built).arm9, BOOT_LITERAL)[0]
    if lit != BOOT_SCRIPT:
        sys.exit(f"release: boot script literal is {lit:#x}, not {BOOT_SCRIPT:#x}: debug menu left on")

    rel.mkdir(exist_ok=True)
    run("xdelta3", "-e", "-9", "-f", "-s", build.ROM, build.OUT, patch)
    check = ROOT / "work/release/reapplied.nds"
    run("xdelta3", "-d", "-f", "-s", build.ROM, patch, check)
    if check.read_bytes() != built:
        sys.exit("release: re-applied patch does not reproduce build/eog_en.nds")
    h0, h1 = hashes(orig), hashes(built)
    readme = (ROOT / "docs/release-readme.txt").read_text(encoding="utf-8").format(
        version=a.version, patch=patch.name, orig=h0, built=h1)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", readme)
    print(f"release: {zpath} ok; patched CRC32 {h1['crc32']} SHA-1 {h1['sha1']}")


if __name__ == "__main__":
    main()
