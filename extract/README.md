# Solar Expanse Data Extractor — BepInEx Plugin

Extracts game data at runtime via the real C# API (no binary parsing).

## Build

```powershell
$env:SOLAR_EXPANSE_DIR = "D:\Steam\steamapps\common\Solar Expanse"
dotnet build
```

Or override the game path directly:

```powershell
dotnet build /p:GameDir="D:\Steam\steamapps\common\Solar Expanse"
```

## Deploy

Copy `bin/Debug/netstandard2.1/SolarExpanseExtract.dll` to the game's
`BepInEx/plugins/` directory, then launch the game.

## Output

- If `SOLAR_EXPANSE_EXTRACT_DIR` is set: writes to `$SOLAR_EXPANSE_EXTRACT_DIR/data/`
- Otherwise: writes to `<game root>/ExtractedData/`
