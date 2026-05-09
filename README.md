# Solar Expanse Build Cost Calculator

> **Disclaimer:** This project is 100% LLM-generated code.

Generates a standalone interactive HTML calculator for facility, spacecraft, and
launch vehicle build costs from the game *Solar Expanse*.

The HTML page (`index.html`) shows every buildable item with its resource costs,
construction time, research requirements, and icons — all in a single, offline,
searchable table.

## How It Works

The pipeline has three stages:

1. **Extract data** — A [BepInEx](https://github.com/BepInEx/BepInEx) plugin
   runs inside the game and dumps all build costs, research unlocks, icon
   references, and localization strings to JSON files in `data/`.

2. **Extract icons** — A Python script reads the game's Unity asset files and
   exports resource, facility, spacecraft, and launch vehicle icons as PNGs
   into `icons/`.

3. **Generate HTML** — A Python script consumes all the extracted data and
   icons and produces a single self-contained `index.html`.

```
Game ──> BepInEx plugin ──> data/*.json ─────┐
                      ┌─────<────┘           ├──> generate_table.py ──> index.html
Game assets ──> extract_icons.py ──> icons/ ─┘
```

## Requirements

| Dependency | Used By | Install |
|---|---|---|
| **Solar Expanse** (game) | Data & icon extraction | Steam |
| **Python 3.9+** | Icons & HTML generation | [python.org](https://www.python.org/) |
| **UnityPy** (Python package) | Icon extraction | `pip install -r requirements.txt` |
| **.NET SDK 8.0+** | Plugin compilation | [dotnet.microsoft.com](https://dotnet.microsoft.com/) |

> **Note:** The .NET plugin references game DLLs at build time, so the game
> must be installed *before* building.

## Quick Start

### 1. Set the game directory

The build system needs to know where Solar Expanse is installed.  Set it once:

```sh
# Option A: environment variable (persistent)
export SOLAR_EXPANSE_DIR="C:\Steam\steamapps\common\Solar Expanse"

# Option B: pass to each make invocation
make GAME_DIR="C:\Steam\steamapps\common\Solar Expanse"
```

### 2. Run the full pipeline

```sh
make all
```

This runs all three stages sequentially: `extract-run` → `icons` → `table`.

The game will launch briefly, extract data, then close automatically.  At the
end you'll have `index.html` ready to use.

### 3. Open the calculator

```sh
start index.html
```

## Step-by-Step Build

If you prefer to run each stage individually:

```sh
# Stage 1: Launch the game and extract all data (takes ~30–120 seconds)
make extract-run

# Stage 2: Extract icons from Unity asset files
make icons

# Stage 3: Generate the HTML calculator
make table
```

## Make Targets

| Target | Description |
|---|---|
| `all` | Full pipeline: `extract-run` → `icons` → `table` |
| `extract-run` | Build the BepInEx plugin, launch the game, extract data, kill the game |
| `icons` | Extract all icons from Unity assets into `icons/` |
| `table` | Generate `index.html` from extracted data and icons |
| `clean` | Remove all generated files (`data/`, `icons/`, `index.html`, .NET build artifacts) |
| `help` | Show available targets and variables |

## Output

After a successful build, these files are produced:

```
index.html               # Standalone HTML calculator (open in any browser)
data/                    # Raw extracted JSON data (git-ignored)
icons/                   # PNG icons, organized by category
icons/icon_map.json       # Mapping of game IDs to icon paths
```

## Troubleshooting

### "GAME_DIR is not set"

You must specify the path to your Solar Expanse installation.  Set the
`SOLAR_EXPANSE_DIR` environment variable or pass `GAME_DIR=...` to make.

### "Game executable not found"

Make sure `GAME_DIR` points to the folder containing `Solar Expanse.exe`,
not the `Solar Expanse_Data` subfolder.

### "Build failed" (dotnet)

The plugin references BepInEx and Unity DLLs from the game directory.  Ensure:

- BepInEx is installed in the game directory (the script downloads it automatically on first run, but you can also install it manually).
- The game is installed and up to date (Steam file integrity check).

### "ModuleNotFoundError: No module named 'UnityPy'"

Install the required Python dependencies:

```sh
pip install -r requirements.txt
```

### Game crashes during extraction

The extraction plugin uses reflection to access the game's internal types.
If a game update changes the internal API, the plugin may need updating (see
`extract/Plugin.cs`).

### Extraction times out

The default timeout is 120 seconds.  If the game takes longer to load (e.g., on
a slow machine or first launch), increase it:

```sh
python run_extract.py --game-dir "C:\Steam\...\Solar Expanse" --timeout 300
```

## Project Structure

```
SolarExpanseCalc/
├── extract/
│   ├── Plugin.cs                        # BepInEx data extraction plugin
│   └── SolarExpanseExtract.csproj       # .NET project file
├── run_extract.py                       # Build + launch + wait + kill
├── extract_icons.py                     # Extract icons from Unity assets
├── generate_table.py                    # Generate index.html
├── Makefile                             # Orchestrate pipeline
├── README.md                            # This file
├── .gitignore
├── index.html                           # (generated) HTML calculator
├── icons/                               # (generated) PNG icons
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

## License

The code in this project is licensed under [MIT](LICENSE).  Extracted game data
and icons remain the property of the *Solar Expanse* developers.
