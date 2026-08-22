import sys
from pathlib import Path

# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import pandas as pd

from app.services.data_service import get_provider_data


# ============================================================
# PATHS
# ============================================================

BASE_PATH = (
    r"C:\Users\Roshini\OneDrive\Desktop"
    r"\Provider-Network-Project\data"
    r"\provider_network_ml_ready.csv"
)


# ============================================================
# PREPARE CANDIDATES
# ============================================================

def prepare_candidates(
    state,
    frontend_specialty,
    counties=None
):
    """
    ML-3 candidate preparation.

    Runtime candidate source:
        BE-1 get_provider_data()

    Candidate unit:
        ZIP/ZCTA + PRIMARY_TAXONOMY

    BE-1 handles:
        - state filtering
        - county filtering
        - specialty filtering
        - approved taxonomy mapping
        - BE-3 integration
        - population enrichment

    ML-2 five-feature contract:

        1. population
        2. zip_provider_share_of_state
        3. individual_provider_ratio
        4. organization_provider_ratio
        5. specialty_diversity

    PRIMARY_TAXONOMY is metadata/context only.
    It is NOT an ML-2 model feature.
    """

    print("\n========================================")
    print("ML-3 CANDIDATE PREPARATION")
    print("========================================")

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    state = str(state).strip()

    frontend_specialty = str(
        frontend_specialty
    ).strip()

    if counties is None:
        counties = []

    counties = [
        str(county).strip()
        for county in counties
        if str(county).strip()
    ]

    print(f"\nState: {state}")

    if counties:
        print(f"Counties: {counties}")
    else:
        print("Counties: ALL")

    print(
        f"Frontend specialty: {frontend_specialty}"
    )

    # ========================================================
    # STEP 1
    # CALL BE-1
    # ========================================================

    print("\nCalling BE-1 get_provider_data()...")

    records = get_provider_data(
        state,
        counties,
        [frontend_specialty]
    )

    print(
        f"BE-1 returned {len(records)} records."
    )

    # ========================================================
    # NO RECORDS
    # ========================================================

    if not records:

        print(
            "\nNo records returned by BE-1."
        )

        return pd.DataFrame(
            columns=[
                "STATE_CLEAN",
                "ZIP_CLEAN",
                "ZCTA_CLEAN",
                "PRIMARY_TAXONOMY",
                "frontend_specialty",
                "population",
                "zip_provider_share_of_state",
                "individual_provider_ratio",
                "organization_provider_ratio",
                "specialty_diversity"
            ]
        )

    # ========================================================
    # STEP 2
    # BE-1 RESPONSE -> DATAFRAME
    # ========================================================

    df = pd.DataFrame(records)

    print(
        f"\nBE-1 dataframe rows: {len(df)}"
    )

    print("\nBE-1 columns:")

    print(
        df.columns.tolist()
    )

    # ========================================================
    # CHECK REQUIRED BE-1 COLUMNS
    # ========================================================

    required_be1_columns = [
        "zip_clean",
        "zcta_clean",
        "primary_taxonomy",
        "state",
        "population"
    ]

    missing_be1_columns = [
        column
        for column in required_be1_columns
        if column not in df.columns
    ]

    if missing_be1_columns:

        raise ValueError(
            "BE-1 response is missing required columns: "
            f"{missing_be1_columns}"
        )

    # ========================================================
    # STEP 3
    # NORMALIZE BE-1 IDENTIFIERS
    # ========================================================

    print("\nNormalizing BE-1 data...")

    df["zip_clean"] = (
        df["zip_clean"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    df["zcta_clean"] = (
        df["zcta_clean"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    df["primary_taxonomy"] = (
        df["primary_taxonomy"]
        .astype(str)
        .str.strip()
    )

    df["STATE_CLEAN"] = (
        df["state"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    print("BE-1 normalization complete.")

    # ========================================================
    # STEP 4
    # CREATE UNIQUE ML-3 CANDIDATE UNIT
    # ========================================================

    print(
        "\nCreating ZIP/ZCTA + PRIMARY_TAXONOMY candidates..."
    )

    candidate_keys = [
        "zip_clean",
        "zcta_clean",
        "primary_taxonomy"
    ]

    # ========================================================
    # AGGREGATION
    # ========================================================

    aggregation = {}

    # Population
    aggregation["population"] = "max"

    # Frontend specialty
    if "frontend_specialty" in df.columns:
        aggregation["frontend_specialty"] = "first"

    # State
    aggregation["STATE_CLEAN"] = "first"

    # BE-3 supporting evidence
    supporting_columns = [
        "provider_count_5mi",
        "same_taxonomy_count_5mi",
        "area_provider_count_5mi",
        "area_same_taxonomy_count_5mi",
        "specialty_provider_count",
        "specialty_provider_density_per_1000",
        "area_provider_count_5mi_be3",
        "area_same_taxonomy_count_5mi_be3"
    ]

    for column in supporting_columns:

        if column in df.columns:
            aggregation[column] = "max"

    candidates = (
        df
        .groupby(
            candidate_keys,
            as_index=False
        )
        .agg(aggregation)
    )

    print(
        "\nUnique ZIP/ZCTA + taxonomy candidates:",
        len(candidates)
    )

    # ========================================================
    # STEP 5
    # LOAD ML-1 BASE DATA
    # ========================================================

    print(
        "\nLoading ML-1 base features..."
    )

    base_df = pd.read_csv(
        BASE_PATH
    )

    print(
        "ML-1 base rows:",
        len(base_df)
    )

    # ========================================================
    # STEP 6
    # NORMALIZE ML-1 BASE
    # ========================================================

    print(
        "\nNormalizing ML-1 base data..."
    )

    # Your base dataset previously used column "6"
    # as the state column.
    if "STATE_CLEAN" not in base_df.columns:

        if "6" in base_df.columns:

            base_df["STATE_CLEAN"] = (
                base_df["6"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        else:

            raise ValueError(
                "ML-1 base dataset does not contain "
                "'STATE_CLEAN' or column '6'."
            )

    base_df["ZIP_CLEAN"] = (
        base_df["ZIP_CLEAN"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    # ========================================================
    # STEP 7
    # CHECK ML-2 FEATURE COLUMNS
    # ========================================================

    required_base_columns = [
        "ZIP_CLEAN",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
        "specialty_diversity_ratio"
    ]

    missing_columns = [
        column
        for column in required_base_columns
        if column not in base_df.columns
    ]

    if missing_columns:

        raise ValueError(
            "ML-1 base dataset is missing required "
            f"columns: {missing_columns}"
        )

    # ========================================================
    # STEP 8
    # SELECT ONLY REQUIRED ML-1 FEATURES
    # ========================================================

    base_features = base_df[
        [
            "STATE_CLEAN",
            "ZIP_CLEAN",
            "zip_provider_share_of_state",
            "individual_provider_ratio",
            "organization_provider_ratio",
            "specialty_diversity_ratio"
        ]
    ].copy()

    # ========================================================
    # IMPORTANT
    #
    # BE-1 already performed state/county filtering.
    #
    # Therefore we do NOT perform another county filter here.
    #
    # We only need ML-1 feature values for the ZIPs
    # already returned by BE-1.
    # ========================================================

    candidate_zips = set(
        candidates["zip_clean"]
        .astype(str)
        .str.zfill(5)
    )

    print(
        "\nBE-1 candidate ZIPs:",
        len(candidate_zips)
    )

    # ========================================================
    # STEP 9
    # FILTER ML-1 BASE TO CANDIDATE ZIPS
    # ========================================================

    print(
        "\nFiltering ML-1 features to candidate ZIPs..."
    )

    base_features = base_features[
        base_features["ZIP_CLEAN"].isin(
            candidate_zips
        )
    ].copy()

    print(
        "Matching ML-1 rows:",
        len(base_features)
    )

    # ========================================================
    # STEP 10
    # HANDLE DUPLICATE ZIP ROWS
    # ========================================================

    duplicate_count = int(
        base_features["ZIP_CLEAN"]
        .duplicated()
        .sum()
    )

    print(
        "Duplicate matching ZIP rows:",
        duplicate_count
    )

    if duplicate_count > 0:

        print(
            "Keeping one ML-1 feature row per ZIP..."
        )

        base_features = (
            base_features
            .drop_duplicates(
                subset=["ZIP_CLEAN"],
                keep="first"
            )
            .copy()
        )

    # ========================================================
    # STEP 11
    # CREATE FAST ZIP LOOKUP
    # ========================================================

    print(
        "\nCreating ML-1 ZIP feature lookup..."
    )

    base_lookup = (
        base_features
        .set_index("ZIP_CLEAN")
    )

    # ========================================================
    # STEP 12
    # LOOK UP ML-1 FEATURES
    #
    # This replaces the slow/problematic merge.
    # ========================================================

    print(
        "\nAdding ML-1 features to candidates..."
    )

    candidates["zip_provider_share_of_state"] = (
        candidates["zip_clean"]
        .map(
            base_lookup[
                "zip_provider_share_of_state"
            ]
        )
    )

    print(
        "Added: zip_provider_share_of_state"
    )

    candidates["individual_provider_ratio"] = (
        candidates["zip_clean"]
        .map(
            base_lookup[
                "individual_provider_ratio"
            ]
        )
    )

    print(
        "Added: individual_provider_ratio"
    )

    candidates["organization_provider_ratio"] = (
        candidates["zip_clean"]
        .map(
            base_lookup[
                "organization_provider_ratio"
            ]
        )
    )

    print(
        "Added: organization_provider_ratio"
    )

    candidates["specialty_diversity"] = (
        candidates["zip_clean"]
        .map(
            base_lookup[
                "specialty_diversity_ratio"
            ]
        )
    )

    print(
        "Added: specialty_diversity"
    )

    # ========================================================
    # STEP 13
    # CREATE FINAL METADATA COLUMNS
    # ========================================================

    candidates["ZIP_CLEAN"] = (
        candidates["zip_clean"]
    )

    candidates["ZCTA_CLEAN"] = (
        candidates["zcta_clean"]
    )

    candidates["PRIMARY_TAXONOMY"] = (
        candidates["primary_taxonomy"]
    )

    # ========================================================
    # STEP 14
    # CHECK REQUIRED ML-2 FEATURES
    # ========================================================

    print(
        "\nChecking required ML-2 features..."
    )

    required_ml2_features = [
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
        "specialty_diversity"
    ]

    missing_mask = (
        candidates[
            required_ml2_features
        ]
        .isnull()
        .any(axis=1)
    )

    missing_count = int(
        missing_mask.sum()
    )

    complete_count = (
        len(candidates) - missing_count
    )

    print(
        "Candidates with complete features:",
        complete_count
    )

    print(
        "Candidates with missing features:",
        missing_count
    )

    # ========================================================
    # SHOW MISSING CANDIDATES
    # ========================================================

    if missing_count > 0:

        print(
            "\nCandidates removed because of "
            "missing ML-2 features:"
        )

        print(
            candidates.loc[
                missing_mask,
                [
                    "STATE_CLEAN",
                    "ZIP_CLEAN",
                    "PRIMARY_TAXONOMY",
                    "population",
                    "zip_provider_share_of_state",
                    "individual_provider_ratio",
                    "organization_provider_ratio",
                    "specialty_diversity"
                ]
            ].to_string(
                index=False
            )
        )

        candidates = (
            candidates[
                ~missing_mask
            ]
            .copy()
        )

    # ========================================================
    # STEP 15
    # FINAL COLUMNS
    # ========================================================

    final_columns = [
        "STATE_CLEAN",
        "ZIP_CLEAN",
        "ZCTA_CLEAN",
        "PRIMARY_TAXONOMY",
        "frontend_specialty",
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
        "specialty_diversity"
    ]

    # Keep columns that exist
    final_columns = [
        column
        for column in final_columns
        if column in candidates.columns
    ]

    candidates = (
        candidates[
            final_columns
        ]
        .copy()
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "FINAL ML-3 CANDIDATES:",
        len(candidates)
    )

    print(
        "========================================"
    )

    print(
        "\nFinal columns:"
    )

    print(
        candidates.columns.tolist()
    )

    print(
        "\nFirst 10 candidates:"
    )

    if len(candidates) > 0:

        print(
            candidates
            .head(10)
            .to_string(
                index=False
            )
        )

    else:

        print(
            "NO VALID CANDIDATES"
        )

    return candidates


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    candidates = prepare_candidates(
        state="Texas",
        counties=["Harris"],
        frontend_specialty="Cardiology"
    )

    print(
        "\nPrepared candidates:",
        len(candidates)
    )