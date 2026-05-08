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
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "facility_costs.json"


def read_str_at(raw, pos):
    """Read a length-prefixed string at pos, return (string, next_pos) or (None, pos)."""
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
        if not all(c.isprintable() for c in s):
            return None, pos
        # padded to 4-byte alignment
        pad = (4 - slen % 4) % 4
        return s, end + pad
    except Exception:
        return None, pos


def read_double_at(raw, pos):
    if pos + 8 <= len(raw):
        return struct.unpack_from("<d", raw, pos)[0]
    return None


def read_float_at(raw, pos):
    if pos + 4 <= len(raw):
        return struct.unpack_from("<f", raw, pos)[0]
    return None


def read_int32_at(raw, pos):
    """Read a little-endian int32 at pos, or None if out of bounds."""
    if pos + 4 <= len(raw):
        return struct.unpack_from("<i", raw, pos)[0]
    return None


def extract_facility_type(raw, fid_content_pos):
    """Extract EFacilityType enum from Odin-serialized FacilityBaseDescriptor.

    The facilityType appears shortly after the facility ID string, but its exact
    offset depends on the descriptor subclass:
      - GroundFacilityDescriptor: marker=1 at off, type at off+4  (offsets ~52-76)
      - SpaceModuleDescriptor:    standalone type value          (offsets ~64-76)

    We scan forward from the ID string content using a multi-rule approach.
    """
    # Collect int32 values near the ID (offsets 0..200)
    ints = {}
    for offset in range(0, 200, 4):
        pos = fid_content_pos + offset
        if pos + 4 > len(raw):
            break
        val = read_int32_at(raw, pos)
        if val is not None and val != 0:  # skip zero (filtered like the dumper)
            ints[offset] = val

    offsets = sorted(ints.keys())

    # Rule 1: marker=1 at offsets 48-80, followed by value 0-8
    for off in offsets:
        if 48 <= off <= 80 and ints[off] == 1:
            if off + 4 in ints and 0 <= ints[off + 4] <= 8:
                return ints[off + 4]

    # Rule 2: marker=1 at offsets 48-80, no next value -> Module (0)
    for off in offsets:
        if 48 <= off <= 80 and ints[off] == 1:
            if off + 4 not in ints:
                return 0

    # Rule 3: standalone value 0-8 at offsets 60-76 (SpaceModuleDescriptor layout)
    for off in offsets:
        if 60 <= off <= 76 and 0 <= ints[off] <= 8:
            return ints[off]

    # Rule 4: broader marker=1, no next -> Module (0)
    for off in offsets:
        if ints[off] == 1 and off + 4 not in ints:
            return 0

    return None


def find_all(raw, needle):
    """Find all positions of needle bytes in raw."""
    positions = []
    start = 0
    while True:
        idx = raw.find(needle, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + 1
    return positions


def extract_class_type(raw):
    """Extract the C# class type name from the MonoBehaviour raw data.

    The class type appears as a string like:
        '0|System.RuntimeType, mscorlib...Game.ObjectInfoDataScripts.MiningFacility, Assembly-CSharp'
    or  'facilityItemClass0|System.RuntimeType, mscorlib...Game.ObjectInfoDataScripts.CustomFacilitiesAndModules.RefineryF'

    Returns the short class name (e.g. 'MiningFacility', 'RefineryF') or None.
    """
    for i in range(40, min(len(raw), 400), 4):
        s, _ = read_str_at(raw, i)
        if not s:
            continue
        # Look for the class type specifier string
        if "ObjectInfoDataScripts" not in s and "Assembly-CSharp" not in s:
            continue
        if "System.Nullable" in s:
            continue  # skip trivia references
        # Extract the class name after the last '.' and before ',' or end
        if "ObjectInfoDataScripts." in s:
            # Full path: ...ObjectInfoDataScripts.SomeClass or ...ObjectInfoDataScripts.Sub.SomeClass
            after_ns = s.split("ObjectInfoDataScripts.")[-1]
            class_name = after_ns.split(",")[0].strip()
            if class_name:
                return class_name
        elif "Assembly-CSharp" in s:
            # Simpler format: just the class name before ', Assembly-CSharp'
            parts = s.split(",")
            for p in parts:
                p = p.strip()
                if (
                    p
                    and "Assembly-CSharp" not in p
                    and "mscorlib" not in p
                    and "System." not in p
                ):
                    return p
    return None


def extract_facility(raw, obj_id):
    """Extract build cost data from a facility descriptor object."""
    result = {
        "obj_id": obj_id,
        "facility_id": None,
        "class_type": None,
        "build_time_days": None,
        "resources": {},
        "money_cost": 0.0,
    }

    # Extract class type first (found in the first ~400 bytes)
    result["class_type"] = extract_class_type(raw)

    # Strategy: find the facility ID by looking for 'build_', 'module_', 'id_LV_', etc.
    # then scan nearby bytes for resource costs

    # Find the SECOND occurrence of the ID (first is m_Name, second is the 'id' field in Odin)
    # We detect the id field by finding a length-prefixed string at 4-byte aligned positions

    facility_id = None
    id_field_pos = None  # position of the START of the id string length prefix

    # Scan for length-prefixed strings that look like facility IDs
    candidates = []
    for i in range(0, len(raw) - 4, 4):
        s, next_pos = read_str_at(raw, i)
        if s and (
            s.startswith("build_")
            or s.startswith("module_")
            or s.startswith("id_LV_")
            or s.startswith("id_SpacecraftType_")
        ):
            candidates.append((i, s))

    if not candidates:
        return None

    # Use the LAST occurrence (deepest in the data = actual id field in Odin serialization)
    # Actually, use the one that appears AFTER the big header section (after byte 400)
    # which contains the actual game data

    # Find facility ID occurrences
    id_occurrences = {}
    for pos, s in candidates:
        if s not in id_occurrences:
            id_occurrences[s] = []
        id_occurrences[s].append(pos)

    # Pick the most common ID
    if not id_occurrences:
        return None

    # Get the first valid ID (build_ prefix preferred)
    for fid_start in ["build_", "module_", "id_LV_", "id_SpacecraftType_"]:
        for s in id_occurrences:
            if s.startswith(fid_start) and "Test" not in s and "test" not in s:
                facility_id = s
                # Use the occurrence that is after position 200 (past the Unity header)
                valid_positions = [p for p in id_occurrences[s] if p > 200]
                if valid_positions:
                    id_field_pos = valid_positions[0]
                    break
                elif id_occurrences[s]:
                    id_field_pos = id_occurrences[s][-1]
                    break
        if facility_id:
            break

    if not facility_id or id_field_pos is None:
        return None

    result["facility_id"] = facility_id

    # Extract facilityType enum (EFacilityType: 0=Module … 8=FacilitySegment)
    fid_content_pos = id_field_pos + 4  # string content starts after length prefix
    result["facility_type"] = extract_facility_type(raw, fid_content_pos)

    # After the id field, scan for resource costs within the next ~800 bytes
    # Pattern: [list_count: int32][resource_id: string][amount: double] (repeated count times)
    # Then: [money_cost: double]

    search_start = id_field_pos
    search_end = min(len(raw), id_field_pos + 800)

    # Find resource ID strings (id_resource_*) in the search window
    resource_pos_list = []
    for i in range(search_start, search_end - 4, 4):
        s, next_pos = read_str_at(raw, i)
        if s and s.startswith("id_resource_"):
            # Read the double right after
            amount = read_double_at(raw, next_pos)
            if amount is not None and amount > 0:
                resource_pos_list.append((i, s, amount, next_pos))

    # Collect resources (deduplicate, keeping highest value if duplicated)
    resources = {}
    for pos, rid, amount, next_pos in resource_pos_list:
        clean_rid = rid.replace("id_resource_", "")
        if clean_rid not in resources or amount > resources[clean_rid]:
            resources[clean_rid] = amount

    result["resources"] = resources

    # Find money cost: double at position right after the last resource entry
    if resource_pos_list:
        last_entry = max(resource_pos_list, key=lambda x: x[0])
        money_pos = last_entry[3] + 8  # after the amount double
        money = read_double_at(raw, money_pos)
        if money is not None and 0 <= money <= 100000000:
            result["money_cost"] = money

    # Find build time: float in range 0.5-2000 days, near the id field
    build_times_found = []
    for i in range(search_start, min(len(raw), search_start + 400) - 4, 4):
        v = read_float_at(raw, i)
        if v is not None and 0.5 <= v <= 2000.0 and v != v % 0.1 and v == round(v, 1):
            build_times_found.append((i, v))

    # Filter: the FIRST reasonable build time after the id field
    for pos, v in build_times_found[:5]:
        if 1.0 <= v <= 2000.0:
            result["build_time_days"] = v
            break

    return result


# Load assets
print("Loading assets and extracting facility data...\n")

asset_file = "sharedassets0.assets"
path = os.path.join(data_dir, asset_file)
env = UnityPy.load(path)

facilities = {}  # keyed by facility_id, deduplication

for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        raw = obj.get_raw_data()
        if not raw:
            continue
        # Quick filter
        has_build = (
            b"build_" in raw
            or b"module_" in raw
            or b"id_LV_" in raw
            or b"id_SpacecraftType_" in raw
        )
        if not has_build:
            continue

        data = extract_facility(raw, obj.path_id)
        if data and data["facility_id"]:
            fid = data["facility_id"]
            # Keep the one with more resources (avoid duplicates that have empty data)
            if fid not in facilities or len(data["resources"]) > len(
                facilities[fid]["resources"]
            ):
                facilities[fid] = data
    except Exception as e:
        pass

# Print and save results
print(f"Found {len(facilities)} unique facilities/buildings:\n")

# Sort by category
sorted_facilities = sorted(facilities.values(), key=lambda x: x["facility_id"])

output_data = {}
for f in sorted_facilities:
    fid = f["facility_id"]
    resources = f["resources"]
    money = f["money_cost"]
    build_time = f["build_time_days"]

    res_str = (
        ", ".join(f"{r}: {int(a)}" for r, a in sorted(resources.items()))
        if resources
        else "none"
    )
    money_str = f"${money:.0f}" if money > 0 else "$0 (resource only)"
    bt_str = f"{build_time} days" if build_time else "?"

    print(f"  {fid}")
    print(f"    Build time: {bt_str}")
    print(f"    Resources:  {res_str}")
    print(f"    Money cost: {money_str}")
    print()

    output_data[fid] = {
        "build_time_days": build_time,
        "resources": resources,
        "money_cost": money,
        "class_type": f.get("class_type"),
        "facility_type": f.get("facility_type"),
    }

# Save to JSON
with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
    json.dump(output_data, fp, indent=2, ensure_ascii=False)

print(f"\nSaved to {OUTPUT_PATH} ({len(output_data)} entries)")
