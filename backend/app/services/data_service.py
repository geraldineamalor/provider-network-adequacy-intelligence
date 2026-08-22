from typing import Any

import pandas as pd

from pathlib import Path

import os

from app.data.specialties import Specialty
from app.data.specialty_taxonomy import resolve_specialty

# ---------------------------------------------------------------------------
# Resolve project root: go three levels up from this file
# (backend/app/services/ → backend/app/ → backend/ → workspace root)
# ---------------------------------------------------------------------------
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ---------------------------------------------------------------------------
# Data paths (relative to workspace root)
# ---------------------------------------------------------------------------
ML1_PATH = _WORKSPACE_ROOT / "data/processed/provider_network_ml_ready_specialty.csv"
BE3_PATH = _WORKSPACE_ROOT / "data/be3/final/be3_final_281478.csv"
CENSUS_PATH = _WORKSPACE_ROOT / "data/processed/census_zip_population_2023.csv"
ZCTA_COUNTY_PATH = _WORKSPACE_ROOT / "data/be3/geographic_reference/zcta_county_relationship_2020.csv"

# ---------------------------------------------------------------------------
# Deterministic state-name <-> 2-char code mapping
# ---------------------------------------------------------------------------
_STATE_NAMES_LOWER = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}

_STATE_CODE_TO_NAME = {v: k for k, v in _STATE_NAMES_LOWER.items()}


# ---------------------------------------------------------------------------
# Cache: load data once at module import time
# ---------------------------------------------------------------------------
_ml1_df: pd.DataFrame | None = None
_be3_df: pd.DataFrame | None = None
_census_df: pd.DataFrame | None = None
_zcta_county_df: pd.DataFrame | None = None

# Cached ZCTA5 -> county_fips lookup (built once at import)
_zcta_to_county_fips = None


def _ensure_ml1_loaded() -> pd.DataFrame:
    global _ml1_df
    if _ml1_df is None:
        _ml1_df = pd.read_csv(ML1_PATH, dtype={"STATE_CLEAN": str, "ZIP_CLEAN": str, "PRIMARY_TAXONOMY": str})
    return _ml1_df


def _ensure_be3_loaded() -> pd.DataFrame:
    global _be3_df
    if _be3_df is None:
        _be3_df = pd.read_csv(BE3_PATH, dtype={"zip_clean": str, "zcta_clean": str, "county_fips": str})
    return _be3_df


def _ensure_census_loaded() -> pd.DataFrame:
    global _census_df
    if _census_df is None:
        _census_df = pd.read_csv(CENSUS_PATH, dtype={"ZIP_CLEAN": str, "population": float})
    return _census_df


def _ensure_zcta_county_loaded() -> pd.DataFrame:
    global _zcta_county_df
    if _zcta_county_df is None:
        _zcta_county_df = pd.read_csv(
            ZCTA_COUNTY_PATH,
            dtype={"GEOID_ZCTA5_20": str, "GEOID_COUNTY_20": str, "NAMELSAD_COUNTY_20": str},
        )
        # Build cached lookup: normalized county name -> set of county_fips (5-digit strings)
        global _zcta_to_county_fips
        _zcta_to_county_fips = {}
        for _, row in _zcta_county_df.iterrows():
            county_name = str(row.get("NAMELSAD_COUNTY_20", "")).strip().lower()
            county_fips = str(row.get("GEOID_COUNTY_20", "")).strip()
            # Normalize to 5-digit FIPS code
            county_fips_5d = county_fips.zfill(5)
            if county_name not in _zcta_to_county_fips:
                _zcta_to_county_fips[county_name] = set()
            _zcta_to_county_fips[county_name].add(county_fips_5d)
    return _zcta_county_df


# ---------------------------------------------------------------------------
# State resolution
# ---------------------------------------------------------------------------

def resolve_state(request_state: str) -> tuple[str, str]:
    """
    Given a request state (e.g. "Texas" or "TX"), return
    (state_code_2char, state_name_full).

    Accepts either a full state name (e.g. "Texas") or a 2-char code
    (e.g. "TX").  Deterministic mapping via _STATE_NAMES_LOWER / _STATE_CODE_TO_NAME.
    """
    s = request_state.strip()
    # If it's a 2-character code, look up the full name
    if len(s) == 2 and s.isalpha():
        state_code = s.upper()
        state_full = _STATE_CODE_TO_NAME.get(state_code, s)
        return state_code, state_full
    # Otherwise treat it as a full state name
    state_lower = s.lower()
    state_code = _STATE_NAMES_LOWER.get(state_lower)
    if state_code is None:
        raise ValueError(f"Unknown state name/code: {request_state!r}")
    state_full = _STATE_CODE_TO_NAME.get(state_code, s)
    return state_code, state_full


# ---------------------------------------------------------------------------
# County filtering
# ---------------------------------------------------------------------------

def _build_county_fips_set(counties: list[str]) -> set[str]:
    """
    Given a list of county names (as supplied in the API request),
    return the set of county_fips strings that match via the cached
    ZCTA-County relationship lookup.

    The lookup is built once at module import time from
    zcta_county_relationship_2020.csv, mapping normalized county names
    to the 5-digit FIPS codes that BE-3 uses.

    County names in the reference may include " County" suffix.
    The API may send just the county name.  We normalize by trying both.

    Because BE-3 county_fips are nationally unique 5-digit FIPS codes,
    matching by FIPS inherently avoids mixing counties with the same
    name across different states.

    Returns an empty set if no counties are requested or if no matches found.
    """
    if not counties:
        return set()

    # Use cached lookup built at module import time
    lookup = _zcta_to_county_fips
    if lookup is None:
        _ensure_zcta_county_loaded()
        lookup = _zcta_to_county_fips

    requested = {c.strip().lower() for c in counties}
    matching_fips: set[str] = set()

    for name in requested:
        if name in lookup:
            matching_fips.update(lookup[name])
        # Also try normalized name with " county" suffix
        suffixed = name + " county"
        if suffixed in lookup:
            matching_fips.update(lookup[suffixed])

    return matching_fips


# ---------------------------------------------------------------------------
# Taxonomy resolution (delegates to existing BE-1 layer)
# ---------------------------------------------------------------------------

def _resolve_taxonomy_codes(specialties: list[Specialty]) -> list[str]:
    """
    Return ALL approved PRIMARY_TAXONOMY codes for the given frontend specialties.
    Delegates to the existing BE-1 taxonomy mapping layer (reads
    specialty_taxonomy_mapping.csv and validates against the Specialty enum).
    """
    codes: set[str] = set()
    for s in specialties:
        for row in resolve_specialty(s):
            codes.add(row["code"])
    return sorted(codes)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_provider_data(
    state: str,
    counties: list[str],
    specialties: list[str],
) -> list[dict[str, Any]]:
    """
    Retrieve real provider/network data for the requested geographic areas
    and specialties.

    Data sources (loaded once, cached):
      - ML-1 specialty data: provider_network_ml_ready_specialty.csv
        Columns: STATE_CLEAN, ZIP_CLEAN, PRIMARY_TAXONOMY,
                 specialty_provider_count, area_id, population,
                 specialty_provider_density_per_1000
      - BE-3 authoritative provider/geographic data: be3_final_281478.csv
        (full provider record)
      - Census ZIP population: census_zip_population_2023.csv
      - ZCTA-County relationship: zcta_county_relationship_2020.csv

    Filtering flow (deterministic, no fuzzy matching):
      1. Resolve frontend specialties → PRIMARY_TAXONOMY code(s)
      2. Resolve state name → 2-char code (for ML-1) / full name (for BE-3)
      3. Filter ML-1 rows by STATE_CLEAN + PRIMARY_TAXONOMY
      4. Filter BE-3 rows by state code AND by PRIMARY_TAXONOMY code
      5. Join ML-1 ↔ BE-3 on ZIP_CLEAN == zip_clean (left merge)
      6. Apply county_fips filter via cached ZCTA→county lookup
      7. Enrich with population from census ZIP lookup
      8. Build response-record dicts from available fields
    """

    if not specialties:
        return []

    # --- Step 1: Resolve taxonomy codes ---
    taxonomy_codes = _resolve_taxonomy_codes(specialties)

    # --- Step 2: Resolve state ---
    state_code, state_full = resolve_state(state)

    # --- Step 3: Load cached data ---
    ml1 = _ensure_ml1_loaded()        # ML-1 specialty dataset
    be3 = _ensure_be3_loaded()        # BE-3 authoritative dataset
    census = _ensure_census_loaded()  # ZIP → population
    zcta_county = _ensure_zcta_county_loaded()

    # --- Step 4: Filter ML-1 by STATE_CLEAN + PRIMARY_TAXONOMY ---
    ml1_filtered = ml1[
        (ml1["STATE_CLEAN"].str.strip().str.upper() == state_code.upper())
        & (ml1["PRIMARY_TAXONOMY"].isin(taxonomy_codes))
    ].copy()

    if ml1_filtered.empty:
        return []

    # --- Step 5: Filter BE-3 by state code AND by PRIMARY_TAXONOMY ---
    # BE-3 uses 2-char state codes in the Provider Business Practice Location
    # Address State Name column. Filter to only the requested state first.
    be3_filtered = be3[
        be3["Provider Business Practice Location Address State Name"]
        .astype(str)
        .str.strip()
        .str.upper()
        == state_code.upper()
    ].copy()

    # NEW: Additionally filter BE-3 by the resolved PRIMARY_TAXONOMY codes.
    # The BE-3 column "Healthcare Provider Taxonomy Code_1" contains the
    # provider's taxonomy. Filter to only providers with the requested specialty.
    if not be3_filtered.empty:
        be3_filtered = be3_filtered[
            be3_filtered["Healthcare Provider Taxonomy Code_1"].isin(taxonomy_codes)
        ].copy()

    if be3_filtered.empty:
        return []

    # --- Step 6: Join ML-1 ↔ BE-3 on ZIP_CLEAN == zip_clean ---
    # Left merge on BE-3: each BE-3 provider (NPI) record is preserved.
    # Multiple ML-1 rows (different taxonomies) can map to one BE-3 NPI;
    # the left merge creates rows per combination.
    merged = ml1_filtered.merge(
        be3_filtered,
        left_on="ZIP_CLEAN",
        right_on="zip_clean",
        how="left",
        suffixes=("_ml1", "_be3"),
    )

    if merged.empty:
        return []

    # --- Step 7: Apply county filtering ---
    requested_fips = _build_county_fips_set(counties)

    if requested_fips:
        # Normalise BE-3 county_fips to string for comparison (already string, ensure)
        merged["_county_fips_str"] = merged["county_fips"].astype(str)
        # County_fips in BE-3 may be 3 or 5 digits; normalize to 5-digit for comparison
        merged["_county_fips_5d"] = merged["_county_fips_str"].str.zfill(5)
        merged = merged[merged["_county_fips_5d"].isin(requested_fips)].copy()

    if merged.empty:
        return []

    # --- Step 8: Deduplicate by NPI ---
    # After filtering BE-3 by taxonomy before the join, each NPI that remains
    # correctly represents the requested specialty. drop_duplicates is now safe.
    merged = merged.drop_duplicates(subset="NPI", keep="first")

    # Remove rows where BE-3 taxonomy was not matched (NaN from left merge).
    merged = merged[merged["Healthcare Provider Taxonomy Code_1"].notna()].copy()

    if merged.empty:
        return []

    # --- Step 9: Enrich with population from census ---
    census_pop = dict(zip(census["ZIP_CLEAN"].astype(str), census["population"].astype(float)))

    # --- Step 10: Build response records ---
    def _safe_str(row, col, default=""):
        """Get a string value from a DataFrame row, returning default if NaN."""
        val = row[col] if col in row.index else default
        if isinstance(val, float) and pd.isna(val):
            return default
        return str(val) if val is not None else default

    def _safe_float(row, col, default=0.0):
        """Get a float value from a DataFrame row, returning default if NaN."""
        val = row[col] if col in row.index else default
        if isinstance(val, float) and pd.isna(val):
            return default
        return float(val)

    records: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        zip_clean = str(row["zip_clean"])

        # Population from census ZIP lookup
        pop = census_pop.get(zip_clean, 0.0)

        # ML-1 joined fields (may be NaN if no match)
        ml1_sp_count = _safe_float(row, "specialty_provider_count_ml1", 0)
        ml1_density = _safe_float(row, "specialty_provider_density_per_1000_ml1", 0)

        # BE-3 provider counts safely
        be3_provider_5mi = _safe_float(row, "provider_count_5mi", 0)
        be3_same_tax_5mi = _safe_float(row, "same_taxonomy_count_5mi", 0)
        be3_area_total_5mi = _safe_float(row, "area_provider_count_5mi", 0)
        be3_area_same_5mi = _safe_float(row, "area_same_taxonomy_count_5mi", 0)

        # Provider name fields — safely handle NaN
        _org_name = _safe_str(row, "Provider Organization Name (Legal Business Name)")
        _last_name = _safe_str(row, "Provider Last Name (Legal Name)")
        _first_name = _safe_str(row, "Provider First Name")

        # Primary taxonomy from BE-3 (the actual resolved taxonomy code)
        primary_taxonomy = _safe_str(row, "Healthcare Provider Taxonomy Code_1")

        record = {
            # BE-3 authoritative identity + geography (preserved as strings)
            "npi": int(row["NPI"]) if not pd.isna(row["NPI"]) else None,
            "zip_clean": zip_clean,
            "zcta_clean": str(row["zcta_clean"]) if not pd.isna(row["zcta_clean"]) else None,
            "county_fips": str(row["county_fips"]) if not pd.isna(row["county_fips"]) else None,
            "state": state_full,
            # Provider name
            "provider_organization_name": _org_name,
            "provider_last_name": _last_name,
            "provider_first_name": _first_name,
            # Coordinates
            "latitude": _safe_float(row, "spatial_latitude"),
            "longitude": _safe_float(row, "spatial_longitude"),
            "spatial_coordinate_type": _safe_str(row, "spatial_coordinate_type"),
            "spatial_coordinate_source": _safe_str(row, "spatial_coordinate_source"),
            "spatial_coordinate_confidence": _safe_str(row, "spatial_coordinate_confidence"),
            # Taxonomy (from BE-3)
            "primary_taxonomy": primary_taxonomy,
            # Frontend specialty (the requested specialty)
            "frontend_specialty": specialties[0] if specialties else "",
            # ML-1 specialty metrics (joined via ZIP)
            "specialty_provider_count": ml1_sp_count,
            "specialty_provider_density_per_1000": ml1_density,
            # BE-3 provider adequacy metrics
            "provider_count_5mi": be3_provider_5mi,
            "same_taxonomy_count_5mi": be3_same_tax_5mi,
            "area_provider_count_5mi": be3_area_total_5mi,
            "area_same_taxonomy_count_5mi": be3_area_same_5mi,
            # Derived: population from census ZIP
            "population": int(pop) if pop and pop > 0 else None,
            # Joined ML-1 area counts
            "area_provider_count_5mi_be3": be3_area_total_5mi,
            "area_same_taxonomy_count_5mi_be3": be3_area_same_5mi,
        }
        records.append(record)

    return records