# Solar Expanse Build Cost Calculator
# ====================================

# --- Configuration ---
PYTHON     := python

# GAME_DIR: path to Solar Expanse install.
# Override via env var SOLAR_EXPANSE_DIR or pass as make variable.
GAME_DIR   ?= $(or $(SOLAR_EXPANSE_DIR),)

ifeq ($(GAME_DIR),)
  $(error GAME_DIR is not set. Set SOLAR_EXPANSE_DIR env var or pass GAME_DIR=...)
endif

DATA_DIR   := data
ICONS_DIR  := icons

# --- Intermediate outputs (all in data/) ---
FACILITY_JSON   := $(DATA_DIR)/facility_costs.json
SPACECRAFT_JSON := $(DATA_DIR)/spacecraft_costs.json
LOC_NAMES_TXT   := $(DATA_DIR)/loc_names.txt
BUILDABILITY_JSON := $(DATA_DIR)/extracted_buildability.json
RESEARCH_JSON     := $(DATA_DIR)/research_unlocks.json

# --- Final output ---
HTML_OUT := index.html

# --- Phony targets ---
.PHONY: all clean icons facilities spacecraft loc buildability research table help

# --- Default target ---
all: table

# --- Help ---
help:
	@echo "Solar Expanse Build Cost Calculator"
	@echo ""
	@echo "Targets:"
	@echo "  all          Generate the full HTML calculator (default)"
	@echo "  facilities   Extract facility/building costs -> data/facility_costs.json"
	@echo "  spacecraft   Extract spacecraft costs        -> data/spacecraft_costs.json"
	@echo "  icons        Extract resource icons          -> icons/"
	@echo "  loc          Dump localization strings       -> data/loc_names.txt"
	@echo "  buildability Extract UI/buildability flags   -> data/extracted_buildability.json"
	@echo "  research     Extract research unlock data    -> data/research_unlocks.json"
	@echo "  table        Generate HTML build cost table  -> index.html"
	@echo "  clean        Remove generated files"
	@echo ""
	@echo "Variables:"
	@echo "  GAME_DIR            Path to Solar Expanse install"
	@echo "  SOLAR_EXPANSE_DIR   Env var alternative to GAME_DIR"

# --- Facilities ---
$(FACILITY_JSON): extract_costs.py
	@echo "[*] Extracting facility costs..."
	$(PYTHON) extract_costs.py --game-dir "$(GAME_DIR)"

facilities: $(FACILITY_JSON)

# --- Spacecraft ---
$(SPACECRAFT_JSON): extract_spacecraft_costs.py
	@echo "[*] Extracting spacecraft costs..."
	$(PYTHON) extract_spacecraft_costs.py --game-dir "$(GAME_DIR)"

spacecraft: $(SPACECRAFT_JSON)

# --- Icons ---
$(ICONS_DIR): extract_icons.py
	@echo "[*] Extracting resource icons..."
	$(PYTHON) extract_icons.py --game-dir "$(GAME_DIR)"

icons: $(ICONS_DIR)

# --- Localization ---
$(LOC_NAMES_TXT): dump_loc.py
	@echo "[*] Dumping localization strings..."
	$(PYTHON) dump_loc.py --game-dir "$(GAME_DIR)"

loc: $(LOC_NAMES_TXT)

# --- Buildability flags ---
$(BUILDABILITY_JSON): extract_buildability.py
	@echo "[*] Extracting buildability flags..."
	$(PYTHON) extract_buildability.py --game-dir "$(GAME_DIR)"

buildability: $(BUILDABILITY_JSON)

# --- Research ---
$(RESEARCH_JSON): extract_research.py
	@echo "[*] Extracting research unlock data..."
	$(PYTHON) extract_research.py --game-dir "$(GAME_DIR)"

research: $(RESEARCH_JSON)

# --- HTML table (depends on all intermediate outputs) ---
$(HTML_OUT): generate_table.py $(FACILITY_JSON) $(SPACECRAFT_JSON) $(ICONS_DIR) $(LOC_NAMES_TXT) $(BUILDABILITY_JSON) $(RESEARCH_JSON)
	@echo "[*] Generating HTML build cost calculator..."
	$(PYTHON) generate_table.py

table: $(HTML_OUT)

# --- Clean ---
clean:
	@echo "[*] Cleaning generated files..."
	-@del /Q "$(HTML_OUT)" 2>NUL || rm -f "$(HTML_OUT)"
	-@del /Q "$(FACILITY_JSON)" 2>NUL || rm -f "$(FACILITY_JSON)"
	-@del /Q "$(SPACECRAFT_JSON)" 2>NUL || rm -f "$(SPACECRAFT_JSON)"
	-@del /Q "$(LOC_NAMES_TXT)" 2>NUL || rm -f "$(LOC_NAMES_TXT)"
	-@del /Q "$(BUILDABILITY_JSON)" 2>NUL || rm -f "$(BUILDABILITY_JSON)"
	-@del /Q "$(RESEARCH_JSON)" 2>NUL || rm -f "$(RESEARCH_JSON)"
	-@rmdir /S /Q "$(ICONS_DIR)" 2>NUL || rm -rf "$(ICONS_DIR)"
