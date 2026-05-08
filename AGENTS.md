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
via the real C# API.  Resource icons are still extracted from the Unity asset
bundle via Python.

## Project Structure

```
SolarExpanseCalc/
├── extract/
│   ├── Plugin.cs                       # BepInEx data extraction plugin
│   ├── SolarExpanseExtract.csproj       # .NET project file
│   ├── run_extract.py                   # Build + launch + wait + kill
│   └── README.md
├── extract_icons.py                     # Extract resource icons (Python)
├── generate_table.py                    # Generate index.html
├── Makefile                             # Orchestrate pipeline
├── AGENTS.md                            # This file
├── .gitignore
├── index.html                           # (generated) HTML calculator
├── icons/                               # (generated) PNG resource icons
└── data/                                # (generated, git-ignored)
    ├── facility_costs.json
    ├── spacecraft_costs.json
    ├── loc_names.txt
    ├── extracted_buildability.json
    ├── research_unlocks.json
```

### Extraction (BepInEx plugin — replaces 5 old Python scripts)

| Output | Source in plugin |
|---|---|
| `data/facility_costs.json` | `FacilityBaseDescriptor.Price`, `TimeToBuildInDays` |
| `data/spacecraft_costs.json` | `SpacecraftType.PriceBase`, `TimeToBuildInDays` |
| `data/loc_names.txt` | `StreamingAssets/Languages/en-US.csv` |
| `data/extracted_buildability.json` | `IsLocked`, `IsObsolete`, `ShowOnUI`, `facilityType` |
| `data/research_unlocks.json` | `UnlockData.actionUnlock` + `parameter1` fields |

### Generation

| Script | Input | Output |
|---|---|---|
| `generate_table.py` | All data/ files + icons/ | `index.html` |

## Running

```bash
export SOLAR_EXPANSE_DIR="D:\Steam\steamapps\common\Solar Expanse"

make extract-run    # Launch game, extract all data, kill game
make icons          # Extract resource icons
make table          # Generate HTML
make clean          # Remove all generated files

# Or all in one:
make extract-run icons table
```

The plugin writes a config file (`SolarExpanseExtract.cfg`) next to the DLL so
it knows where to output data. The `run_extract.py` script manages this.
