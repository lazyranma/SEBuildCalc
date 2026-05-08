# Solar Expanse Build Cost Calculator — Agent Instructions

## Overview

Extracts facility/spacecraft build costs from the game *Solar Expanse* and
generates a standalone interactive HTML calculator (`index.html`).

## Data Pipeline

```
[Game Assets] ──extract──> [data/*.json] ──generate──> [index.html]
```

All extraction scripts read from `sharedassets0.assets` (Unity binary) in the
game install directory. Each produces one intermediate JSON file in `data/`.
The final step reads all JSON files and produces `index.html`.

## Project Structure

```
SolarExpanseCalc/
├── extract_costs.py           # Extract facility build costs
├── extract_spacecraft_costs.py # Extract spacecraft costs
├── dump_loc.py                # Dump localization strings
├── extract_buildability.py    # Extract isObsolete flags
├── extract_research.py        # Extract research unlock data
├── extract_icons.py           # Extract resource icons
├── generate_table.py          # Generate index.html
├── Makefile                   # Orchestrate extraction + generation
├── AGENTS.md                  # This file
├── index.html                 # (generated) Interactive HTML calculator
├── icons/                     # (generated) PNG resource icons
└── data/                      # (generated, git-ignored)
    ├── facility_costs.json
    ├── spacecraft_costs.json
    ├── loc_names.txt
    ├── extracted_buildability.json
    ├── research_unlocks.json
    └── research/              # BepInEx plugin + investigation notes
```

### Extraction Scripts (read game, write data/)

| Script | Output | What it extracts |
|---|---|---|
| `extract_costs.py` | `data/facility_costs.json` | Build costs, C# `class_type`, **`facility_type`** (EFacilityType enum 0-8) |
| `extract_spacecraft_costs.py` | `data/spacecraft_costs.json` | Spacecraft build costs and display names |
| `dump_loc.py` | `data/loc_names.txt` | Display names for all facilities (`build_*`, `module_*`) |
| `extract_buildability.py` | `data/extracted_buildability.json` | `isObsolete` flag per facility |
| `extract_research.py` | `data/research_unlocks.json` | Facility IDs unlocked by each research |
| `extract_icons.py` | `icons/` | PNG icons for each resource type |

### Generation Script

| Script | Input | Output |
|---|---|---|
| `generate_table.py` | All data/ files + icons/ | `index.html` |

### Other

| File | Purpose |
|---|---|
| `Makefile` | Orchestrates extraction + generation; `make clean` removes all outputs |
| `data/research/` | BepInEx plugin and investigation artifacts (not part of pipeline) |
| `AGENTS.md` | This file |

## Running

```bash
# Set the game directory (either env var or make variable):
export SOLAR_EXPANSE_DIR="D:\Steam\steamapps\common\Solar Expanse"

make          # full pipeline: extract everything, generate HTML
make clean    # remove all generated files (data/*.json, icons/, index.html)
make table    # generate HTML only (requires data/ files present)
```

The game directory can be set via:
- Environment variable: `SOLAR_EXPANSE_DIR`
- Make variable: `make GAME_DIR="path/to/game"`
- Directly to each script: `python extract_costs.py --game-dir "path/to/game"`
