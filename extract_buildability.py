"""
Extract isObsolete from FacilityBaseDescriptor Odin binary.

KEY INSIGHT: Odin only serializes non-default values. For most facilities:
- isObsolete=False (default) → written as 0 (simple field before facilityItemClass)

Strategy:
1. Find facilityItemClass label → isObsolete is 4 bytes before the label's node_type
2. Since Odin skips defaults, most fields are absent → we can't walk fields.
"""

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
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "extracted_buildability.json"

# Field names for label matching
FIELD_LABELS = {
    "facilityItemClass",
    "byproducts",
    "resourcesToMine",
    "canBuildParameter",
    "habitabilityParametersEfficiencyCurveMultipliers",
    "habitabilityParameterEfficiencyMultiplierCurveOld",
    "workloadEfficiencyCurve",
    "specialAbilityFacilityNew",
    "energyProductionData",
    "energyStorageData2",
    "habitabilityParametersBonus",
    "prefabOnOrbit3dView",
    "custom3DViewObjectInfoPrefab",
    "scTypeInterstellarShip",
    "scTypeAsteroidPullingShip",
    "facilityDescriptorSegmentConstruction",
    "refinerData",
}


def find_labels(raw, start=0):
    """Find all Odin field labels in raw data. Returns {name: name_len_position}."""
    labels = {}
    for j in range(start, len(raw) - 8, 4):
        sl = struct.unpack_from("<I", raw, j)[0]
        if 3 < sl < 128 and j + 4 + sl <= len(raw):
            try:
                s = raw[j + 4 : j + 4 + sl].decode("ascii")
                if s in FIELD_LABELS:
                    labels[s] = j
            except:
                pass
    return labels


def extract_facility(raw):
    """
    Extract facility data from raw Odin binary.
    Returns dict with isObsolete, or None.
    """
    # Find facilityItemClass label
    labels = find_labels(raw)
    if "facilityItemClass" not in labels:
        return None

    fic_nl_pos = labels["facilityItemClass"]

    # The 3 simple fields before facilityItemClass:
    # [value:4][value:4][value:4] [node_type:4][name_len:4]["facilityItemClass":17][pad:3]
    # In Odin, the label format for the first complex field seems to have a node_type
    # But looking at actual data, the format is:
    # [...simple_fields...] [X:4][name_len:4][name:N][pad] [value...]
    # where X is 5-15 (node_type for named fields)
    #
    # The 3 simple fields before the label are at: fic_nl_pos - 12
    #
    # Actually from build_metalmine: label has [node_type(11):4][name_len(17):4][name(17):3pad]
    # So node_type at fic_nl_pos - 4, name_len at fic_nl_pos, name at fic_nl_pos + 4
    # Wait, fic_nl_pos = position of name_len. So node_type at fic_nl_pos - 4.
    # The 3 simple fields start at fic_nl_pos - 4 - 12 = fic_nl_pos - 16

    # Let me verify: for build_metalmine, FIC name_len is at 100, name at 104.
    # node_type at 96 (100-4). 3 simple fields at 84, 88, 92 (100-16 to 100-5).
    # Yes: simple_start = fic_nl_pos - 16

    simple_start = fic_nl_pos - 16
    if simple_start < 0:
        return None

    facility_type = struct.unpack_from("<i", raw, simple_start)[0]
    sorting_shop = struct.unpack_from("<i", raw, simple_start + 4)[0]
    is_obsolete = struct.unpack_from("<i", raw, simple_start + 8)[0]
    # Note: there's a 4-byte gap between the 3rd field (isObsolete) and the node_type
    # That gap (at simple_start+12 = fic_nl_pos-4) is the node_type for FIC label

    return {
        "facilityType": facility_type,
        "sortingShop": sorting_shop,
        "isObsolete": bool(is_obsolete),
    }


def find_facility_id(raw):
    """Find the facility ID string (build_xxx or module_xxx)."""
    for i in range(0, min(len(raw) - 20, 600), 4):
        slen = struct.unpack_from("<I", raw, i)[0]
        if 7 < slen < 60 and i + 4 + slen <= len(raw):
            try:
                s = raw[i + 4 : i + 4 + slen].decode("ascii")
                if (
                    s.startswith("build_") or s.startswith("module_")
                ) and s.isprintable():
                    return s
            except:
                pass
    return None


def find_class_type(raw):
    """Find the class type string."""
    for tag in [
        b"NuclearBomb",
        b"MiningFacility",
        b"PowerFacility",
        b"HabitationFacility",
        b"ProductionFacility",
        b"LaunchFacility",
        b"TerraformationFacility",
        b"OtherFacility",
        b"FacilitySegment",
        b"ConstructionEquipmentModule",
    ]:
        if tag in raw:
            return tag.decode()
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
print("Loading localization...")
loc = {}
loc_path = GAME_DIR / r"Solar Expanse_Data\StreamingAssets\Languages\en-US.csv"
with open(loc_path, encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line or "," not in line:
            continue
        k, v = line.split(",", 1)
        loc[k] = v.strip('"')

print("Loading assets...")
env = UnityPy.load(os.path.join(data_dir, "sharedassets0.assets"))

results = {}
failures = []
no_fic = 0

for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        raw = obj.get_raw_data()
        if not raw or len(raw) < 100:
            continue

        values = extract_facility(raw)
        if values is None:
            no_fic += 1
            continue

        facility_id = find_facility_id(raw)
        if not facility_id:
            continue

        class_type = find_class_type(raw)

        entry = {
            "facility_id": facility_id,
            "class_type": class_type,
            "facilityType": values.get("facilityType"),
            "isObsolete": values.get("isObsolete", False),
            "has_localization": facility_id in loc,
            "display_name": loc.get(facility_id, "(none)"),
        }

        results[facility_id] = entry

    except Exception as e:
        failures.append((getattr(obj, "path_id", "?"), str(e)))

print(f"\nExtracted {len(results)} facilities ({no_fic} without facilityItemClass)")
if failures:
    print(f"Failures: {len(failures)} (showing first 5)")
    for pid, err in failures[:5]:
        print(f"  pid={pid}: {err}")

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
obsolete = [(fid, d) for fid, d in results.items() if d["isObsolete"]]

print(f"\nisObsolete=True: {len(obsolete)}")
for fid, d in sorted(obsolete):
    print(f"  {fid}: class={d.get('class_type')}")

print("\n_big VARIANTS:")
for fid, d in sorted(results.items()):
    if fid.endswith("_big"):
        print(f"  {fid}: isObsolete={d['isObsolete']}")

print("\n_deposition VARIANTS:")
for fid, d in sorted(results.items()):
    if fid.endswith("_deposition"):
        print(f"  {fid}: isObsolete={d['isObsolete']}")

print("\nmodule_contractitem (Nuclear Device):")
nd = results.get("module_contractitem")
if nd:
    print(f"  isObsolete={nd['isObsolete']}, class={nd.get('class_type')}")

# Save
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {OUTPUT_PATH}")
