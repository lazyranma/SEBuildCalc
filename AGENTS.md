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
│   ├── Plugin.cs                        # BepInEx data extraction plugin
│   ├── SolarExpanseExtract.csproj       # .NET project file
│   └── run_extract.py                   # Build + launch + wait + kill
├── extract_icons.py                     # Extract icons from Unity assets (Python)
├── generate_table.py                    # Generate index.html
├── Makefile                             # Orchestrate pipeline
├── AGENTS.md                            # This file
├── .gitignore
├── index.html                           # (generated) HTML calculator
├── icons/                               # (generated)
│   ├── *.png                            #   Resource icons
│   ├── facilities/*.png                 #   Facility & module icons
│   ├── launch_vehicles/*.png            #   Launch vehicle icons
│   ├── spacecraft/*.png                 #   Spacecraft icons
│   └── icon_map.json                    #   Combined icon manifest
└── data/                                # (generated, git-ignored)
    ├── facility_costs.json
    ├── facility_icons.json
    ├── launch_vehicle_costs.json
    ├── launch_vehicle_icons.json
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
| `data/launch_vehicle_costs.json` | `LaunchVehicleType.PriceBase`, `TimeToBuildInDays`, `fakeForFacility`, `forCycleMission`, `isLocked` |
| `data/launch_vehicle_icons.json` | `GetSpriteName()` on each launch vehicle type |
| `data/spacecraft_costs.json` | `SpacecraftType.PriceBase`, `TimeToBuildInDays` |
| `data/spacecraft_icons.json` | `GetSpriteName()` on each spacecraft type |
| `data/resource_icons.json` | `GetSpriteName()` on each resource descriptor |
| `data/loc_names.txt` | `StreamingAssets/Languages/en-US.csv` |
| `data/extracted_buildability.json` | `IsLocked`, `IsObsolete`, `ShowOnUI`, `facilityType` |
| `data/research_unlocks.json` | `UnlockData.actionUnlock` (= `UnlockFacility` or `UnlockVehicleType`) + `parameter1` |

### Generation

| Script | Input | Output |
|---|---|---|
| `generate_table.py` | All data/ files + icons/ | `index.html` |

## Running

```bash
make extract-run    # Launch game, extract all data, kill game
make icons          # Extract all icons from Unity assets
make table          # Generate HTML
make clean          # Remove all generated files

# Or all in one:
make extract-run icons table
```

## Known Agent Issues

### `index.html` is too large to read or grep

The generated `index.html` file contains very large HTML table rows that will
overflow the agent context window if read. The `read_file` and `grep` tools do
not truncate large matches — they return the full content, which can consume
all available context and cause the session to break.

**Do not** use `grep` or `read_file` on `index.html`. If you need to inspect
or modify the HTML output, work with the source generator script
(`generate_table.py`) and its input data files instead.

### edit_file tool: DeepSeek V4 generates incorrect tool prompts

Direct calls to `edit_file` with specific model (DeepSeek V4 Pro) often
produce `"old_text":""` on the wire, even when the JSON in the tool call appears
correct. The model generates an empty string for the `old_text` parameter
irrespective of what was written in the tool-use block.

**Workarounds:**
- **Always attempt `edit` mode first** for files inside this project directory.
  If the call fails (e.g. `old_text` comes back empty), retry up to two more
  times — the intermittent nature of the bug means a retry often succeeds.
- If `edit` mode fails after several sequential attempts, **fall back** to one
  of the following:
  - Use `write` mode, providing the complete file content.
  - Spawn a sub-agent and ask it to make the edit — sub-agents do not exhibit
    this problem.
