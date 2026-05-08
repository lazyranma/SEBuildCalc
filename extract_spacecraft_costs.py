import argparse
import json
import os
import struct
from pathlib import Path

import UnityPy


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
data_dir = str(GAME_DIR / "Solar Expanse_Data")
env = UnityPy.load(os.path.join(data_dir, "sharedassets0.assets"))
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "spacecraft_costs.json"

# Spacecraft to extract (from earlier scan)
SPACECRAFT_PIDS = {
    7043,
    7044,
    7045,
    7046,
    7047,
    7048,
    7049,
    7050,
    7051,
    7052,
    7053,
    7054,
    7055,
    7056,  # Spacecraft1-14 named ships
    7040,
    7041,
    7042,  # sail variants
    7038,  # InterstellarShip
    7037,  # Atlas (asteroid puller)
}


def read_str_at(raw, pos):
    if pos + 4 > len(raw):
        return None, pos
    slen = struct.unpack_from("<I", raw, pos)[0]
    if slen == 0 or slen > 300:
        return None, pos
    end = pos + 4 + slen
    if end > len(raw):
        return None, pos
    try:
        s = raw[pos + 4 : end].decode("utf-8")
        pad = (4 - slen % 4) % 4
        return s, end + pad
    except:
        return None, pos


results = {}

for obj in env.objects:
    if obj.type.name != "MonoBehaviour" or obj.path_id not in SPACECRAFT_PIDS:
        continue
    try:
        raw = obj.get_raw_data()
        if not raw:
            continue

        # Read ship ID from pos=28
        sc_id, _ = read_str_at(raw, 28)
        if not sc_id:
            continue

        # Scan for pattern: id_resource_X -> "price" -> numeric_string
        resources = {}
        build_time = None
        text_key = None
        i = 0
        while i < len(raw) - 4:
            s, npos = read_str_at(raw, i)
            if s and s.startswith("id_resource_") and len(s) > 12:
                res_key = s[len("id_resource_") :]
                # Look for 'price' string nearby (within 80 bytes)
                j = npos
                while j < npos + 80 and j < len(raw):
                    s2, npos2 = read_str_at(raw, j)
                    if s2 == "price":
                        # Amount string is within ~50 bytes after 'price' (with an Odin node header in between)
                        k = npos2
                        while k < npos2 + 50 and k < len(raw):
                            s3, npos3 = read_str_at(raw, k)
                            if s3:
                                try:
                                    amt = float(s3)
                                    if amt > 0:
                                        if (
                                            res_key not in resources
                                            or amt > resources[res_key]
                                        ):
                                            resources[res_key] = amt
                                    break
                                except ValueError:
                                    pass
                            k += 4
                        break
                    j += 4
                i = npos
            elif s == "buildTimeBase":
                # Scan for the numeric value string within next ~50 bytes
                k = npos
                while k < npos + 50 and k < len(raw):
                    s2, _ = read_str_at(raw, k)
                    if s2:
                        try:
                            build_time = float(s2)
                            break
                        except ValueError:
                            pass
                    k += 4
                i = npos
            elif s == "text":
                # text field holds the localization key (e.g. 'spacecraft_nuke_mid')
                k = npos
                while k < npos + 100 and k < len(raw):
                    s2, _ = read_str_at(raw, k)
                    if (
                        s2
                        and s2.startswith("spacecraft_")
                        and not s2.endswith("_Description")
                    ):
                        text_key = s2
                        break
                    k += 4
                i = npos
            else:
                i += 4

        results[sc_id] = {
            "display_name": None,  # filled in below from localization
            "text_key": text_key,
            "build_time_days": build_time,
            "resources": resources,
        }
        print(f"  {sc_id} [{text_key}]: {resources}  time={build_time}")
    except Exception as e:
        import traceback

        print(f"ERROR pid={obj.path_id}: {e}")
        traceback.print_exc()

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} spacecraft to {OUTPUT_PATH}")

# Add display names from localization
loc = {}
with open(
    GAME_DIR / r"Solar Expanse_Data\StreamingAssets\Languages\en-US.csv",
    encoding="utf-8-sig",
) as f:
    for line in f:
        line = line.strip()
        if not line or "," not in line:
            continue
        k, v = line.split(",", 1)
        loc[k] = v.strip('"')

# For InterstellarShip use its direct key; for others use text_key
for sc_id, entry in results.items():
    key = entry.get("text_key")
    if sc_id == "id_Spacecraft_InterstellarShip":
        key = "id_Spacecraft_InterstellarShip"
    if key and key in loc:
        entry["display_name"] = loc[key]
    else:
        # Fallback: strip prefix numbers from internal name
        name = sc_id
        for pfx in (
            "Spacecraft1",
            "Spacecraft2",
            "Spacecraft3",
            "Spacecraft4",
            "Spacecraft5",
            "Spacecraft6",
            "Spacecraft7",
            "Spacecraft8",
            "Spacecraft9",
            "Spacecraft10",
            "Spacecraft11",
            "Spacecraft12",
            "Spacecraft13",
            "Spacecraft14",
        ):
            if sc_id.startswith(pfx):
                name = sc_id[len(pfx) :]
        entry["display_name"] = name

# Print final mapping
print("\nFinal spacecraft:")
for sc_id, entry in sorted(
    results.items(), key=lambda x: x[1].get("display_name") or ""
):
    print(
        f"  {entry['display_name']:30s} | {entry['resources']}  time={entry['build_time_days']}"
    )

# Overwrite with display names included
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
