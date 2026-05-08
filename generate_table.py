import base64
import html as htmllib
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

with open(DATA_DIR / "facility_costs.json", encoding="utf-8") as f:
    facility_data = json.load(f)
with open(DATA_DIR / "spacecraft_costs.json", encoding="utf-8") as f:
    spacecraft_data = json.load(f)

icons_dir = BASE_DIR / "icons"

RESOURCE_NAMES = {
    "metal": "Metals",
    "raremetal": "Rare Metals",
    "steel": "Alloy",
    "alloy": "Exotic Alloys",
    "chips": "Electronics",
    "plastic": "Polymers",
    "glass": "Glass",
    "silicon": "Silicon",
    "supply": "Supplies",
    "fuel": "Chem. Fuel",
    "hel3": "Helium-3",
    "uran": "Fissiles",
    "volatile": "Carbon",
    "water": "Water",
    "hydrogen": "Hydrogen",
    "oxygen": "Oxygen",
    "nitrogen": "Nitrogen",
    "noblegas": "Noble Gas",
    "co2": "CO2",
    "energy": "Energy",
    "human": "Human",
    "consumergoods": "Consumer Goods",
    "antimatter": "Antimatter",
}
ALL_RESOURCES = list(RESOURCE_NAMES.keys())

loc = {}
with open(DATA_DIR / "loc_names.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or "," not in line:
            continue
        k, v = line.split(",", 1)
        loc[k] = v.strip('"')

# Load buildability flags extracted from the game's Odin-serialized assets.
# These come from FacilityBaseDescriptor.isObsolete bool.
_BUILDABILITY = {}
try:
    with open(DATA_DIR / "extracted_buildability.json", encoding="utf-8") as f:
        _BUILDABILITY = json.load(f)
    print(f"Loaded buildability data for {len(_BUILDABILITY)} facilities")
except FileNotFoundError:
    print("WARNING: extracted_buildability.json not found in data/")

# Load research unlock data: set of facility IDs that have at least one
# research definition that unlocks them (via UnlockData.actionUnlock == UnlockFacility).
# These are the only facilities that start locked (isLocked=true) but can become
# available through research. Facilities without research and without the isLocked
# flag are freely available from the start.
_RESEARCH_UNLOCK_SET = set()
try:
    with open(DATA_DIR / "research_unlocks.json", encoding="utf-8") as f:
        research_data = json.load(f)
    _RESEARCH_UNLOCK_SET = set(research_data.get("all_unlocked_facilities", []))
    print(f"Loaded research unlocks for {len(_RESEARCH_UNLOCK_SET)} facilities")
except FileNotFoundError:
    print(
        "ERROR: research_unlocks.json not found. Run extract_research.py first.",
        file=sys.stderr,
    )
    sys.exit(1)

# Known non-buildable class types (from DLL exploration)
# NuclearBomb = Nuclear Device quest item (module_contractitem)
NON_BUILDABLE_CLASSES = {
    "NuclearBomb",
}

# Items confirmed not present in the game UI (scrapped/disabled content)
SKIP_IDS = {
    "module_metalmining",
    "module_raremining",
}


def _is_buildable_id(fid, entry):
    """Determine if a facility ID represents a player-buildable item.

    Uses isLocked from the BepInEx plugin (real C# property) instead of
    suffix-matching heuristics. Falls back to suffix check only when
    isLocked is absent from the buildability data.
    """
    # Must have localization
    if fid not in loc:
        return False

    # Exclude test/fake items
    lower_id = fid.lower()
    if "test" in lower_id or "fake" in lower_id:
        return False

    # Check isObsolete flag
    bd = _BUILDABILITY.get(fid)
    if bd is not None and bd.get("isObsolete", False):
        return False

    # Exclude known non-buildable class types
    class_type = entry.get("class_type") or (bd or {}).get("class_type")
    if class_type and class_type in NON_BUILDABLE_CLASSES:
        return False

    # Exclude items confirmed not present in the game UI
    if fid in SKIP_IDS:
        return False

    # --- isLocked check (real data from BepInEx plugin) ---
    if bd is not None and "isLocked" in bd:
        is_locked = bd["isLocked"]
        if not is_locked:
            return True  # freely available
        return fid in _RESEARCH_UNLOCK_SET  # locked: needs research

    # Fallback: old Python extraction without isLocked — suffix proxy
    if fid in _RESEARCH_UNLOCK_SET:
        return True
    if fid.endswith("_big") or fid.endswith("_deposition") or fid.endswith("2"):
        return False
    return True


buildings = {
    k: v
    for k, v in facility_data.items()
    if k.startswith("build_") and _is_buildable_id(k, v)
}
modules = {
    k: v
    for k, v in facility_data.items()
    if k.startswith("module_") and _is_buildable_id(k, v)
}
spacecraft = {}
for k, v in spacecraft_data.items():
    display_name = v.get("display_name")
    if not display_name:
        text_key = v.get("text_key", "")
        # Try exact match, then lowercase (C# Name -> CSV key)
        display_name = (
            loc.get(text_key, "")
            or loc.get(text_key.lower(), "")
            or loc.get(k, "")
            or loc.get(k.lower(), "")
        )
    if display_name and (v.get("resources") or v.get("build_time_days")):
        v["display_name"] = display_name
        spacecraft[k] = v

# facility_costs.json carries "facility_type" (extracted by extract_costs.py).
# Build a quick lookup:  facility_id -> enum int (0=Modules … 8=Segments).
_FTYPE_NAMES = {
    0: "Modules",
    1: "Habitation",
    2: "Power",
    3: "Mining",
    4: "Production",
    5: "Launch Facilities",
    6: "Terraformation",
    7: "Other",
    8: "Segments",
}

_FACILITY_TYPES = {}
for fid, entry in facility_data.items():
    ft = entry.get("facility_type")
    if ft is not None:
        _FACILITY_TYPES[fid] = ft
print(f"Loaded facility types for {len(_FACILITY_TYPES)} facilities")

# Category display order (matches game UI tab order: EFacilityType enum)
CATEGORY_ORDER = [
    "Modules",
    "Habitation",
    "Power",
    "Mining",
    "Production",
    "Launch Facilities",
    "Terraformation",
    "Segments",
    "Other",
]


def get_category(building_id, class_type):
    """Determine the game UI category for a building.

    Uses the EFacilityType enum value extracted from the game binary.
    Falls back to building-ID prefix matching for missing entries.
    """
    ft = _FACILITY_TYPES.get(building_id)
    if ft is not None:
        return _FTYPE_NAMES.get(ft, "Other")
    # Fallback for facilities missing from the extraction
    if (
        building_id.startswith("build_habitat")
        or building_id in ("build_outpost", "build_hq")
        or building_id.startswith("build_space_0g")
    ):
        return "Habitation"
    if building_id.startswith("build_launch_"):
        return "Launch Facilities"
    if building_id.startswith("build_terraform_"):
        return "Terraformation"
    if building_id.startswith("build_interstellar_"):
        return "Segments"
    return "Other"


def categorize_buildings(buildings_dict):
    """Split buildings dict into {category: {id: data}} mapping."""
    result = {cat: {} for cat in CATEGORY_ORDER}
    for bid, data in buildings_dict.items():
        class_type = data.get("class_type")
        cat = get_category(bid, class_type)
        if cat in result:
            result[cat][bid] = data
        else:
            result["Other"][bid] = data
    return result


def used_resources(entries):
    used = set()
    for v in entries:
        used.update(v.get("resources", {}).keys())
    return [r for r in ALL_RESOURCES if r in used]


def icon_b64(subpath):
    """Read a PNG from icons/ and return its base64 string."""
    path = icons_dir / subpath
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return None

# Pre-load resource icons (flat PNGs in icons/)
icon_data = {r: icon_b64(f"{r}.png") for r in ALL_RESOURCES}

all_res = used_resources(
    list(buildings.values()) + list(modules.values()) + list(spacecraft.values())
)

# Generate CSS classes only for resources actually used in the table
_res_icon_css_parts = []
for _rid in all_res:
    _b64 = icon_data.get(_rid)
    if _b64:
        _name = _rid.replace("id_resource_", "")
        _res_icon_css_parts.append(
            f".ric-{_name}{{background-image:url(data:image/png;base64,{_b64})}}"
        )
RES_ICON_CSS = "".join(_res_icon_css_parts)





# --- Load facility & spacecraft icons (generated by extract_icons.py from plugin data) ---
_facility_icon_data = {}  # facility_id -> base64 PNG
_spacecraft_icon_data = {}  # spacecraft_id -> base64 PNG

try:
    icon_map_path = icons_dir / "icon_map.json"
    if icon_map_path.exists():
        with open(icon_map_path, encoding="utf-8") as f:
            icon_map = json.load(f)
        # Pre-load facility icons
        for fid, rel_path in icon_map.get("facilities", {}).items():
            b64 = icon_b64(rel_path)
            if b64:
                _facility_icon_data[fid] = b64
        # Pre-load spacecraft icons
        for sid, rel_path in icon_map.get("spacecraft", {}).items():
            b64 = icon_b64(rel_path)
            if b64:
                _spacecraft_icon_data[sid] = b64
        print(
            f"Loaded {len(_facility_icon_data)} facility icons, "
            f"{len(_spacecraft_icon_data)} spacecraft icons"
        )
except Exception as e:
    print(f"Note: icon_map.json not loaded ({e})")


def facility_icon_img(fid, size=48):
    """Return an <img> tag for a facility/spacecraft icon, or empty string."""
    b64 = _facility_icon_data.get(fid) or _spacecraft_icon_data.get(fid)
    if b64:
        return (
            f'<img class="row-icon" src="data:image/png;base64,{b64}" '
            f'style="max-width:{size}px;max-height:{size}px" alt="">'
        )
    return ""


def header_row(resources, name_col="Name"):
    cells = [
        f'<th class="col-name">{name_col}</th>',
        '<th class="col-qty">Qty</th>',
        '<th class="col-days">Days</th>',
    ]
    for r in resources:
        short = r.replace("id_resource_", "")
        b64 = icon_data.get(r)
        img = (
            f'<span class="res-icon ric-{short}" '
            f'title="{RESOURCE_NAMES.get(r, r)}"></span>'
            if b64
            else ""
        )
        label = RESOURCE_NAMES.get(r, r)
        cells.append(
            f'<th class="col-res" data-res="{r}">{img}<span>{label}</span></th>'
        )
    cells.append('<th class="col-mass">Mass<br><small>(t)</small></th>')
    return "<tr>" + "".join(cells) + "</tr>"


def build_rows(entries, resources, key_fn, display_fn, time_fn):
    rows = []
    for key in sorted(entries.keys(), key=display_fn):
        v = entries[key]
        res = v.get("resources", {})
        t = time_fn(v)
        costs_json = json.dumps({r: res[r] for r in res})
        time_val = t if t else 0
        name = htmllib.escape(display_fn(key))
        sub = htmllib.escape(key)
        icon_html = facility_icon_img(key_fn(key))
        row = (
            f"<tr data-costs='{costs_json}' data-time=\"{time_val}\" data-resources='{json.dumps(list(res.keys()))}'>"
            f'<td class="col-name">{icon_html}<span>{name}<br><small>{sub}</small></span></td>'
            f'<td class="col-qty"><input type="number" min="0" value="0" class="qty-input"></td>'
            f'<td class="col-days res-days">0</td>'
        )
        for r in resources:
            row += f'<td class="col-res res-cell" data-res="{r}">-</td>'
        row += '<td class="col-mass res-mass">0</td>'
        row += "</tr>"
        rows.append(row)
    return "\n".join(rows)


def subtotal_row(resources, label="Subtotal"):
    cells = [
        f'<td class="subtotal-label" colspan="2">{label}</td>',
        '<td class="subtotal col-days" data-sum="days">0</td>',
    ]
    for r in resources:
        cells.append(f'<td class="subtotal col-res" data-sum="{r}">0</td>')
    cells.append('<td class="subtotal col-mass" data-sum="mass">0</td>')
    return "<tr class='subtotal-row'>" + "".join(cells) + "</tr>"


s_rows = build_rows(
    spacecraft, all_res, lambda k: k, lambda k: k, lambda v: v.get("build_time_days", 0)
)


# Fix spacecraft display: key=internal, display=display_name
def sc_display(k):
    return spacecraft[k].get("display_name", k)


s_rows = build_rows(
    spacecraft, all_res, lambda k: k, sc_display, lambda v: v.get("build_time_days", 0)
)

# Build categorized building sections HTML.
# Merge module_ items into the Module category – they share the same game UI tab.
categorized = categorize_buildings(buildings)
for mk, mv in modules.items():
    categorized["Modules"][mk] = mv

building_sections_html = ""
for cat in CATEGORY_ORDER:
    cat_buildings = categorized[cat]
    if not cat_buildings:
        continue
    cat_res_json = json.dumps(all_res)
    cat_rows = build_rows(
        cat_buildings,
        all_res,
        lambda k: k,
        lambda k: loc.get(k, k).upper(),
        lambda v: v.get("build_time_days", 0),
    )
    building_sections_html += f"""<h2>{cat} ({len(cat_buildings)})</h2>
<table data-res='{cat_res_json}'>
<thead>{header_row(all_res)}</thead>
<tbody>
{cat_rows}
{subtotal_row(all_res, f"{cat} subtotal")}
</tbody>
</table>
"""

# Grand total resource cells for the bottom panel
grand_cells = ""
for r in all_res:
    short = r.replace("id_resource_", "")
    img = (
        f'<span class="res-icon ric-{short}" '
        f'title="{RESOURCE_NAMES.get(r, r)}"></span>'
    )
    label = RESOURCE_NAMES.get(r, r)
    grand_cells += (
        f'<div class="grand-res" id="grand-{r}">'
        f'  {img}<span class="res-label">{label}</span>'
        f'  <span class="res-total" data-grand="{r}">0</span>'
        f"</div>"
    )

all_res_json = json.dumps(all_res)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Solar Expanse - Build Cost Calculator</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', sans-serif;
  background: #0d1117; color: #c9d1d9;
  padding: 16px 24px 160px;
}}
h1 {{ color: #58a6ff; font-size: 1.4em; margin-bottom: 16px; }}
h2 {{
  color: #79c0ff; font-size: 1.1em; margin: 28px 0 8px;
  border-bottom: 1px solid #21262d; padding-bottom: 6px;
}}
table {{
  border-collapse: collapse; width: 100%;
  margin-bottom: 6px; font-size: 12.5px;
}}
th {{
  background: #161b22; color: #8b949e; padding: 6px 5px;
  border: 1px solid #30363d; text-align: center;
  vertical-align: bottom; position: sticky; top: 0; z-index: 2;
  white-space: nowrap;
}}
td {{ padding: 4px 6px; border: 1px solid #21262d; vertical-align: middle; }}
td.col-name {{ min-width: 200px; font-weight: 600; padding: 0 6px; display: flex; align-items: center; gap: 6px; }}
.col-name .row-icon {{ flex-shrink: 0; image-rendering: auto; }}
.res-icon {{ display: block; width: 28px; height: 28px; margin: 0 auto; margin-bottom: 4px; background-size: contain; background-repeat: no-repeat; background-position: center; image-rendering: auto; }}
.col-name small {{ font-weight: normal; color: #6e7681; font-family: monospace; font-size: 10px; display: block; }}
.col-qty {{ width: 64px; text-align: center; }}
.col-days {{ width: 52px; text-align: right; color: #d2a679; }}
.col-res {{ width: 72px; text-align: center; }}
.col-mass {{ width: 80px; text-align: right; color: #ce93d8; font-weight: 600; }}
.qty-input {{
  width: 56px; background: #161b22; color: #c9d1d9;
  border: 1px solid #30363d; border-radius: 4px;
  padding: 3px 5px; font-size: 12px; text-align: center;
}}
.qty-input:focus {{ outline: none; border-color: #58a6ff; background: #1c2128; }}
.qty-input:hover {{ border-color: #58a6ff88; }}
tr:nth-child(even) td {{ background: #0d1117; }}
tr:nth-child(odd) td {{ background: #111820; }}
tr:hover td {{ background: #1c2128 !important; }}
.res-cell.nonzero {{ color: #a5d6a7; font-weight: 700; }}
.res-cell.zero {{ color: #30363d; }}
.res-days.nonzero {{ color: #d2a679; font-weight: 700; }}
.res-days.zero {{ color: #30363d; }}
.res-mass.nonzero {{ color: #ce93d8; font-weight: 700; }}
.res-mass.zero {{ color: #30363d; }}
.subtotal-row td {{
  background: #161b22 !important;
  font-weight: 700; color: #58a6ff;
  border-top: 2px solid #30363d;
}}
.subtotal-label {{ color: #8b949e; font-size: 11px; text-align: right; padding-right: 8px; }}
.subtotal.col-days {{ color: #d2a679; text-align: right; }}
.subtotal.col-res {{ text-align: right; color: #a5d6a7; }}
.subtotal.col-res.zero {{ color: #30363d; }}
.subtotal.col-mass {{ color: #ce93d8; text-align: right; }}

/* Grand total panel fixed at bottom */
#grand-panel {{
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #161b22cc; backdrop-filter: blur(8px);
  border-top: 2px solid #30363d;
  padding: 10px 24px; z-index: 100;
  display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px;
}}
#grand-panel h3 {{ color: #79c0ff; font-size: 0.9em; margin-right: 8px; white-space: nowrap; }}
.grand-res {{
  display: flex; align-items: center; gap: 4px;
  background: #0d1117; border: 1px solid #21262d;
  border-radius: 6px; padding: 4px 8px; min-width: 120px;
  font-size: 12px; cursor: pointer; user-select: none;
}}
.grand-res:active {{ background: #1a2230; }}
.grand-res .res-icon {{ width: 36px; height: 36px; margin: 0; flex-shrink: 0; }}
.res-label {{ color: #8b949e; flex: 1; }}
.res-total {{ color: #a5d6a7; font-weight: 700; min-width: 60px; text-align: right; }}
.res-total.zero {{ color: #30363d; }}
#grand-mass {{
  background: #1a1030; border: 1px solid #7b5ea7;
  border-radius: 6px; padding: 4px 12px;
  font-size: 13px; font-weight: 700;
  color: #ce93d8; white-space: nowrap;
}}
#grand-days {{
  background: #101820; border: 1px solid #5a7a4a;
  border-radius: 6px; padding: 4px 12px;
  font-size: 13px; font-weight: 700;
  color: #d2a679; white-space: nowrap;
}}
#modules-label {{
  display: flex; align-items: center; gap: 6px;
  color: #8b949e; font-size: 12px; white-space: nowrap;
}}
#modules-input {{
  width: 52px; background: #161b22; color: #c9d1d9;
  border: 1px solid #30363d; border-radius: 4px;
  padding: 3px 6px; font-size: 13px; text-align: center;
}}
#modules-input:focus {{ outline: none; border-color: #58a6ff; }}
#grand-parallel {{
  background: #101828; border: 1px solid #3a6a9a;
  border-radius: 6px; padding: 4px 12px;
  font-size: 13px; font-weight: 700;
  color: #79c0ff; white-space: nowrap;
}}
#btn-clear {{
  margin-left: auto; background: #21262d;
  border: 1px solid #30363d; color: #8b949e;
  border-radius: 6px; padding: 5px 14px;
  cursor: pointer; font-size: 12px;
}}
#btn-clear:hover {{ background: #30363d; color: #c9d1d9; }}
#tech-checks {{
  display: flex; flex-direction: column; gap: 3px;
  justify-content: center;
}}
.tech-label {{
  display: flex; align-items: center; gap: 5px;
  color: #c9d1d9; font-size: 12px; cursor: pointer; white-space: nowrap;
  user-select: none;
}}
.tech-label input {{ cursor: pointer; accent-color: #58a6ff; }}
.tech-note {{ color: #8b949e; font-size: 11px; }}
{RES_ICON_CSS}
</style>
</head>
<body>
<h1>Solar Expanse - Build Cost Calculator</h1>
<p style="color:#8b949e;font-size:12px;margin-bottom:16px;">
  Enter quantities - totals update automatically. 1 unit = 1 tonne.</p>

{building_sections_html}

<h2>Spacecraft ({len(spacecraft)})</h2>
<table id="tbl-spacecraft" data-res='{all_res_json}'>
<thead>{header_row(all_res, "Spacecraft")}</thead>
<tbody>
{s_rows}
{subtotal_row(all_res, "Spacecraft subtotal")}
</tbody>
</table>

<!-- Grand total panel -->
<div id="grand-panel">
  <h3>TOTAL</h3>
  {grand_cells}
  <div id="grand-mass">0 t total mass</div>
  <div id="grand-days">0 days build</div>
  <label id="modules-label">
    <span>Construction modules:</span>
    <input type="number" id="modules-input" min="1" value="1">
  </label>
  <div id="grand-parallel">- days parallel</div>
  <div id="tech-checks">
    <label class="tech-label" title="Diamonds tech: -10% build cost">
      <input type="checkbox" id="tech-diamonds"> Diamonds <span class="tech-note">(-10% cost)</span>
    </label>
    <label class="tech-label" title="Mega-scale carbon allotrope application: -10% build time">
      <input type="checkbox" id="tech-carbon"> Mega-scale carbon allotrope <span class="tech-note">(-10% time)</span>
    </label>
  </div>
  <button id="btn-clear">Clear All</button>
</div>

<script>
const ALL_RES = {all_res_json};

function fmt(n) {{
  if (n === 0) return '-';
  return n.toLocaleString('en-US');
}}

function fmtDays(n) {{
  if (n === 0) return '0';
  return n.toLocaleString('en-US');
}}

function recalc() {{
  const grandTotals = {{}};
  ALL_RES.forEach(r => grandTotals[r] = 0);
  let grandMass = 0;
  let grandDays = 0;
  const allJobs = [];  // one entry per unit: its build time in days

  const costMult = document.getElementById('tech-diamonds').checked ? 0.9 : 1.0;
  const timeMult = document.getElementById('tech-carbon').checked  ? 0.9 : 1.0;

  document.querySelectorAll('table[data-res]').forEach(tbl => {{
    const tblRes = JSON.parse(tbl.dataset.res);
    const subtotals = {{}};
    tblRes.forEach(r => subtotals[r] = 0);
    let subDays = 0, subMass = 0;

    tbl.querySelectorAll('tr[data-costs]').forEach(row => {{
      const qty = parseInt(row.querySelector('.qty-input').value) || 0;
      const costs = JSON.parse(row.dataset.costs);
      const time  = parseFloat(row.dataset.time) || 0;

      // Row shows base cost (per unit), not affected by qty
      // Days cell: show base build time (not multiplied)
      const daysCell = row.querySelector('.res-days');
      daysCell.textContent = time > 0 ? fmtDays(time) : '0';
      daysCell.className = 'col-days res-days ' + (time > 0 ? 'nonzero' : 'zero');

      // Resources: row shows per-unit cost, but totals count qty
      let baseRowMass = 0;
      tblRes.forEach(r => {{
        const baseCost = costs[r] || 0;
        const cell = row.querySelector(`.res-cell[data-res="${{r}}"]`);
        if (cell) {{
          cell.textContent = baseCost > 0 ? fmt(baseCost) : '-';
          cell.className = 'col-res res-cell ' + (baseCost > 0 ? 'nonzero' : 'zero');
          subtotals[r] += baseCost * costMult * qty;
        }}
        baseRowMass += baseCost;
        grandTotals[r] = (grandTotals[r] || 0) + baseCost * costMult * qty;
      }});
      subDays += time * timeMult * qty;
      subMass += baseRowMass * costMult * qty;
      grandMass += baseRowMass * costMult * qty;
      if (qty > 0 && time > 0) {{
        for (let i = 0; i < qty; i++) allJobs.push(time * timeMult);
      }}

      // Mass cell: show per-unit mass
      const massCell = row.querySelector('.res-mass');
      massCell.textContent = baseRowMass > 0 ? fmt(baseRowMass) : '0';
      massCell.className = 'col-mass res-mass ' + (baseRowMass > 0 ? 'nonzero' : 'zero');
    }});

    // Subtotal row
    const sub = tbl.querySelector('.subtotal-row');
    if (sub) {{
      const daysEl = sub.querySelector('[data-sum="days"]');
      if (daysEl) daysEl.textContent = fmtDays(subDays);
      tblRes.forEach(r => {{
        const el = sub.querySelector(`[data-sum="${{r}}"]`);
        if (el) {{
          el.textContent = subtotals[r] > 0 ? fmt(subtotals[r]) : '-';
          el.className = 'subtotal col-res ' + (subtotals[r] > 0 ? '' : 'zero');
        }}
      }});
      const massEl = sub.querySelector('[data-sum="mass"]');
      if (massEl) massEl.textContent = fmt(subMass) === '-' ? '0' : fmt(subMass);
    }}

    grandDays += subDays;
  }});

  // Grand totals panel
  ALL_RES.forEach(r => {{
      const el = document.querySelector(`[data-grand="${{r}}"]`);
      if (el) {{
        const v = grandTotals[r] || 0;
        el.textContent = v > 0 ? fmt(v) : '0';
        el.className = 'res-total ' + (v > 0 ? '' : 'zero');
        el.dataset.raw = v;
      }}
    }});
  document.getElementById('grand-mass').textContent =
    fmt(grandMass) + ' t total mass';
  document.getElementById('grand-days').textContent =
    fmtDays(grandDays) + ' days (sequential)';

  const modules = Math.max(1, parseInt(document.getElementById('modules-input').value) || 1);
  // Greedy LPT scheduler: assign each job to the module finishing earliest
  let parallelDays = 0;
  if (allJobs.length > 0) {{
    allJobs.sort((a, b) => b - a);  // longest first
    const finish = new Array(modules).fill(0);
    for (const dur of allJobs) {{
      let minIdx = 0;
      for (let i = 1; i < modules; i++)
        if (finish[i] < finish[minIdx]) minIdx = i;
      finish[minIdx] += dur;
    }}
    parallelDays = Math.max(...finish);
  }}
  const parallelStr = parallelDays > 0
    ? (Number.isInteger(parallelDays) ? parallelDays.toLocaleString('en-US') : parallelDays.toFixed(1))
    : '0';
  document.getElementById('grand-parallel').textContent =
    parallelStr + ' days with ' + modules + ' module' + (modules !== 1 ? 's' : '');
}}

document.addEventListener('input', e => {{
  if (e.target.classList.contains('qty-input')
    || e.target.id === 'modules-input'
    || e.target.id === 'tech-diamonds'
    || e.target.id === 'tech-carbon') recalc();
}});

document.getElementById('btn-clear').addEventListener('click', () => {{
  document.querySelectorAll('.qty-input').forEach(el => el.value = 0);
  recalc();
}});

// Click grand-res to copy raw value to clipboard
document.getElementById('grand-panel').addEventListener('click', e => {{
  const grandRes = e.target.closest('.grand-res');
  if (!grandRes) return;
  const totalEl = grandRes.querySelector('.res-total');
  if (!totalEl) return;
  const raw = totalEl.dataset.raw;
  if (raw === undefined) return;
  const num = parseFloat(raw);
  navigator.clipboard.writeText(num.toString()).then(() => {{
    const label = grandRes.querySelector('.res-label').textContent;
    totalEl.textContent = 'Copied!';
    setTimeout(() => {{ totalEl.textContent = num > 0 ? fmt(num) : '0'; }}, 800);
  }}).catch(() => {{}});
}});

recalc();
</script>
</body>
</html>
"""

out = "index.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Saved: {out}")
print(
    f"  {len(buildings)} buildings, {len(modules)} modules, {len(spacecraft)} spacecraft"
)
