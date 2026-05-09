"""
extract_icons.py — Extract resource, facility, and spacecraft icons from
Solar Expanse Unity asset files.

Resources: sprites in the solar_expanse_icons atlas (sharedassets0.assets).
Facilities & spacecraft: standalone Texture2D objects named after the icon
(mostly in resources.assets), NOT sprites in an atlas.

Strategy:
  1. Scan all .assets files; build TWO registries:
     - texture_registry:   Texture2D name → PIL.Image (standalone icons)
     - sprite_objects:     sprite name → UnityPy Sprite object
  2. Resource icons: find sprite by name, use sprite.image (UnityPy handles
     all atlas resolution, alpha merging, cropping, and coordinate flips).
  3. Facility/spacecraft icons: try texture_registry first, then sprite_objects.
"""

import argparse
import json
import os
import shutil
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
data_dir = GAME_DIR / "Solar Expanse_Data"
output_dir = Path(__file__).resolve().parent / "icons"
output_dir.mkdir(exist_ok=True)

PROJECT_DATA_DIR = Path(__file__).resolve().parent / "data"

# ---- Step 1: Build global registries across all .assets files ----

# texture_registry: lowercase name → PIL.Image (standalone Texture2D icons)
texture_registry = {}
# sprite_objects: lowercase name → UnityPy Sprite object (for on-demand .image)
sprite_objects = {}

asset_files = sorted(data_dir.glob("*.assets"))
if not asset_files:
    asset_files = sorted(data_dir.glob("sharedassets*.assets"))

print(f"Found {len(asset_files)} asset file(s):")
for af in asset_files:
    print(f"  {af.name}")

for asset_path in asset_files:
    try:
        env = UnityPy.load(str(asset_path))
    except Exception as e:
        print(f"  WARNING: Could not load {asset_path.name}: {e}")
        continue

    # --- Pass A: collect standalone Texture2D objects by name ---
    for obj in env.objects:
        if obj.type.name != "Texture2D":
            continue
        try:
            d = obj.read()
            if d.image is not None:
                name = (getattr(d, "m_Name", None) or "").lower()
                if name and name not in texture_registry:
                    texture_registry[name] = d.image
        except Exception:
            pass

    # --- Pass B: collect Sprite objects by name ---
    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        try:
            d = obj.read()
            name = d.m_Name
            if name:
                key = name.lower()
                if key not in sprite_objects:
                    sprite_objects[key] = d
        except Exception:
            pass

print(f"\nTotal standalone textures: {len(texture_registry)}")
print(f"Total sprite objects:      {len(sprite_objects)}")


def get_sprite_image(name):
    """Return a PIL.Image for a sprite by name, or None.

    Uses UnityPy's built-in sprite.image property which handles:
      - Atlas texture resolution (including SpriteAtlas references)
      - Separate alpha texture merging
      - Cropping to the sprite's textureRect
      - Packing rotation (flip/rotate)
      - Bottom-left → top-left coordinate flip
    """
    d = sprite_objects.get(name.lower())
    if d is None:
        return None
    try:
        img = d.image
        if img is not None:
            return img
    except Exception:
        pass
    return None


# ---- Step 2: Extract resource icons (always from atlas sprites) ----

# Load resource->sprite mapping extracted by the BepInEx plugin
with open(PROJECT_DATA_DIR / "resource_icons.json", encoding="utf-8") as f:
    resource_to_sprite = json.load(f)
print(f"Loaded resource icon mapping ({len(resource_to_sprite)} entries)")

resource_icon_map = {}
print("\n--- Resource icons ---")
for res_id, sprite_name in sorted(resource_to_sprite.items()):
    icon = get_sprite_image(sprite_name)
    if icon is None:
        print(f"  WARNING: sprite '{sprite_name}' not found for {res_id}")
        continue

    clean_name = res_id.replace("id_resource_", "")
    out_path = output_dir / f"{clean_name}.png"
    icon.save(out_path)
    resource_icon_map[res_id] = f"{clean_name}.png"
    print(f"  Saved: {clean_name}.png ({icon.width}x{icon.height})")

with open(output_dir / "resource_icon_map.json", "w", encoding="utf-8") as f:
    json.dump(resource_icon_map, f, indent=2)

# ---- Step 3: Extract facility & spacecraft icons ----
#
# Lookup order:
#   1. texture_registry (standalone Texture2D by name)
#   2. sprite_objects (atlas sprite, via sprite.image)


def load_json(filename):
    path = PROJECT_DATA_DIR / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


facility_icon_map = load_json("facility_icons.json")
launch_vehicle_icon_map = load_json("launch_vehicle_icons.json")
spacecraft_icon_map = load_json("spacecraft_icons.json")


def extract_icons(icon_map, subdir_name, label):
    """Extract icons for a category (facilities or spacecraft).

    For each (game_id → sprite_name) entry:
      1. Look up sprite_name as a standalone Texture2D (by name).
      2. Fall back to the sprite registry (via sprite.image).
    Returns a dict: game_id → relative PNG path.
    """
    result = {}
    if not icon_map:
        print(f"\n--- No {label} icons data found (run extract-run first) ---")
        return result

    print(f"\n--- {label} icons ({len(icon_map)} entries) ---")
    subdir = output_dir / subdir_name
    # Clean stale icons
    if subdir.exists():
        shutil.rmtree(subdir)
    subdir.mkdir(exist_ok=True)

    found_texture = 0
    found_sprite = 0
    missing = 0

    for game_id, sprite_name in sorted(icon_map.items()):
        if not sprite_name:
            missing += 1
            continue

        safe_name = game_id.replace("/", "_").replace("\\", "_")
        out_path = subdir / f"{safe_name}.png"

        # --- Try standalone texture first ---
        tex = texture_registry.get(sprite_name.lower())
        if tex is not None:
            tex.save(out_path)
            result[game_id] = f"{subdir_name}/{safe_name}.png"
            found_texture += 1
            if found_texture <= 5:
                print(f"  [tex] Saved: {safe_name}.png ({tex.width}x{tex.height})")
            continue

        # --- Fall back to sprite ---
        icon = get_sprite_image(sprite_name)
        if icon is not None:
            icon.save(out_path)
            result[game_id] = f"{subdir_name}/{safe_name}.png"
            found_sprite += 1
            if found_sprite <= 5:
                print(f"  [sprite] Saved: {safe_name}.png ({icon.width}x{icon.height})")
            continue

        # --- Not found ---
        missing += 1
        if missing <= 5:
            print(f"  MISSING: {game_id} -> '{sprite_name}'")

    total = found_texture + found_sprite
    if total > 10:
        extra = (
            total
            - max(found_texture if found_texture <= 5 else 5, 0)
            - max(found_sprite if found_sprite <= 5 else 5, 0)
        )
        if extra > 0:
            print(f"  ... and {extra} more")
    print(
        f"  Found: {found_texture} textures + {found_sprite} sprites; missing: {missing}"
    )
    return result


facility_icons = extract_icons(facility_icon_map, "facilities", "Facility")
launch_vehicle_icons = extract_icons(
    launch_vehicle_icon_map, "launch_vehicles", "Launch Vehicle"
)
spacecraft_icons = extract_icons(spacecraft_icon_map, "spacecraft", "Spacecraft")

# ---- Step 4: Save combined icon mapping for generate_table.py ----

combined_icon_map = {
    "resources": resource_icon_map,
    "facilities": facility_icons,
    "launch_vehicles": launch_vehicle_icons,
    "spacecraft": spacecraft_icons,
}
with open(output_dir / "icon_map.json", "w", encoding="utf-8") as f:
    json.dump(combined_icon_map, f, indent=2)

print("\n--- Summary ---")
print(f"  Resource icons:        {len(resource_icon_map)}")
print(f"  Facility icons:        {len(facility_icons)}")
print(f"  Launch vehicle icons:  {len(launch_vehicle_icons)}")
print(f"  Spacecraft icons:      {len(spacecraft_icons)}")
print(f"  Texture registry:   {len(texture_registry)} standalone textures")
print(f"  Sprite objects:     {len(sprite_objects)}")
print(f"  Icon map saved:     icon_map.json")
print(f"  Icons directory:    {output_dir}")
