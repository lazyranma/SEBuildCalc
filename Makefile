# Solar Expanse Build Cost Calculator
# ====================================

PYTHON     := python

# GAME_DIR: path to Solar Expanse install.
# Override via env var SOLAR_EXPANSE_DIR or pass as make variable.
GAME_DIR   ?= $(or $(SOLAR_EXPANSE_DIR),)

# Use sh explicitly so the Makefile works from any shell (pwsh, cmd, bash).
# Requires Git Bash / MSYS2 / MinGW sh on PATH.
SHELL := sh

# Guard: fail early with a clear message when GAME_DIR is required but not set.
# Use as the first line of a recipe:  $(call require-game-dir)
require-game-dir = $(if $(strip $(GAME_DIR)),,$(error GAME_DIR is not set. Set GAME_DIR=... or set SOLAR_EXPANSE_DIR env var.))

DATA_DIR   := data
ICONS_DIR  := icons
EXTRACT_DIR := extract

# --- Plugin ---
PLUGIN_DLL  := $(EXTRACT_DIR)/bin/Debug/netstandard2.1/SolarExpanseExtract.dll
PLUGIN_SRCS := $(EXTRACT_DIR)/Plugin.cs $(EXTRACT_DIR)/SolarExpanseExtract.csproj

# --- Stamp files for multi-output recipes ---
DATA_STAMP  := $(DATA_DIR)/.stamp
ICON_MAP    := $(ICONS_DIR)/icon_map.json

# --- Final output ---
HTML_OUT := index.html

.PHONY: all table clean help extract icons plugin

# ===================================================================
# Default target: build index.html and everything it needs
# ===================================================================
all: $(HTML_OUT)

# table is a synonym for all — both produce the final HTML
table: $(HTML_OUT)

help:
	@echo "Solar Expanse Build Cost Calculator"
	@echo ""
	@echo "  all / table  Build index.html (and all missing prerequisites)"
	@echo "  plugin       Build the BepInEx extraction plugin"
	@echo "  extract      Run game extraction -> data/*.json"
	@echo "  icons        Extract icons from game assets -> icons/"
	@echo "  clean        Remove all generated files"
	@echo ""
	@echo "Variables:"
	@echo "  GAME_DIR            Path to Solar Expanse install"
	@echo "  SOLAR_EXPANSE_DIR   Env var alternative to GAME_DIR"

# ===================================================================
# Plugin DLL — rebuilt whenever source files change
# ===================================================================
$(PLUGIN_DLL): $(PLUGIN_SRCS)
	$(call require-game-dir)
	@echo "[*] Building extraction plugin..."
	dotnet build $(EXTRACT_DIR)/SolarExpanseExtract.csproj -p:GameDir="$(GAME_DIR)" --nologo -v q

# ===================================================================
# Data extraction — runs the game with the plugin installed.
# Triggered when: DLL changed, or stamp missing (clean / first run).
# ===================================================================
$(DATA_STAMP): $(PLUGIN_DLL) run_extract.py
	$(call require-game-dir)
	@echo "[*] Running game extraction..."
	$(PYTHON) run_extract.py --game-dir "$(GAME_DIR)"
	@touch $@

# Convenience phony targets
plugin: $(PLUGIN_DLL)
extract: $(DATA_STAMP)

# ===================================================================
# Icon extraction — reads game assets + icon JSONs from data/
# ===================================================================
$(ICON_MAP): extract_icons.py $(DATA_STAMP)
	$(call require-game-dir)
	@echo "[*] Extracting icons..."
	$(PYTHON) extract_icons.py --game-dir "$(GAME_DIR)"

icons: $(ICON_MAP)

# ===================================================================
# HTML table — generated from data/*.json + icons/
# ===================================================================
$(HTML_OUT): generate_table.py $(DATA_STAMP) $(ICON_MAP)
	@echo "[*] Generating HTML calculator..."
	$(PYTHON) generate_table.py

# ===================================================================
# Clean
# ===================================================================
clean:
	@echo "[*] Cleaning generated files..."
	-@rm -rf "$(DATA_DIR)"
	-@rm -rf "$(ICONS_DIR)"
	-@rm -f "$(HTML_OUT)"
	-@rm -rf $(EXTRACT_DIR)/bin $(EXTRACT_DIR)/obj
