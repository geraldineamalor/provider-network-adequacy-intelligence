import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_PATH = (
    r"C:\Users\Roshini\OneDrive\Desktop\Provider-Network-Project"
    r"\data"
)

BE3_PATH = BASE_PATH + r"\be3_final_281478.csv"
ML2_PATH = BASE_PATH + r"\ml2_predictions.csv"
OUTPUT_PATH = BASE_PATH + r"\ml3_recommendations.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\nLoading ML-2 predictions...", flush=True)

    ml2 = pd.read_csv(ML2_PATH)

    print(
        f"ML-2 predictions: {len(ml2)}",
        flush=True
    )

    print(
        "\nLoading BE-3 dataset...",
        flush=True
    )

    be3 = pd.read_csv(
        BE3_PATH,
        low_memory=False
    )

    print(
        f"BE-3 rows: {len(be3)}",
        flush=True
    )

    return ml2, be3


# ============================================================
# NORMALIZE ML-2
# ============================================================

def normalize_ml2(ml2):

    print(
        "\nNormalizing ML-2...",
        flush=True
    )

    ml2["ZIP_CLEAN"] = (
        ml2["ZIP_CLEAN"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    ml2["PRIMARY_TAXONOMY"] = (
        ml2["PRIMARY_TAXONOMY"]
        .astype(str)
        .str.strip()
    )

    return ml2


# ============================================================
# NORMALIZE BE-3
# ============================================================

def normalize_be3(be3):

    print(
        "\nNormalizing BE-3...",
        flush=True
    )

    be3["zip_clean"] = (
        be3["zip_clean"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    be3["Healthcare Provider Taxonomy Code_1"] = (
        be3[
            "Healthcare Provider Taxonomy Code_1"
        ]
        .astype(str)
        .str.strip()
    )

    be3["spatial_metric_policy"] = (
        be3["spatial_metric_policy"]
        .astype(str)
        .str.strip()
    )

    return be3


# ============================================================
# FILTER BE-3 TO ONLY ML-2 CANDIDATES
# ============================================================

def filter_be3_to_candidates(ml2, be3):

    print(
        "\nFiltering BE-3 to ML-2 candidate ZIP + taxonomy...",
        flush=True
    )

    candidate_keys = (
        ml2[
            [
                "ZIP_CLEAN",
                "PRIMARY_TAXONOMY"
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    print(
        f"Unique ML-2 candidate combinations: "
        f"{len(candidate_keys)}",
        flush=True
    )

    # Rename BE-3 columns temporarily
    be3_temp = be3.rename(
        columns={
            "zip_clean": "ZIP_CLEAN",
            "Healthcare Provider Taxonomy Code_1":
                "PRIMARY_TAXONOMY"
        }
    )

    # Keep only rows matching our candidates
    filtered = be3_temp.merge(
        candidate_keys,
        on=[
            "ZIP_CLEAN",
            "PRIMARY_TAXONOMY"
        ],
        how="inner"
    )

    print(
        f"BE-3 matching rows: {len(filtered)}",
        flush=True
    )

    return filtered


# ============================================================
# PREPARE BE-3 EVIDENCE
# ============================================================

def prepare_be3_evidence(be3):

    print(
        "\nPreparing BE-3 geographic evidence...",
        flush=True
    )

    # --------------------------------------------------------
    # Determine policy for each ZIP + taxonomy
    # --------------------------------------------------------

    policy_priority = {
        "provider_level": 1,
        "area_level_fallback": 2,
        "unresolved": 3
    }

    def choose_policy(series):

        policies = set(
            series.dropna()
            .astype(str)
            .str.strip()
        )

        if "provider_level" in policies:
            return "provider_level"

        if "area_level_fallback" in policies:
            return "area_level_fallback"

        return "unresolved"

    policies = (
        be3
        .groupby(
            [
                "ZIP_CLEAN",
                "PRIMARY_TAXONOMY"
            ]
        )["spatial_metric_policy"]
        .agg(choose_policy)
        .reset_index()
    )

    print(
        f"Unique matched ZIP + taxonomy combinations: "
        f"{len(policies)}",
        flush=True
    )

    # --------------------------------------------------------
    # AREA-LEVEL AGGREGATION
    # --------------------------------------------------------

    area = be3[
        be3["spatial_metric_policy"]
        == "area_level_fallback"
    ].copy()

    print(
        f"Area-level BE-3 rows: {len(area)}",
        flush=True
    )

    if not area.empty:

        area_columns = [
            "ZIP_CLEAN",
            "PRIMARY_TAXONOMY",
            "area_provider_count_5mi",
            "area_provider_count_10mi",
            "area_provider_count_25mi",
            "area_provider_count_50mi",
            "area_provider_count_100mi",
            "area_same_taxonomy_count_5mi",
            "area_same_taxonomy_count_10mi",
            "area_same_taxonomy_count_25mi",
            "area_same_taxonomy_count_50mi",
            "area_same_taxonomy_count_100mi"
        ]

        area = area[
            area_columns
        ]

        area = (
            area
            .groupby(
                [
                    "ZIP_CLEAN",
                    "PRIMARY_TAXONOMY"
                ],
                as_index=False
            )
            .median(
                numeric_only=True
            )
        )

    # --------------------------------------------------------
    # PROVIDER-LEVEL AGGREGATION
    # --------------------------------------------------------

    provider = be3[
        be3["spatial_metric_policy"]
        == "provider_level"
    ].copy()

    print(
        f"Provider-level BE-3 rows: {len(provider)}",
        flush=True
    )

    if not provider.empty:

        provider_columns = [
            "ZIP_CLEAN",
            "PRIMARY_TAXONOMY",
            "nearest_provider_distance_miles",
            "second_nearest_provider_distance_miles",
            "provider_count_5mi",
            "provider_count_10mi",
            "provider_count_25mi",
            "provider_count_50mi",
            "provider_count_100mi",
            "same_taxonomy_count_5mi",
            "same_taxonomy_count_10mi",
            "same_taxonomy_count_25mi",
            "same_taxonomy_count_50mi",
            "same_taxonomy_count_100mi"
        ]

        provider = provider[
            provider_columns
        ]

        provider = (
            provider
            .groupby(
                [
                    "ZIP_CLEAN",
                    "PRIMARY_TAXONOMY"
                ],
                as_index=False
            )
            .median(
                numeric_only=True
            )
        )

    # --------------------------------------------------------
    # COMBINE POLICY + EVIDENCE
    # --------------------------------------------------------

    result = policies.copy()

    print(
        "\nCombining BE-3 evidence...",
        flush=True
    )

    if not area.empty:

        result = result.merge(
            area,
            on=[
                "ZIP_CLEAN",
                "PRIMARY_TAXONOMY"
            ],
            how="left"
        )

    if not provider.empty:

        result = result.merge(
            provider,
            on=[
                "ZIP_CLEAN",
                "PRIMARY_TAXONOMY"
            ],
            how="left"
        )

    # --------------------------------------------------------
    # Geographic evidence status
    # --------------------------------------------------------

    result["geographic_evidence_status"] = (
        result["spatial_metric_policy"]
        .map(
            {
                "provider_level": "available",
                "area_level_fallback": "available",
                "unresolved": "insufficient"
            }
        )
        .fillna("insufficient")
    )

    print(
        f"BE-3 evidence records created: {len(result)}",
        flush=True
    )

    return result


# ============================================================
# MERGE ML-2 + BE-3
# ============================================================

def merge_ml2_be3(ml2, be3_evidence):

    print(
        "\nMerging ML-2 predictions with BE-3 evidence...",
        flush=True
    )

    result = ml2.merge(
        be3_evidence,
        on=[
            "ZIP_CLEAN",
            "PRIMARY_TAXONOMY"
        ],
        how="left"
    )

    print(
        f"Final merged candidates: {len(result)}",
        flush=True
    )

    return result


# ============================================================
# RANK CANDIDATES
# ============================================================

def rank_candidates(df):

    print(
        "\nRanking candidates by access_gap_score...",
        flush=True
    )

    # --------------------------------------------------------
    # Primary ranking signal
    # --------------------------------------------------------

    df = df.sort_values(
        by="access_gap_score",
        ascending=False
    ).reset_index(
        drop=True
    )

    df["rank"] = (
        df.index + 1
    )

    return df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        "ML-3 RECRUITMENT RANKING"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # 1. LOAD
    # --------------------------------------------------------

    ml2, be3 = load_data()

    # --------------------------------------------------------
    # 2. NORMALIZE
    # --------------------------------------------------------

    ml2 = normalize_ml2(
        ml2
    )

    be3 = normalize_be3(
        be3
    )

    # --------------------------------------------------------
    # 3. FILTER BE-3
    #
    # VERY IMPORTANT:
    # Only process BE-3 rows relevant to the
    # 273 ML-2 candidates.
    # --------------------------------------------------------

    be3_filtered = filter_be3_to_candidates(
        ml2,
        be3
    )

    # Free original BE-3 memory
    del be3

    # --------------------------------------------------------
    # 4. PREPARE BE-3 EVIDENCE
    # --------------------------------------------------------

    be3_evidence = prepare_be3_evidence(
        be3_filtered
    )

    # --------------------------------------------------------
    # Free filtered data
    # --------------------------------------------------------

    del be3_filtered

    # --------------------------------------------------------
    # 5. MERGE
    # --------------------------------------------------------

    result = merge_ml2_be3(
        ml2,
        be3_evidence
    )

    # Mark candidates without BE-3 evidence explicitly
    result["spatial_metric_policy"] = (
        result["spatial_metric_policy"]
        .fillna("unresolved")
    )

    result["geographic_evidence_status"] = (
        result["geographic_evidence_status"]
        .fillna("insufficient")
    )

    # --------------------------------------------------------
    # 6. RANK
    # --------------------------------------------------------

    result = rank_candidates(
        result
    )

    # --------------------------------------------------------
    # 7. SAVE
    # --------------------------------------------------------

    print(
        "\nSaving ML-3 recommendations...",
        flush=True
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # --------------------------------------------------------
    # 8. DISPLAY
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        "FINAL ML-3 RESULTS"
    )

    print(
        "========================================"
    )

    print(
        f"Total recommendations: {len(result)}"
    )

    display_columns = [
        "rank",
        "STATE_CLEAN",
        "ZIP_CLEAN",
        "PRIMARY_TAXONOMY",
        "population",
        "prediction",
        "access_gap_score",
        "gap_category",
        "spatial_metric_policy",
        "geographic_evidence_status"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in result.columns
    ]

    print(
        "\nTop 20 recruitment candidates:"
    )

    print(
        result[
            available_columns
        ]
        .head(20)
        .to_string(index=False)
    )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_PATH
    )