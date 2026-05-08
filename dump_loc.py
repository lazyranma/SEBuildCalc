import argparse
import os
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game-dir",
        default=os.environ.get("SOLAR_EXPANSE_DIR", ""),
        help="Path to Solar Expanse install (or set SOLAR_EXPANSE_DIR env var)",
    )
    return parser.parse_args()


args = parse_args()
if not args.game_dir:
    print(
        "ERROR: --game-dir is required (or set SOLAR_EXPANSE_DIR env var)", flush=True
    )
    exit(1)
GAME_DIR = Path(args.game_dir)
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "loc_names.txt"

loc = {}
suffixes = ("_Description", "_Capabilities", "_Requirements", "_Warning", "_Tooltip")
prefixes = ("build_", "module_", "id_SpacecraftType_", "id_LV_")

# Try different encodings
for enc in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
    try:
        with open(
            GAME_DIR / r"Solar Expanse_Data\StreamingAssets\Languages\en-US.csv",
            encoding=enc,
        ) as f:
            content = f.read()
        if "build_metalmine" in content:
            print(f"# Encoding: {enc}", flush=True)
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                idx = line.find(",")
                if idx == -1:
                    continue
                key = line[:idx]
                val = line[idx + 1 :].strip('"')
                loc[key] = val
            break
    except Exception as e:
        print(f"# {enc} failed: {e}", flush=True)

lines = []
for k in sorted(loc):
    if any(k.startswith(p) for p in prefixes) and not any(
        k.endswith(s) for s in suffixes
    ):
        lines.append(f"{k},{loc[k]}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    out.write("\n".join(lines) + "\n")

print(f"Wrote {len(lines)} entries to {OUTPUT_PATH}")
