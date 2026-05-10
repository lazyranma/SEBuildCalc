"""
Deploy and run the BepInEx extraction plugin.

The plugin DLL must already be built (by the Makefile) before calling this script.

1. Ensure BepInEx is installed in the game directory (download if missing)
2. Verify the pre-built plugin DLL exists
3. Copy the DLL + config file to BepInEx/plugins/
4. Launch the game
5. Wait for the marker file to appear (timeout: 60s)
6. Kill the game

Usage:
    python run_extract.py [--game-dir PATH] [--timeout SECONDS]
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# BepInEx 5.x for Unity Mono x64
BEPINEX_DOWNLOAD_URL = (
    "https://github.com/BepInEx/BepInEx/releases/download/"
    "v5.4.23.5/BepInEx_win_x64_5.4.23.5.zip"
)

MARKER_FILE = "extract_plugin_ok.txt"
PLUGIN_DLL = "SolarExpanseExtract.dll"
CONFIG_FILE = "SolarExpanseExtract.cfg"
GAME_EXE_NAME = "Solar Expanse.exe"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_paths():
    """Determine game dir, project root, extract dir, and data dir."""
    parser = argparse.ArgumentParser(description="Run BepInEx extraction plugin")
    parser.add_argument(
        "--game-dir",
        default=os.environ.get("SOLAR_EXPANSE_DIR", ""),
        help="Path to Solar Expanse install (or set SOLAR_EXPANSE_DIR env var)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Seconds to wait for marker file (default: 60)",
    )
    args = parser.parse_args()

    if not args.game_dir:
        print("ERROR: --game-dir is required (or set SOLAR_EXPANSE_DIR)", flush=True)
        sys.exit(1)

    game_dir = Path(args.game_dir).resolve()
    project_root = Path(__file__).resolve().parent
    extract_dir = project_root / "extract"
    data_dir = project_root / "data"
    plugin_src = extract_dir / "bin" / "Debug" / "netstandard2.1" / PLUGIN_DLL
    plugin_dest = game_dir / "BepInEx" / "plugins" / PLUGIN_DLL
    config_dest = game_dir / "BepInEx" / "plugins" / CONFIG_FILE
    game_exe = game_dir / GAME_EXE_NAME
    marker_path = data_dir / MARKER_FILE

    return (
        args,
        game_dir,
        project_root,
        data_dir,
        plugin_src,
        plugin_dest,
        config_dest,
        game_exe,
        marker_path,
    )


def _run_tasklist(exe_name: str):
    """Run tasklist and return list of PIDs for the given image name."""
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
    )
    pids = []
    for line in result.stdout.strip().split("\n"):
        if exe_name in line:
            parts = line.replace('"', "").split(",")
            if len(parts) >= 2:
                try:
                    pids.append(int(parts[1].strip()))
                except ValueError:
                    pass
    return pids


def _is_game_running():
    """Check if any Solar Expanse process is running."""
    return len(_run_tasklist(GAME_EXE_NAME)) > 0


def ensure_bepinex(game_dir: Path):
    """Download and install BepInEx if not already present."""
    bepinix_core = game_dir / "BepInEx" / "core" / "BepInEx.dll"
    if bepinix_core.exists():
        print(f"[*] BepInEx already installed: {bepinix_core}")
        return True

    print("[*] BepInEx not found, downloading...")
    zip_path = game_dir / "BepInEx.zip"
    try:
        print(f"    Fetching {BEPINEX_DOWNLOAD_URL} ...")
        urllib.request.urlretrieve(BEPINEX_DOWNLOAD_URL, zip_path)
        print(f"    Extracting to {game_dir} ...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(game_dir)
        zip_path.unlink()
        print("[*] BepInEx installed successfully.")
        return True
    except Exception as e:
        print(f"ERROR downloading BepInEx: {e}", flush=True)
        if zip_path.exists():
            zip_path.unlink()
        return False


def install_plugin(
    plugin_src: Path, plugin_dest: Path, config_dest: Path, data_dir: Path
):
    """Copy the built DLL to BepInEx/plugins/ and write config file."""
    if not plugin_src.exists():
        print(f"ERROR: Plugin DLL not found: {plugin_src}", flush=True)
        return False
    plugin_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plugin_src, plugin_dest)
    print(f"[*] Installed: {plugin_dest}")

    config_dest.write_text(f"data_dir={data_dir}\n", encoding="utf-8")
    print(f"[*] Config written: {config_dest}")
    return True


def launch_game(game_exe: Path):
    """Launch the game.

    The game may exit and relaunch via Steam; we don't track PIDs.
    The marker file is the only reliable success signal.
    """
    if not game_exe.exists():
        print(f"ERROR: Game executable not found: {game_exe}", flush=True)
        return False

    print(f"[*] Launching: {game_exe}")
    subprocess.Popen(
        [str(game_exe)],
        cwd=str(game_exe.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def wait_for_marker(marker_path: Path, timeout: int):
    """Poll for the marker file. Returns True if found before timeout.

    Intentionally does not track game processes — the game may hand off to Steam and
    relaunch under a different PID. The marker file is the only signal.
    """
    if marker_path.exists():
        marker_path.unlink()
        print(f"[*] Removed previous marker: {marker_path}")

    deadline = time.time() + timeout
    print(f"[*] Waiting for marker file (timeout: {timeout}s)...")
    print(f"    Expected: {marker_path}")

    while time.time() < deadline:
        if marker_path.exists():
            elapsed = timeout - (deadline - time.time())
            print(f"    Marker appeared after {elapsed:.1f}s!")
            content = marker_path.read_text().strip()
            print(f"    Content: {content}")
            return True

        time.sleep(1)
        elapsed = int(timeout - (deadline - time.time()))
        if elapsed % 10 == 0:
            print(f"    ... {elapsed}s elapsed, still waiting")

    print("    TIMEOUT: marker did not appear.", flush=True)
    return False


def uninstall_plugin(plugin_dest: Path, config_dest: Path):
    """Remove the plugin DLL and config from BepInEx/plugins/."""
    for f in (plugin_dest, config_dest):
        if f.exists():
            f.unlink()
            print(f"[*] Removed: {f}")


def kill_game():
    """Terminate all Solar Expanse processes."""
    if not _is_game_running():
        return
    print("[*] Terminating game process...")
    subprocess.run(
        ["taskkill", "/IM", GAME_EXE_NAME, "/F"],
        capture_output=True,
    )
    for _ in range(20):
        if not _is_game_running():
            print("    Game terminated.")
            return
        time.sleep(0.5)
    print("    WARNING: game may still be running.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    (
        args,
        game_dir,
        project_root,
        data_dir,
        plugin_src,
        plugin_dest,
        config_dest,
        game_exe,
        marker_path,
    ) = resolve_paths()

    print("=" * 60)
    print("  Solar Expanse Extraction Runner")
    print("=" * 60)
    print(f"  Game dir:     {game_dir}")
    print(f"  Project root: {project_root}")
    print(f"  Marker file:  {marker_path}")
    print()

    if _is_game_running():
        print(
            "ERROR: Solar Expanse is already running. "
            "Close it before running extraction.",
            flush=True,
        )
        sys.exit(1)

    if not ensure_bepinex(game_dir):
        sys.exit(1)

    if not plugin_src.exists():
        print(
            f"ERROR: Plugin DLL not found: {plugin_src}",
            flush=True,
        )
        print(
            "       Run 'make' to build the plugin first.",
            flush=True,
        )
        sys.exit(1)
    print(f"[*] Using plugin: {plugin_src}")

    if not install_plugin(plugin_src, plugin_dest, config_dest, data_dir):
        sys.exit(1)

    if not launch_game(game_exe):
        sys.exit(1)

    success = wait_for_marker(marker_path, args.timeout)

    kill_game()

    uninstall_plugin(plugin_dest, config_dest)

    # Remove the marker file - only needed during the run
    if marker_path.exists():
        marker_path.unlink()

    if success:
        print("\n[DONE] Extraction completed successfully.")
        sys.exit(0)
    else:
        print("\n[FAIL] Extraction did not complete.", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
