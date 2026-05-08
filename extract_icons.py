import argparse
import json
import os
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
output_dir = Path(__file__).resolve().parent / "icons"
output_dir.mkdir(exist_ok=True)

env = UnityPy.load(os.path.join(data_dir, "sharedassets0.assets"))

# Load the atlas texture
atlas_img = None
for obj in env.objects:
    if obj.type.name == "Texture2D":
        d = obj.read()
        if d.m_Name == "solar_expanse_icons":
            atlas_img = d.image
            atlas_h = d.m_Height
            print(f"Loaded atlas: {d.m_Width}x{d.m_Height}")
            break

if atlas_img is None:
    print("ERROR: Atlas not found!")
    exit(1)

# Resource ID -> sprite index mapping (from map_resource_icons.py output)
resource_to_sprite = {
    "id_resource_alloy": "solar_expanse_icons_13",
    "id_resource_antimatter": "solar_expanse_icons_19",
    "id_resource_chips": "solar_expanse_icons_10",
    "id_resource_co2": "solar_expanse_icons_21",
    "id_resource_consumergoods": "solar_expanse_icons_20",
    "id_resource_energy": "solar_expanse_icons_8",
    "id_resource_fuel": "solar_expanse_icons_5",
    "id_resource_glass": "solar_expanse_icons_14",
    "id_resource_hel3": "solar_expanse_icons_6",
    "id_resource_human": "solar_expanse_icons_18",
    "id_resource_hydrogen": "solar_expanse_icons_15",
    "id_resource_metal": "solar_expanse_icons_1",
    "id_resource_nitrogen": "solar_expanse_icons_22",
    "id_resource_noblegas": "solar_expanse_icons_17",
    "id_resource_oxygen": "solar_expanse_icons_16",
    "id_resource_plastic": "solar_expanse_icons_9",
    "id_resource_raremetal": "solar_expanse_icons_2",
    "id_resource_silicon": "solar_expanse_icons_3",
    "id_resource_steel": "solar_expanse_icons_11",
    "id_resource_supply": "solar_expanse_icons_7",
    "id_resource_uran": "solar_expanse_icons_4",
    "id_resource_volatile": "solar_expanse_icons_12",
    "id_resource_water": "solar_expanse_icons_0",
}

# Collect sprite rects from Sprite objects
sprite_rects = {}  # name -> (x, y, w, h) in PIL coords
for obj in env.objects:
    if obj.type.name != "Sprite":
        continue
    try:
        d = obj.read()
        name = d.m_Name
        if not name.startswith("solar_expanse_icons_"):
            continue
        rect = d.m_Rect
        x = int(rect.x)
        y = int(rect.y)
        w = int(rect.width)
        h = int(rect.height)
        # Unity uses bottom-left origin; PIL uses top-left
        # Convert: PIL_y = atlas_height - unity_y - sprite_height
        pil_y = atlas_h - y - h
        sprite_rects[name] = (x, pil_y, x + w, pil_y + h)
    except:
        pass

print(f"Found {len(sprite_rects)} atlas sprites\n")

# Extract each resource icon
for res_id, sprite_name in sorted(resource_to_sprite.items()):
    if sprite_name not in sprite_rects:
        print(f"WARNING: sprite {sprite_name} not found for {res_id}")
        continue

    rect = sprite_rects[sprite_name]
    icon = atlas_img.crop(rect)

    # Save with clean resource name (strip id_resource_ prefix)
    clean_name = res_id.replace("id_resource_", "")
    out_path = output_dir / f"{clean_name}.png"
    icon.save(out_path)
    print(f"  Saved: {clean_name}.png ({icon.width}x{icon.height}) [{res_id}]")

# Also extract the full atlas for reference
atlas_img.save(output_dir / "_atlas_full.png")
print(f"\nAll icons saved to: {output_dir}/")
print(f"Full atlas saved as: _atlas_full.png")

# Save a resource ID to icon filename mapping JSON
mapping = {
    res_id: res_id.replace("id_resource_", "") + ".png" for res_id in resource_to_sprite
}
with open(output_dir / "resource_icon_map.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2)
print("Resource icon map saved: resource_icon_map.json")
