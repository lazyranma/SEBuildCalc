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
with open(DATA_DIR / "launch_vehicle_costs.json", encoding="utf-8") as f:
    launch_vehicle_data = json.load(f)

icons_dir = BASE_DIR / "icons"

ALL_RESOURCES = [
    "metal",
    "raremetal",
    "steel",
    "alloy",
    "chips",
    "plastic",
    "glass",
    "silicon",
    "supply",
    "fuel",
    "hel3",
    "uran",
    "volatile",
    "water",
    "hydrogen",
    "oxygen",
    "nitrogen",
    "noblegas",
    "co2",
    "energy",
    "human",
    "consumergoods",
    "antimatter",
]

UI_TRANSLATIONS = {
    "en-US": {
        "title": "Solar Expanse - Build Cost Calculator",
        "col_name": "Name",
        "col_qty": "Qty",
        "col_days": "Days",
        "col_mass": "Mass",
        "col_mass_unit": "t",
        "subtotal_label": "Subtotal",
        "grand_total": "TOTAL",
        "grand_mass": "total mass",
        "gp_day_seq": {"one": "day (sequential)", "other": "days (sequential)"},
        "gp_day_par": {"one": "day with", "other": "days with"},
        "gp_module": {"one": "module", "other": "modules"},
        "grand_modules_label": "Construction modules:",
        "bonus_section_title": "Research Bonuses",
        "bonus_cost_title": "Build Cost",
        "bonus_speed_title": "Build Speed",
        "bonus_target_all": "ALL",
        "bonus_target_facility": "FACILITIES",
        "bonus_target_lv": "LAUNCH VEHICLES",
        "bonus_target_sc": "SPACECRAFT",
        "btn_clear": "Clear All",
        "copied": "Copied!",
    },
    "de-DE": {
        "title": "Solar Expanse - Baukostenrechner",
        "col_name": "Name",
        "col_qty": "Anz.",
        "col_days": "Tage",
        "col_mass": "Masse",
        "col_mass_unit": "t",
        "subtotal_label": "Zwischensumme",
        "grand_total": "GESAMT",
        "grand_mass": "Gesamtmasse",
        "gp_day_seq": {"one": "Tag (sequenziell)", "other": "Tage (sequenziell)"},
        "gp_day_par": {"one": "Tag mit", "other": "Tage mit"},
        "gp_module": {"one": "Modul", "other": "Modulen"},
        "grand_modules_label": "Baumodule:",
        "bonus_section_title": "Forschungsboni",
        "bonus_cost_title": "Baukosten",
        "bonus_speed_title": "Baugeschwindigkeit",
        "bonus_target_all": "ALLE",
        "bonus_target_facility": "EINRICHTUNGEN",
        "bonus_target_lv": "TRÄGERRAKETEN",
        "bonus_target_sc": "RAUMSCHIFFE",
        "btn_clear": "Alles löschen",
        "copied": "Kopiert!",
    },
    "fr-FR": {
        "title": "Solar Expanse - Calculateur de coûts",
        "col_name": "Nom",
        "col_qty": "Qté",
        "col_days": "Jours",
        "col_mass": "Masse",
        "col_mass_unit": "t",
        "subtotal_label": "Sous-total",
        "grand_total": "TOTAL",
        "grand_mass": "masse totale",
        "gp_day_seq": {"one": "jour (séquentiel)", "other": "jours (séquentiel)"},
        "gp_day_par": {"one": "jour avec", "other": "jours avec"},
        "gp_module": {"one": "module", "other": "modules"},
        "grand_modules_label": "Modules de construction :",
        "bonus_section_title": "Bonus de recherche",
        "bonus_cost_title": "Coût de construction",
        "bonus_speed_title": "Vitesse de construction",
        "bonus_target_all": "TOUT",
        "bonus_target_facility": "INSTALLATIONS",
        "bonus_target_lv": "LANCEURS",
        "bonus_target_sc": "VAISSEAUX",
        "btn_clear": "Tout effacer",
        "copied": "Copié !",
    },
    "es-ES": {
        "title": "Solar Expanse - Calculadora de costes",
        "col_name": "Nombre",
        "col_qty": "Cant.",
        "col_days": "Días",
        "col_mass": "Masa",
        "col_mass_unit": "t",
        "subtotal_label": "Subtotal",
        "grand_total": "TOTAL",
        "grand_mass": "masa total",
        "gp_day_seq": {"one": "día (secuencial)", "other": "días (secuencial)"},
        "gp_day_par": {"one": "día con", "other": "días con"},
        "gp_module": {"one": "módulo", "other": "módulos"},
        "grand_modules_label": "Módulos de construcción:",
        "bonus_section_title": "Bonificaciones de investigación",
        "bonus_cost_title": "Coste de construcción",
        "bonus_speed_title": "Velocidad de construcción",
        "bonus_target_all": "TODO",
        "bonus_target_facility": "INSTALACIONES",
        "bonus_target_lv": "LANZADERAS",
        "bonus_target_sc": "NAVES",
        "btn_clear": "Limpiar todo",
        "copied": "¡Copiado!",
    },
    "pt-BR": {
        "title": "Solar Expanse - Calculadora de custos",
        "col_name": "Nome",
        "col_qty": "Qtd.",
        "col_days": "Dias",
        "col_mass": "Massa",
        "col_mass_unit": "t",
        "subtotal_label": "Subtotal",
        "grand_total": "TOTAL",
        "grand_mass": "massa total",
        "gp_day_seq": {"one": "dia (sequencial)", "other": "dias (sequencial)"},
        "gp_day_par": {"one": "dia com", "other": "dias com"},
        "gp_module": {"one": "módulo", "other": "módulos"},
        "grand_modules_label": "Módulos de construção:",
        "bonus_section_title": "Bônus de pesquisa",
        "bonus_cost_title": "Custo de construção",
        "bonus_speed_title": "Velocidade de construção",
        "bonus_target_all": "TUDO",
        "bonus_target_facility": "INSTALAÇÕES",
        "bonus_target_lv": "LANÇADORES",
        "bonus_target_sc": "NAVES",
        "btn_clear": "Limpar tudo",
        "copied": "Copiado!",
    },
    "ru-RU": {
        "title": "Solar Expanse - Калькулятор стоимости",
        "col_name": "Название",
        "col_qty": "Кол.",
        "col_days": "Дни",
        "col_mass": "Масса",
        "col_mass_unit": "т",
        "subtotal_label": "Промежуточный итог",
        "grand_total": "ИТОГО",
        "grand_mass": "общая масса",
        "gp_day_seq": {
            "one": "день (последовательно)",
            "few": "дня (последовательно)",
            "many": "дней (последовательно)",
        },
        "gp_day_par": {"one": "день с", "few": "дня с", "many": "дней с"},
        "gp_module": {"one": "модулем", "few": "модулями", "many": "модулями"},
        "grand_modules_label": "Строительные модули:",
        "bonus_section_title": "Бонусы исследований",
        "bonus_cost_title": "Стоимость строительства",
        "bonus_speed_title": "Скорость строительства",
        "bonus_target_all": "ВСЁ",
        "bonus_target_facility": "СООРУЖЕНИЯ",
        "bonus_target_lv": "РАКЕТЫ-НОСИТЕЛИ",
        "bonus_target_sc": "КОРАБЛИ",
        "btn_clear": "Очистить всё",
        "copied": "Скопировано!",
    },
    "zh-CN": {
        "title": "Solar Expanse - 建造成本计算器",
        "col_name": "名称",
        "col_qty": "数量",
        "col_days": "天数",
        "col_mass": "质量",
        "col_mass_unit": "吨",
        "subtotal_label": "小计",
        "grand_total": "总计",
        "grand_mass": "总质量",
        "gp_day_seq": {"other": "天（顺序）"},
        "gp_day_par": {"other": "天（使用"},
        "gp_module": {"other": "个模块）"},
        "grand_modules_label": "建造模块：",
        "bonus_section_title": "研究加成",
        "bonus_cost_title": "建造成本",
        "bonus_speed_title": "建造速度",
        "bonus_target_all": "全部",
        "bonus_target_facility": "设施",
        "bonus_target_lv": "运载火箭",
        "bonus_target_sc": "航天器",
        "btn_clear": "全部清除",
        "copied": "已复制！",
    },
    "ja-JP": {
        "title": "Solar Expanse - 建設コスト計算機",
        "col_name": "名称",
        "col_qty": "数量",
        "col_days": "日数",
        "col_mass": "質量",
        "col_mass_unit": "t",
        "subtotal_label": "小計",
        "grand_total": "合計",
        "grand_mass": "総質量",
        "gp_day_seq": {"other": "日（順次）"},
        "gp_day_par": {"other": "日（"},
        "gp_module": {"other": "モジュール）"},
        "grand_modules_label": "建設モジュール：",
        "bonus_section_title": "研究ボーナス",
        "bonus_cost_title": "建設コスト",
        "bonus_speed_title": "建設速度",
        "bonus_target_all": "すべて",
        "bonus_target_facility": "施設",
        "bonus_target_lv": "ロケット",
        "bonus_target_sc": "宇宙船",
        "btn_clear": "すべてクリア",
        "copied": "コピーしました！",
    },
    "ko-KR": {
        "title": "Solar Expanse - 건설 비용 계산기",
        "col_name": "이름",
        "col_qty": "수량",
        "col_days": "일수",
        "col_mass": "질량",
        "col_mass_unit": "t",
        "subtotal_label": "소계",
        "grand_total": "총계",
        "grand_mass": "총 질량",
        "gp_day_seq": {"other": "일 (순차)"},
        "gp_day_par": {"other": "일 ("},
        "gp_module": {"other": "모듈)"},
        "grand_modules_label": "건설 모듈:",
        "bonus_section_title": "연구 보너스",
        "bonus_cost_title": "건설 비용",
        "bonus_speed_title": "건설 속도",
        "bonus_target_all": "전체",
        "bonus_target_facility": "시설",
        "bonus_target_lv": "발사체",
        "bonus_target_sc": "우주선",
        "btn_clear": "모두 지우기",
        "copied": "복사됨!",
    },
}

NATIVE_LANGUAGE_NAMES = {
    "en-US": "English",
    "de-DE": "Deutsch",
    "fr-FR": "Français",
    "es-ES": "Español",
    "pt-BR": "Português",
    "ru-RU": "Русский",
    "zh-CN": "中文",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
}

# Languages that have UI translations available
UI_LOCALES = set(UI_TRANSLATIONS.keys())

loc = {}
_legacy_loc_path = DATA_DIR / "loc_names.txt"
if _legacy_loc_path.exists():
    with open(_legacy_loc_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            k, v = line.split(",", 1)
            loc[k] = v.strip('"')

# Build a lowercase index for case-insensitive lookups
_loc_lower = {k.lower(): v for k, v in loc.items()}


def _loc_get(key, default=""):
    """Get localized name, trying exact match then case-insensitive fallback."""
    if not key:
        return default
    if key in loc:
        return loc[key]
    return _loc_lower.get(key.lower(), default)


def _sentence_case(s):
    """Convert to sentence case: first letter uppercase, rest lowercase."""
    if not s:
        return s
    return s[0].upper() + s[1:].lower()


# Game localization keys for facility type category tabs (from EFacilityType enum)
_FACILITY_TYPE_LOC_KEY = {
    "Modules": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Modules",
    "Habitation": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Habitation",
    "Power": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Power",
    "Mining": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Mining",
    "Production": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Production",
    "Launch Facilities": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.LaunchFacilities",
    "Terraformation": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Terraformation",
    "Other": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Other",
    "Segments": "Tooltip.ChoseFacilityWindow.FaciltyTypeTab.Segments",
}

# Game localization keys for section headers (PlanMissionWindow step headers)
_SECTION_LOC_KEY = {
    "launch_vehicles": "Game.UI.Windows.Windows.PlanMissionWindow.Header.SelectLaunchVehicle2",
    "spacecraft": "Game.UI.Windows.Windows.PlanMissionWindow.Header.SelectRocket2",
}

# Game localization keys for research names
_RESEARCH_LOC_KEY = {
    "diamondoids": "research_mat_diamondoid_Title",
    "carbon_allotrope": "research_mat_fibre4_Title",
}


def _cat_display(cat):
    """Get sentence-case display name for a category from game loc."""
    loc_key = _FACILITY_TYPE_LOC_KEY.get(cat, "")
    name = _loc_get(loc_key) or cat
    return _sentence_case(name)


def _section_display(section_id):
    """Get sentence-case display name for a section from game loc."""
    loc_key = _SECTION_LOC_KEY.get(section_id, "")
    name = _loc_get(loc_key) or section_id.replace("_", " ")
    return _sentence_case(name)


# Phase A: Load multiple locale files
# Map game locale codes to standard BCP 47 codes where they differ
_GAME_LOCALE_MAP = {
    "jp-JP": "ja-JP",
    "ko-KO": "ko-KR",
}
ALL_GAME_LOC = {}
AVAILABLE_LOCALES = []

try:
    locales_path = DATA_DIR / "locales.json"
    if locales_path.exists():
        with open(locales_path, encoding="utf-8") as f:
            locale_codes = json.load(f)
        for lc in locale_codes:
            loc_path = DATA_DIR / f"loc_names_{lc}.txt"
            if loc_path.exists():
                locale_dict = {}
                with open(loc_path, encoding="utf-8") as lf:
                    for line in lf:
                        line = line.strip()
                        if not line or "," not in line:
                            continue
                        k, v = line.split(",", 1)
                        locale_dict[k] = v.strip('"')
                mapped = _GAME_LOCALE_MAP.get(lc, lc)
                ALL_GAME_LOC[mapped] = locale_dict
        AVAILABLE_LOCALES = [
            _GAME_LOCALE_MAP.get(lc, lc)
            for lc in locale_codes
            if _GAME_LOCALE_MAP.get(lc, lc) in ALL_GAME_LOC
        ]
    if not AVAILABLE_LOCALES:
        # Fallback: use existing loc as en-US only
        ALL_GAME_LOC = {"en-US": loc}
        AVAILABLE_LOCALES = ["en-US"]
except Exception:
    ALL_GAME_LOC = {"en-US": loc}
    AVAILABLE_LOCALES = ["en-US"]

# Intersect with locales that have UI translations
AVAILABLE_LOCALES = [l for l in AVAILABLE_LOCALES if l in UI_LOCALES]
if not AVAILABLE_LOCALES:
    AVAILABLE_LOCALES = ["en-US"]

# Populate the global 'loc' dict from en-US game locale so existing code
# (_is_buildable_id, _loc_get, display functions) continues to work.
if "en-US" in ALL_GAME_LOC and ALL_GAME_LOC["en-US"]:
    loc = ALL_GAME_LOC["en-US"]
    _loc_lower = {k.lower(): v for k, v in loc.items()}
elif not loc:
    # No data at all — pick the first available game locale as fallback
    for lc in AVAILABLE_LOCALES:
        if lc in ALL_GAME_LOC and ALL_GAME_LOC[lc]:
            loc = ALL_GAME_LOC[lc]
            _loc_lower = {k.lower(): v for k, v in loc.items()}
            break

# Build resource_id -> loc_key mapping for resource name lookups in GAME_LOC
resource_loc_keys = {}
for rid in ALL_RESOURCES:
    loc_key = f"id_resource_{rid}"
    if "en-US" in ALL_GAME_LOC and loc_key in ALL_GAME_LOC["en-US"]:
        resource_loc_keys[rid] = loc_key
    else:
        resource_loc_keys[rid] = None  # fallback to RESOURCE_NAMES

print(f"Available locales: {AVAILABLE_LOCALES}")

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
# The game stores unlocks in separate dictionaries per EActionUnlock type.
_RESEARCH_UNLOCK_FACILITY = set()
_RESEARCH_UNLOCK_FACILITY_LOWER = set()
_RESEARCH_UNLOCK_VEHICLE = set()
_RESEARCH_UNLOCK_VEHICLE_LOWER = set()
_RESEARCH_UNLOCK_SPACECRAFT = set()
_RESEARCH_UNLOCK_SPACECRAFT_LOWER = set()
try:
    with open(DATA_DIR / "research_unlocks.json", encoding="utf-8") as f:
        research_data = json.load(f)
    _RESEARCH_UNLOCK_FACILITY = set(research_data.get("unlocked_facilities", []))
    _RESEARCH_UNLOCK_FACILITY_LOWER = {u.lower() for u in _RESEARCH_UNLOCK_FACILITY}
    _RESEARCH_UNLOCK_VEHICLE = set(research_data.get("unlocked_vehicles", []))
    _RESEARCH_UNLOCK_VEHICLE_LOWER = {u.lower() for u in _RESEARCH_UNLOCK_VEHICLE}
    _RESEARCH_UNLOCK_SPACECRAFT = set(research_data.get("unlocked_spacecraft", []))
    _RESEARCH_UNLOCK_SPACECRAFT_LOWER = {u.lower() for u in _RESEARCH_UNLOCK_SPACECRAFT}
    print(
        f"Loaded research unlocks: "
        f"{len(_RESEARCH_UNLOCK_FACILITY)} facilities, "
        f"{len(_RESEARCH_UNLOCK_VEHICLE)} vehicles, "
        f"{len(_RESEARCH_UNLOCK_SPACECRAFT)} spacecraft"
    )
except FileNotFoundError:
    print(
        "ERROR: research_unlocks.json not found. Run extract_research.py first.",
        file=sys.stderr,
    )
    sys.exit(1)

# Load research bonuses for build cost/time discounts
_RESEARCH_BONUSES = []
_RESEARCH_TREE = {}
try:
    with open(DATA_DIR / "research_bonuses.json", encoding="utf-8") as f:
        _RESEARCH_BONUSES = json.load(f)
    print(f"Loaded {len(_RESEARCH_BONUSES)} research bonuses")
except FileNotFoundError:
    print("WARNING: research_bonuses.json not found — no research bonuses will be shown")

try:
    with open(DATA_DIR / "research_tree.json", encoding="utf-8") as f:
        _RESEARCH_TREE = json.load(f)
    print(f"Loaded research tree with {len(_RESEARCH_TREE)} nodes")
except FileNotFoundError:
    print("WARNING: research_tree.json not found")

# Compute transitive dependency closures for bonus research.
# For each bonus research, compute all bonus-granting ancestors
# (traversing through non-bonus intermediates).
_bonus_ids = {b["id"] for b in _RESEARCH_BONUSES}
_BONUS_TRANSITIVE_REQS = {}  # id -> list of bonus-granting ancestor ids

for bonus in _RESEARCH_BONUSES:
    bid = bonus["id"]
    visited = set()
    all_ancestors = []
    queue = list(bonus.get("requirements", []))
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        if current in _bonus_ids:
            all_ancestors.append(current)
        # Continue traversing through non-bonus intermediates
        reqs = _RESEARCH_TREE.get(current, [])
        for r in reqs:
            if r not in visited:
                queue.append(r)
    _BONUS_TRANSITIVE_REQS[bid] = all_ancestors

# Group bonuses by bonus type
_COST_BONUSES = [b for b in _RESEARCH_BONUSES if b["bonus"] == "BuildCost"]
_SPEED_BONUSES = [b for b in _RESEARCH_BONUSES if b["bonus"] == "BuildSpeed"]

# Build loc key for each bonus research
_bonus_loc_keys = {}
for b in _RESEARCH_BONUSES:
    _bonus_loc_keys[b["id"]] = b["id"] + "_Title"

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
        return fid in _RESEARCH_UNLOCK_FACILITY_LOWER  # locked: needs research

    # Fallback: old Python extraction without isLocked — suffix proxy
    if fid in _RESEARCH_UNLOCK_FACILITY_LOWER:
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
    # Filter out fake-for-facility, cycle-mission, and cheat spacecraft
    if v.get("fakeForFacility"):
        continue
    if v.get("forCycleMission"):
        continue

    display_name = v.get("display_name")
    if not display_name:
        text_key = v.get("text_key", "")
        display_name = _loc_get(text_key) or _loc_get(k)
    if display_name:
        # Buildability: same logic as LVs — available if not locked, or if
        # locked but unlocked via research.
        is_locked = v.get("isLocked", False)
        is_buildable = not is_locked or k.lower() in _RESEARCH_UNLOCK_SPACECRAFT_LOWER
        if is_buildable:
            v["display_name"] = display_name
            spacecraft[k] = v

# Process dedicated launch vehicle data (from launch_vehicle_costs.json)
launch_vehicles = {}
for k, v in launch_vehicle_data.items():
    # Filter out fake-for-facility, cycle-mission, and cheat LVs
    if v.get("fakeForFacility"):
        continue
    if v.get("forCycleMission"):
        continue

    display_name = v.get("display_name")
    if not display_name:
        text_key = v.get("text_key", "")
        display_name = _loc_get(text_key) or _loc_get(k)
    if display_name:
        # Buildability: same logic as facilities — available if not locked, or if
        # locked but unlocked via research.
        is_locked = v.get("isLocked", False)
        is_buildable = not is_locked or k.lower() in _RESEARCH_UNLOCK_VEHICLE_LOWER
        if is_buildable:
            v["display_name"] = display_name
            launch_vehicles[k] = v


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
    "Other",
    "Segments",
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
    list(buildings.values())
    + list(modules.values())
    + list(launch_vehicles.values())
    + list(spacecraft.values())
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
_launch_vehicle_icon_data = {}  # launch_vehicle_id -> base64 PNG
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
        # Pre-load launch vehicle icons
        for lid, rel_path in icon_map.get("launch_vehicles", {}).items():
            b64 = icon_b64(rel_path)
            if b64:
                _launch_vehicle_icon_data[lid] = b64
        # Pre-load spacecraft icons
        for sid, rel_path in icon_map.get("spacecraft", {}).items():
            b64 = icon_b64(rel_path)
            if b64:
                _spacecraft_icon_data[sid] = b64
        print(
            f"Loaded {len(_facility_icon_data)} facility icons, "
            f"{len(_launch_vehicle_icon_data)} launch vehicle icons, "
            f"{len(_spacecraft_icon_data)} spacecraft icons"
        )
except Exception as e:
    print(f"Note: icon_map.json not loaded ({e})")


def facility_icon_img(fid, size=48):
    """Return an <img> tag for a facility/spacecraft/launch-vehicle icon, or empty string."""
    b64 = (
        _facility_icon_data.get(fid)
        or _launch_vehicle_icon_data.get(fid)
        or _spacecraft_icon_data.get(fid)
    )
    if b64:
        return (
            f'<img class="row-icon" src="data:image/png;base64,{b64}" '
            f'style="max-width:{size}px;max-height:{size}px" alt="">'
        )
    return ""


def header_row(resources, name_col="Name", name_loc_key="col_name"):
    cells = [
        f'<th class="col-name" data-loc-key="{name_loc_key}">{name_col}</th>',
        '<th class="col-qty" data-loc-key="col_qty">Qty</th>',
        '<th class="col-days" data-loc-key="col_days">Days</th>',
    ]
    for r in resources:
        short = r.replace("id_resource_", "")
        b64 = icon_data.get(r)
        # Use game loc name, fall back to resource ID
        res_name = _loc_get(f"id_resource_{r}") or r
        img = (
            f'<span class="res-icon ric-{short}" title="{res_name}"></span>'
            if b64
            else ""
        )
        cells.append(
            f'<th class="col-res" data-res="{r}">{img}<span>{res_name}</span></th>'
        )
    cells.append(
        '<th class="col-mass"><span data-loc-key="col_mass">Mass</span><br><small data-loc-key="col_mass_unit">(t)</small></th>'
    )
    return "<tr>" + "".join(cells) + "</tr>"


def build_rows(entries, resources, key_fn, display_fn, time_fn, loc_key_fn=None):
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
        # Loc key attributes for multilingual support
        if loc_key_fn:
            loc_name_key, loc_name_fallback = loc_key_fn(key, v)
        else:
            loc_name_key, loc_name_fallback = key, ""
        loc_attrs = f' data-loc-name-key="{htmllib.escape(loc_name_key, quote=True)}"'
        if loc_name_fallback:
            loc_attrs += f' data-loc-name-fallback="{htmllib.escape(loc_name_fallback, quote=True)}"'
        row = (
            f"<tr data-costs='{costs_json}' data-time=\"{time_val}\" data-id=\"{htmllib.escape(key, quote=True)}\" data-resources='{json.dumps(list(res.keys()))}'{loc_attrs}>"
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


def subtotal_row(resources, label="Subtotal", loc_key=""):
    loc_attr = f' data-loc-key="{loc_key}"' if loc_key else ""
    cells = [
        f'<td class="subtotal-label" colspan="2"{loc_attr}>{label}</td>',
        '<td class="subtotal col-days" data-sum="days">0</td>',
    ]
    for r in resources:
        cells.append(f'<td class="subtotal col-res" data-sum="{r}">0</td>')
    cells.append('<td class="subtotal col-mass" data-sum="mass">0</td>')
    return "<tr class='subtotal-row'>" + "".join(cells) + "</tr>"


def lv_display(k):
    return launch_vehicles[k].get("display_name", k).upper()


def lv_loc_key(k, v):
    """Return (loc_name_key, loc_name_fallback) for a launch vehicle."""
    text_key = v.get("text_key", "")
    if text_key:
        return (k, text_key)
    return (k, "")


lv_rows = build_rows(
    launch_vehicles,
    all_res,
    lambda k: k,
    lv_display,
    lambda v: v.get("build_time_days", 0),
    loc_key_fn=lv_loc_key,
)


def sc_display(k):
    return spacecraft[k].get("display_name", k).upper()


def sc_loc_key(k, v):
    """Return (loc_name_key, loc_name_fallback) for a spacecraft."""
    text_key = v.get("text_key", "")
    if text_key:
        return (k, text_key)
    return (k, "")


s_rows = build_rows(
    spacecraft,
    all_res,
    lambda k: k,
    sc_display,
    lambda v: v.get("build_time_days", 0),
    loc_key_fn=sc_loc_key,
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
    cat_game_key = _FACILITY_TYPE_LOC_KEY.get(cat, "")
    cat_display = _cat_display(cat)
    cat_rows = build_rows(
        cat_buildings,
        all_res,
        lambda k: k,
        lambda k: _loc_get(k, k).upper(),
        lambda v: v.get("build_time_days", 0),
        loc_key_fn=lambda k, v: (k, ""),
    )
    building_sections_html += f"""<h2 data-cat="{cat}" data-count="{len(cat_buildings)}" data-loc-key="{cat_game_key}">{cat_display} ({len(cat_buildings)})</h2>
<table data-res='{cat_res_json}'>
<thead>{header_row(all_res)}</thead>
<tbody>
{cat_rows}
{subtotal_row(all_res, "Subtotal", loc_key="subtotal_label")}
</tbody>
</table>
"""

# Grand total resource cells for the bottom panel
grand_cells = ""
for r in all_res:
    short = r.replace("id_resource_", "")
    res_name = _loc_get(f"id_resource_{r}") or r
    img = f'<span class="res-icon ric-{short}" title="{res_name}"></span>'
    grand_cells += (
        f'<div class="grand-res" id="grand-{r}">'
        f'  {img}<span class="res-label">{res_name}</span>'
        f'  <span class="res-total" data-grand="{r}">0</span>'
        f"</div>"
    )

all_res_json = json.dumps(all_res)

# Prepare locale data for embedding in HTML
_available_locales_json = json.dumps(AVAILABLE_LOCALES)
_game_loc_for_js = {l: ALL_GAME_LOC[l] for l in AVAILABLE_LOCALES if l in ALL_GAME_LOC}
_game_loc_json = json.dumps(_game_loc_for_js)
_ui_loc_json = json.dumps(
    {l: UI_TRANSLATIONS[l] for l in AVAILABLE_LOCALES if l in UI_TRANSLATIONS}
)
_resource_loc_keys_json = json.dumps(resource_loc_keys)
_native_names_json = json.dumps(NATIVE_LANGUAGE_NAMES)

# Build research bonuses HTML section
_research_bonuses_html = ""
if _RESEARCH_BONUSES:
    _research_checks_html = ""

    def _bonus_targets_display(targets):
        parts = []
        for t in targets:
            if t == "All":
                parts.append("ALL")
            elif t == "Facility":
                parts.append("FACILITIES")
            elif t == "LV":
                parts.append("LAUNCH VEHICLES")
            elif t == "SC":
                parts.append("SPACECRAFT")
            elif t == "SComponent" or t == "RD":
                continue
            else:
                name = _loc_get(t, t).upper()
                if len(name) > 25:
                    name = name[:22] + "..."
                parts.append(name)
        return ", ".join(parts) if parts else "ALL"

    if _COST_BONUSES:
        _research_checks_html += '<div class="bonus-group"><h4 class="bonus-group-title" data-loc-key="bonus_cost_title">Build Cost</h4>'
        for b in _COST_BONUSES:
            bid = b["id"]
            pct = abs(b["bonusParameter"])
            targets_display = _bonus_targets_display(b["targets"])
            targets_json = json.dumps(b["targets"])
            name = _loc_get(bid + "_Title") or bid
            loc_key = bid + "_Title"
            _research_checks_html += f'''
            <label class="tech-label">
              <input type="checkbox" class="research-check" data-research-id="{bid}">
              <span data-loc-key="{loc_key}">{name.upper()}</span>
              <span class="tech-note" data-targets='{targets_json}' data-pct="{pct:.0f}">(-{pct:.0f}% | {targets_display})</span>
            </label>'''
        _research_checks_html += '</div>'

    if _SPEED_BONUSES:
        _research_checks_html += '<div class="bonus-group"><h4 class="bonus-group-title" data-loc-key="bonus_speed_title">Build Speed</h4>'
        for b in _SPEED_BONUSES:
            bid = b["id"]
            pct = abs(b["bonusParameter"])
            targets_display = _bonus_targets_display(b["targets"])
            targets_json = json.dumps(b["targets"])
            name = _loc_get(bid + "_Title") or bid
            loc_key = bid + "_Title"
            _research_checks_html += f'''
            <label class="tech-label">
              <input type="checkbox" class="research-check" data-research-id="{bid}">
              <span data-loc-key="{loc_key}">{name.upper()}</span>
              <span class="tech-note" data-targets='{targets_json}' data-pct="{pct:.0f}">(-{pct:.0f}% | {targets_display})</span>
            </label>'''
        _research_checks_html += '</div>'

    _research_bonuses_html = f'''<details id="research-bonuses-section" class="research-section">
<summary><span data-loc-key="bonus_section_title">Research Bonuses</span> <span id="bonus-count">(0 active)</span></summary>
<div class="research-checks">
{_research_checks_html}
</div>
</details>'''

# Build launch vehicles section HTML (only if there are launch vehicles)
_launch_vehicles_display = _section_display("launch_vehicles")
launch_vehicles_section_html = ""
if launch_vehicles:
    lv_game_key = _SECTION_LOC_KEY["launch_vehicles"]
    launch_vehicles_section_html = f"""<h2 data-count="{len(launch_vehicles)}" data-loc-key="{lv_game_key}">{_launch_vehicles_display} ({len(launch_vehicles)})</h2>
<table id="tbl-launch-vehicles" data-res='{all_res_json}'>
<thead>{header_row(all_res, _launch_vehicles_display, _SECTION_LOC_KEY["launch_vehicles"])}</thead>
<tbody>
{lv_rows}
{subtotal_row(all_res, "Subtotal", loc_key="subtotal_label")}
</tbody>
</table>
"""

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
  font-size: 12.5px; cursor: pointer; user-select: none;
}}
.grand-res:active {{ background: #1a2230; }}
.grand-res .res-icon {{ width: 28px; height: 28px; margin: 0; flex-shrink: 0; }}
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
.research-section {{ margin: 12px 0 8px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 8px 16px; }}
.research-section summary {{ color: #79c0ff; cursor: pointer; font-size: 15px; font-weight: 600; padding: 4px 0; user-select: none; }}
.research-section summary:hover {{ color: #58a6ff; }}
.research-checks {{ display: flex; flex-wrap: wrap; gap: 16px; padding: 8px 0; }}
.bonus-group {{ display: flex; flex-direction: column; gap: 3px; min-width: 250px; }}
.bonus-group-title {{ color: #79c0ff; font-size: 13px; font-weight: 600; margin: 0 0 2px; }}
.tech-label {{
  display: flex; align-items: center; gap: 5px;
  color: #c9d1d9; font-size: 12px; cursor: pointer; white-space: nowrap;
  user-select: none;
}}
.tech-label input {{ cursor: pointer; accent-color: #58a6ff; }}
.tech-note {{ color: #8b949e; font-size: 11px; }}
.icon-link {{ color:#8b949e; display:flex; align-items:center; opacity:0.7; transition:opacity 0.15s,color 0.15s; }}
.icon-link:hover {{ opacity:1; color:#c9d1d9; }}
{RES_ICON_CSS}
</style>
</head>
<body>
<div style="display:flex; justify-content:flex-end; align-items:center; gap:8px; margin-bottom:8px;">
  <a href="https://github.com/lazyranma/SEBuildCalc" target="_blank" rel="noopener" title="GitHub repository" class="icon-link"><svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></a>
  <a href="https://discord.com/channels/1278330334982967468/1509942881316769884" target="_blank" rel="noopener" title="Discord" class="icon-link"><svg width="18" height="18" viewBox="0 0 127.14 96.36" fill="currentColor"><path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg></a>
  <label for="lang-select" style="color:#8b949e; font-size:12px;">Language:</label>
  <select id="lang-select" style="background:#161b22; color:#c9d1d9; border:1px solid #30363d; border-radius:4px; padding:3px 8px; font-size:12px;"></select>
</div>
<h1 data-loc-key="title">Solar Expanse - Build Cost Calculator</h1>
{_research_bonuses_html}

{building_sections_html}
{launch_vehicles_section_html}
<h2 data-count="{len(spacecraft)}" data-loc-key="{_SECTION_LOC_KEY["spacecraft"]}">{_section_display("spacecraft")} ({len(spacecraft)})</h2>
<table id="tbl-spacecraft" data-res='{all_res_json}'>
<thead>{header_row(all_res, _section_display("spacecraft"), _SECTION_LOC_KEY["spacecraft"])}</thead>
<tbody>
{s_rows}
{subtotal_row(all_res, "Subtotal", loc_key="subtotal_label")}
</tbody>
</table>

<!-- Grand total panel -->
<div id="grand-panel">
  <h3 data-loc-key="grand_total">TOTAL</h3>
  {grand_cells}
  <div id="grand-mass">0 t total mass</div>
  <div id="grand-days">0 days build</div>
  <label id="modules-label">
    <span data-loc-key="grand_modules_label">Construction modules:</span>
    <input type="number" id="modules-input" min="1" value="1">
  </label>
  <div id="grand-parallel">- days parallel</div>
  <button id="btn-toggle-bonuses" style="background:#1a2332; border:1px solid #3a6a9a; color:#79c0ff; border-radius:6px; padding:5px 10px; cursor:pointer; font-size:12px; white-space:nowrap;" data-loc-key="bonus_section_title">Research Bonuses</button>
  <button id="btn-clear" data-loc-key="btn_clear">Clear All</button>
</div>

<script>
const ALL_RES = {all_res_json};
const AVAILABLE_LOCALES = {_available_locales_json};
const GAME_LOC = {_game_loc_json};
const UI_LOC = {_ui_loc_json};
const RESOURCE_LOC_KEYS = {_resource_loc_keys_json};
const NATIVE_NAMES = {_native_names_json};
const FACILITY_TYPE_LOC_KEYS = {json.dumps(_FACILITY_TYPE_LOC_KEY)};
const SECTION_LOC_KEYS = {json.dumps(_SECTION_LOC_KEY)};
const RESEARCH_BONUSES = {json.dumps(_RESEARCH_BONUSES)};
const BONUS_TRANSITIVE_REQS = {json.dumps(_BONUS_TRANSITIVE_REQS)};
const BONUS_LOC_KEYS = {json.dumps(_bonus_loc_keys)};

let currentLocale = 'en-US';

function toSentenceCase(s) {{
  if (!s) return s;
  return s[0].toUpperCase() + s.slice(1).toLowerCase();
}}

function fmt(n) {{
  if (n === 0) return '-';
  return n.toLocaleString('en-US');
}}

function fmtDays(n) {{
  if (n === 0) return '0';
  return n.toLocaleString('en-US');
}}

// Get UI translation
function t(key, locale) {{
  const loc = UI_LOC[locale];
  if (loc && loc[key] !== undefined) return loc[key];
  const enLoc = UI_LOC['en-US'];
  if (enLoc && enLoc[key] !== undefined) return enLoc[key];
  return key;
}}

// Get localized game content name
const GAME_LOC_LOWER = {{}};
for (const [lc, dict] of Object.entries(GAME_LOC)) {{
  const lowerDict = {{}};
  for (const [k, v] of Object.entries(dict)) lowerDict[k.toLowerCase()] = v;
  GAME_LOC_LOWER[lc] = lowerDict;
}}

function getGameLocName(locKey, locale) {{
  if (!locKey) return '';
  const loc = GAME_LOC[locale];
  if (loc && loc[locKey]) return loc[locKey];
  const locLower = GAME_LOC_LOWER[locale];
  if (locLower && locLower[locKey.toLowerCase()]) return locLower[locKey.toLowerCase()];
  const enLoc = GAME_LOC['en-US'];
  if (enLoc && enLoc[locKey]) return enLoc[locKey];
  const enLocLower = GAME_LOC_LOWER['en-US'];
  if (enLocLower && enLocLower[locKey.toLowerCase()]) return enLocLower[locKey.toLowerCase()];
  return locKey;
}}

function pluralize(key, count, locale) {{
  const forms = UI_LOC[locale]?.[key] || UI_LOC['en-US']?.[key];
  if (!forms) return '';
  const cat = new Intl.PluralRules(locale).select(Math.abs(count));
  return forms[cat] || forms.other || '';
}}

function handleResearchCheck(e) {{
  if (!e.target.classList.contains('research-check')) return;
  const researchId = e.target.dataset.researchId;
  if (!researchId) return;

  if (e.target.checked) {{
    checkAncestors(researchId);
  }} else {{
    uncheckDescendants(researchId);
  }}
  recalc();
}}

function checkAncestors(researchId) {{
  const reqs = BONUS_TRANSITIVE_REQS[researchId];
  if (!reqs) return;
  for (const reqId of reqs) {{
    const cb = document.querySelector(`.research-check[data-research-id="${{reqId}}"]`);
    if (cb && !cb.checked) {{
      cb.checked = true;
      checkAncestors(reqId);
    }}
  }}
}}

function uncheckDescendants(researchId) {{
  document.querySelectorAll('.research-check:checked').forEach(cb => {{
    const otherId = cb.dataset.researchId;
    if (!otherId || otherId === researchId) return;
    const reqs = BONUS_TRANSITIVE_REQS[otherId];
    if (!reqs) return;
    if (reqs.includes(researchId)) {{
      cb.checked = false;
      uncheckDescendants(otherId);
    }}
  }});
}}

function getActiveBonuses() {{
  const active = {{}};
  for (const b of RESEARCH_BONUSES) {{
    const cb = document.querySelector(`.research-check[data-research-id="${{b.id}}"]`);
    if (cb && cb.checked) {{
      if (!active[b.bonus]) active[b.bonus] = [];
      active[b.bonus].push(b);
    }}
  }}
  return active;
}}

function appliesTo(targets, rowId) {{
  if (!rowId || !targets || !targets.length) return false;
  for (const t of targets) {{
    if (t === 'All') return true;
    if (t === 'Facility' && (rowId.startsWith('build_') || rowId.startsWith('module_'))) return true;
    if (t === 'LV' && (rowId.startsWith('lv_') || rowId.toLowerCase().startsWith('id_rocket_'))) return true;
    if (t === 'SC' && rowId.startsWith('spacecraft_')) return true;
    if (t.toLowerCase() === rowId.toLowerCase()) return true;
  }}
  return false;
}}

function computeRowMultipliers(rowId, activeBonuses) {{
  let costSum = 0;
  let timeSum = 0;
  if (activeBonuses.BuildCost) {{
    for (const b of activeBonuses.BuildCost) {{
      if (appliesTo(b.targets, rowId)) {{
        costSum += Math.abs(b.bonusParameter);
      }}
    }}
  }}
  if (activeBonuses.BuildSpeed) {{
    for (const b of activeBonuses.BuildSpeed) {{
      if (appliesTo(b.targets, rowId)) {{
        timeSum += Math.abs(b.bonusParameter);
      }}
    }}
  }}
  return {{ costMult: (100 - costSum) / 100, timeMult: (100 - timeSum) / 100 }};
}}

function recalc() {{
  const locale = document.documentElement.lang || currentLocale;
  const grandTotals = {{}};
  ALL_RES.forEach(r => grandTotals[r] = 0);
  let grandMass = 0;
  let grandDays = 0;
  const allJobs = [];  // one entry per unit: its build time in days

  const activeBonuses = getActiveBonuses();

  document.querySelectorAll('table[data-res]').forEach(tbl => {{
    const tblRes = JSON.parse(tbl.dataset.res);
    const subtotals = {{}};
    tblRes.forEach(r => subtotals[r] = 0);
    let subDays = 0, subMass = 0;

    tbl.querySelectorAll('tr[data-costs]').forEach(row => {{
      const qty = parseInt(row.querySelector('.qty-input').value) || 0;
      const costs = JSON.parse(row.dataset.costs);
      const time  = parseFloat(row.dataset.time) || 0;
      const rowId = row.dataset.id || '';
      const {{ costMult, timeMult }} = computeRowMultipliers(rowId, activeBonuses);

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
    fmt(grandMass) + ' t ' + t('grand_mass', locale);
  document.getElementById('grand-days').textContent =
    fmtDays(grandDays) + ' ' + pluralize('gp_day_seq', grandDays, locale);

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
    parallelStr + ' ' + pluralize('gp_day_par', parallelDays, locale) + ' ' + modules + ' ' + pluralize('gp_module', modules, locale);

  // Update bonus count
  const countEl = document.getElementById('bonus-count');
  if (countEl) {{
    const checkedCount = document.querySelectorAll('.research-check:checked').length;
    countEl.textContent = '(' + checkedCount + ' active)';
  }}
}}

document.addEventListener('input', e => {{
  if (e.target.classList.contains('qty-input')
    || e.target.id === 'modules-input') recalc();
}});

document.addEventListener('change', e => {{
  if (e.target.classList.contains('research-check')) {{
    handleResearchCheck(e);
  }}
}});

document.getElementById('btn-clear').addEventListener('click', () => {{
  document.querySelectorAll('.qty-input').forEach(el => el.value = 0);
  recalc();
}});

document.getElementById('btn-toggle-bonuses').addEventListener('click', () => {{
  const section = document.getElementById('research-bonuses-section');
  if (section) {{
    section.open = !section.open;
    section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}
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
  const locale = document.documentElement.lang || currentLocale;
  navigator.clipboard.writeText(num.toString()).then(() => {{
    totalEl.textContent = t('copied', locale);
    setTimeout(() => {{ totalEl.textContent = num > 0 ? fmt(num) : '0'; }}, 800);
  }}).catch(() => {{}});
}});

// === Language support ===

// Detect best locale from browser
function detectLocale() {{
  // Check localStorage first
  const stored = localStorage.getItem('se-locale');
  if (stored && AVAILABLE_LOCALES.includes(stored)) return stored;

  // Try exact match with browser language
  const browserLang = navigator.language || 'en-US';
  if (AVAILABLE_LOCALES.includes(browserLang)) return browserLang;

  // Try primary language match
  const primary = browserLang.split('-')[0].toLowerCase();
  for (const loc of AVAILABLE_LOCALES) {{
    if (loc.toLowerCase().startsWith(primary)) return loc;
  }}

  // Fallback to en-US, or first available
  return AVAILABLE_LOCALES.includes('en-US') ? 'en-US' : AVAILABLE_LOCALES[0];
}}

function updateBonusNotes(locale) {{
  document.querySelectorAll('.tech-note[data-targets]').forEach(el => {{
    const targets = JSON.parse(el.dataset.targets);
    const pct = el.dataset.pct;
    const names = targets.map(t => {{
      if (t === 'All') return t('bonus_target_all', locale);
      if (t === 'Facility') return t('bonus_target_facility', locale);
      if (t === 'LV') return t('bonus_target_lv', locale);
      if (t === 'SC') return t('bonus_target_sc', locale);
      if (t === 'SComponent' || t === 'RD') return null;
      // Specific item ID — use game loc and uppercase
      const name = getGameLocName(t, locale);
      return name ? name.toUpperCase() : null;
    }}).filter(Boolean);
    el.textContent = '(-' + pct + '% | ' + names.join(', ') + ')';
  }});
}}

// Apply locale to entire page
function applyLocale(locale) {{
  currentLocale = locale;
  // Update html lang attribute
  document.documentElement.lang = locale;

  // Update all elements with data-loc-key
  document.querySelectorAll('[data-loc-key]').forEach(el => {{
    const key = el.dataset.locKey;
    let translated = t(key, locale);
    // Fall back to game loc if UI loc doesn't have the key
    if (translated === key) {{
      const gameName = getGameLocName(key, locale);
      if (gameName !== key) translated = gameName;
    }}
    if (!el.querySelector('[data-loc-key]')) {{
      el.textContent = translated;
    }}
  }});

  // Update column mass small element (has its own data-loc-key)
  document.querySelectorAll('th.col-mass small[data-loc-key]').forEach(small => {{
    small.textContent = '(' + t('col_mass_unit', locale) + ')';
  }});

  // Update category and section headings using game loc keys
  document.querySelectorAll('h2[data-cat]').forEach(h2 => {{
    const count = h2.dataset.count;
    const locKey = h2.dataset.locKey;
    const name = getGameLocName(locKey, locale);
    h2.textContent = toSentenceCase(name) + ' (' + count + ')';
  }});
  document.querySelectorAll('h2[data-count]:not([data-cat])').forEach(h2 => {{
    const count = h2.dataset.count || '';
    const locKey = h2.dataset.locKey;
    const name = getGameLocName(locKey, locale);
    h2.textContent = toSentenceCase(name) + (count ? ' (' + count + ')' : '');
  }});

  // Update row display names (game content) - uppercase for consistency
  document.querySelectorAll('tr[data-loc-name-key]').forEach(row => {{
    const locKey = row.dataset.locNameKey;
    const fallbackKey = row.dataset.locNameFallback || '';
    let name = getGameLocName(locKey, locale);
    if (!name && fallbackKey) name = getGameLocName(fallbackKey, locale);
    if (name) {{
      name = name.toUpperCase();
      const nameSpan = row.querySelector('.col-name span');
      if (nameSpan) {{
        const small = nameSpan.querySelector('small');
        if (small) {{
          nameSpan.childNodes[0].textContent = name;
        }} else {{
          nameSpan.textContent = name;
        }}
      }}
    }}
  }});

  // Update resource column headers: update label text and icon tooltip
  document.querySelectorAll('th[data-res]').forEach(th => {{
    const resId = th.dataset.res;
    const locKey = RESOURCE_LOC_KEYS[resId];
    if (locKey) {{
      const name = getGameLocName(locKey, locale);
      if (name) {{
        // Update icon tooltip
        const iconSpan = th.querySelector('span.res-icon');
        if (iconSpan) iconSpan.title = name;
        // Update label span under icon (the second span, not the icon)
        const labelSpan = th.querySelector('span:not(.res-icon)');
        if (labelSpan) labelSpan.textContent = name;
      }}
    }}
  }});

  // Update research tech labels (use game loc)
  document.querySelectorAll('[data-loc-key^="research_"]').forEach(el => {{
    const name = getGameLocName(el.dataset.locKey, locale);
    if (name) el.textContent = name.toUpperCase();
  }});

  // Update bonus group titles
  document.querySelectorAll('.bonus-group-title').forEach(el => {{
    const key = el.dataset.locKey;
    if (key) {{
      const translated = t(key, locale);
      if (translated !== key) el.textContent = translated;
    }}
  }});

  // Update grand panel resource labels and tooltips
  document.querySelectorAll('.grand-res').forEach(el => {{
    const m = el.id && el.id.match(/^grand-(.+)$/);
    if (!m) return;
    const resId = m[1];
    const locKey = RESOURCE_LOC_KEYS[resId];
    if (!locKey) return;
    const name = getGameLocName(locKey, locale);
    if (name) {{
      const iconSpan = el.querySelector('span.res-icon');
      if (iconSpan) iconSpan.title = name;
      const labelSpan = el.querySelector('span.res-label');
      if (labelSpan) labelSpan.textContent = name;
    }}
  }});

  // Update subtotal labels
  document.querySelectorAll('.subtotal-label[data-loc-key]').forEach(el => {{
    el.textContent = t(el.dataset.locKey, locale);
  }});

  // Update grand panel dynamic text
  recalc();  // This will re-render with new locale via format functions

  // Update bonus target labels
  updateBonusNotes(locale);

  // Save preference
  localStorage.setItem('se-locale', locale);

  // Update select dropdown
  const sel = document.getElementById('lang-select');
  if (sel) sel.value = locale;
}}

// Populate language selector
function initLangSelector() {{
  const sel = document.getElementById('lang-select');
  if (!sel) return;
  AVAILABLE_LOCALES.forEach(loc => {{
    const opt = document.createElement('option');
    opt.value = loc;
    opt.textContent = NATIVE_NAMES[loc] || loc;
    sel.appendChild(opt);
  }});
  sel.addEventListener('change', () => applyLocale(sel.value));
}}

// Initialize on load
initLangSelector();
applyLocale(detectLocale());
</script>
</body>
</html>
"""

out = "index.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Saved: {out}")
print(
    f"  {len(buildings)} buildings, {len(modules)} modules, "
    f"{len(launch_vehicles)} launch vehicles, {len(spacecraft)} spacecraft"
)
