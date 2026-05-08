"""
Extract research definitions from the game's Odin-serialized assets.

For each ResearchDefinition, finds facility IDs that are unlocked via
unlockData.actionUnlock == UnlockFacility (value 1) with a matching
parameter1 string (build_* or module_*).

Principle: Odin serializes simple values directly.  The UnlockData struct
is serialized inline: its actionUnlock field appears as a raw int32 (1 for
UnlockFacility), immediately followed by parameter1 (string), etc.
We look for actionUnlock=1 values immediately followed by a build_/module_
string within genuine ResearchDefinition objects.

Output: research_unlocks.json → { "all_unlocked_facilities": [...], ... }
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
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "research_unlocks.json"


def find_strings(raw, prefix="", min_len=7, max_len=80):
    """Find all strings in raw data starting with the given prefix.
    Returns list of (offset_of_name_len, string_value)."""
    results = []
    for i in range(0, len(raw) - 4, 4):
        slen = struct.unpack_from("<I", raw, i)[0]
        if min_len <= slen <= max_len and i + 4 + slen <= len(raw):
            try:
                s = raw[i + 4 : i + 4 + slen].decode("ascii")
                if s.startswith(prefix) and s.isprintable():
                    results.append((i, s))
            except:
                pass
    return results


def is_valid_facility_id(s):
    """Check if a string looks like a real facility ID (not a localization key)."""
    if not (s.startswith("build_") or s.startswith("module_")):
        return False
    # Exclude localization suffixes
    if (
        s.endswith("_Description")
        or s.endswith("_Capabilities")
        or s.endswith("_Title")
        or s.endswith("_fluff")
        or s.endswith("_StatsFormat")
    ):
        return False
    return True


def is_research_definition(raw):
    """Check if raw data is a genuine ResearchDefinition (not a container)."""
    # Research definitions are small and have their ID near the start
    if len(raw) > 2000:
        return False
    research_ids = find_strings(raw, prefix="research_", min_len=10, max_len=80)
    if not research_ids:
        return False
    first_offset, _first_id = research_ids[0]
    if first_offset > 60:
        return False
    return True


def main():
    print("Loading assets...")
    env = UnityPy.load(os.path.join(data_dir, "sharedassets0.assets"))

    all_unlocked = set()
    research_count = 0

    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        if not raw or len(raw) < 100:
            continue

        if not is_research_definition(raw):
            continue

        research_count += 1

        # Build a map of offset -> string for build_/module_ IDs
        facility_strings = {}
        for off, s in find_strings(raw, prefix="build_", min_len=7, max_len=60):
            if is_valid_facility_id(s):
                facility_strings[off] = s
        for off, s in find_strings(raw, prefix="module_", min_len=7, max_len=60):
            if is_valid_facility_id(s):
                facility_strings[off] = s

        # Look for actionUnlock=1 (UnlockFacility) immediately before a facility
        # string. Odin serializes UnlockData inline:
        #   [actionUnlock:4][strlen:4][str:N][pad]
        # So actionUnlock is 4 bytes before the string length prefix.
        for str_off in facility_strings:
            action_offset = str_off - 4
            if action_offset >= 0:
                val = struct.unpack_from("<I", raw, action_offset)[0]
                if val == 1:  # EActionUnlock.UnlockFacility
                    all_unlocked.add(facility_strings[str_off])

    all_unlocked_sorted = sorted(all_unlocked)

    print(f"Found {research_count} research definitions")
    print(f"Unique facilities unlocked by research: {len(all_unlocked)}")

    # Show variants that have research (should be none — these are locked
    # behind isLocked=true with no research to unlock them)
    big_with_research = [f for f in all_unlocked if f.endswith("_big")]
    dep_with_research = [f for f in all_unlocked if f.endswith("_deposition")]
    two_with_research = [f for f in all_unlocked if f.endswith("2")]
    if big_with_research:
        print(f"  _big with research: {big_with_research}")
    if dep_with_research:
        print(f"  _deposition with research: {dep_with_research}")
    if two_with_research:
        print(f"  _2 with research: {two_with_research}")

    print("Sample unlocked facilities:")
    for f in all_unlocked_sorted[:15]:
        print(f"  {f}")
    if len(all_unlocked_sorted) > 15:
        print(f"  ... and {len(all_unlocked_sorted) - 15} more")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"all_unlocked_facilities": all_unlocked_sorted},
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
