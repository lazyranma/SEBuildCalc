# Solar Expanse Build Cost Calculator — Agent Instructions

## Overview

Extracts facility/spacecraft build costs from the game *Solar Expanse* and
generates a standalone interactive HTML calculator (`index.html`).

## Data Pipeline

```
[Game (running)] ──BepInEx plugin──> [data/*.json] ──generate──> [index.html]
                       │
                       └── extract_icons.py ──> [icons/]
```

A single BepInEx plugin (`extract/Plugin.cs`) extracts all game data at runtime
via the real C# API, including icon/sprite references for facilities,
spacecraft, and resources.

## Project Structure

```
SolarExpanseCalc/
├── extract/
│   ├── Plugin.cs                       # BepInEx data extraction plugin
│   ├── SolarExpanseExtract.csproj       # .NET project file
│   ├── run_extract.py                   # Build + launch + wait + kill
│   └── README.md
├── extract_icons.py                     # Extract icons from Unity assets (Python)
├── generate_table.py                    # Generate index.html
├── Makefile                             # Orchestrate pipeline
├── AGENTS.md                            # This file
├── .gitignore
├── index.html                           # (generated) HTML calculator
├── icons/                               # (generated)
│   ├── *.png                            #   Resource icons
│   ├── facilities/*.png                 #   Facility & module icons
│   ├── spacecraft/*.png                 #   Spacecraft icons
│   └── icon_map.json                    #   Combined icon manifest
└── data/                                # (generated, git-ignored)
    ├── facility_costs.json
    ├── facility_icons.json
    ├── spacecraft_costs.json
    ├── spacecraft_icons.json
    ├── resource_icons.json
    ├── loc_names.txt
    ├── extracted_buildability.json
    └── research_unlocks.json
```

### Extraction (BepInEx plugin)

| Output | Source in plugin |
|---|---|
| `data/facility_costs.json` | `FacilityBaseDescriptor.Price`, `TimeToBuildInDays` |
| `data/facility_icons.json` | `GetSpriteName()` on each facility descriptor |
| `data/spacecraft_costs.json` | `SpacecraftType.PriceBase`, `TimeToBuildInDays` |
| `data/spacecraft_icons.json` | `GetSpriteName()` on each spacecraft type |
| `data/resource_icons.json` | `GetSpriteName()` on each resource descriptor |
| `data/loc_names.txt` | `StreamingAssets/Languages/en-US.csv` |
| `data/extracted_buildability.json` | `IsLocked`, `IsObsolete`, `ShowOnUI`, `facilityType` |
| `data/research_unlocks.json` | `UnlockData.actionUnlock` + `parameter1` fields |

### Generation

| Script | Input | Output |
|---|---|---|
| `generate_table.py` | All data/ files + icons/ | `index.html` |

## Running

```bash
export SOLAR_EXPANSE_DIR="/path/to/SolarExpanse"

make extract-run    # Launch game, extract all data, kill game
make icons          # Extract all icons from Unity assets
make table          # Generate HTML
make clean          # Remove all generated files

# Or all in one:
make extract-run icons table
```
