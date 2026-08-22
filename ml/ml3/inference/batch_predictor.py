import pandas as pd
import joblib

from prepare_candidates import prepare_candidates


# ======================================================
# PATHS
# ======================================================

MODEL_PATH = (
    r"C:\Users\Roshini\OneDrive\Desktop\Provider-Network-Project"
    r"\artifacts\final_model.joblib"
)

OUTPUT_PATH = (
    r"C:\Users\Roshini\OneDrive\Desktop\Provider-Network-Project"
    r"\data\ml2_predictions.csv"
)


# ======================================================
# LOAD MODEL
# ======================================================

def load_model():
    return joblib.load(MODEL_PATH)


# ======================================================
# GAP CATEGORY
# ======================================================

def get_gap_category(score):

    if score >= 0.7:
        return "high"

    elif score >= 0.4:
        return "medium"

    else:
        return "low"


# ======================================================
# PREDICT CANDIDATES
# ======================================================

def predict_candidates(
    state,
    counties,
    frontend_specialty
):

    # --------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------

    model = load_model()

    print("\n========================================")
    print("ML-2 BATCH PREDICTION")
    print("========================================")

    print("\nModel loaded successfully!")

    print(f"\nState: {state}")
    print(f"Counties: {counties}")
    print(f"Frontend specialty: {frontend_specialty}")

    # --------------------------------------------------
    # PREPARE CANDIDATES
    # --------------------------------------------------

    print("\nPreparing candidates...")

    candidates = prepare_candidates(
        state=state,
        counties=counties,
        frontend_specialty=frontend_specialty
    )

    print(
        f"\nValid candidates for prediction: "
        f"{len(candidates)}"
    )

    if candidates.empty:
        print("\nNo valid candidates found.")
        return pd.DataFrame()

    # ==================================================
    # ML-2 REQUIRED NUMERIC FEATURES
    # ==================================================

    numeric_features = [
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
        "specialty_diversity"
    ]

    # --------------------------------------------------
    # VERIFY NUMERIC FEATURES
    # --------------------------------------------------

    missing_numeric = [
        column
        for column in numeric_features
        if column not in candidates.columns
    ]

    if missing_numeric:

        raise ValueError(
            "\nMissing required numeric features: "
            + ", ".join(missing_numeric)
        )

    # --------------------------------------------------
    # VERIFY PRIMARY TAXONOMY
    #
    # The existing saved model pipeline requires this
    # column, as confirmed by model.predict().
    # --------------------------------------------------

    if "PRIMARY_TAXONOMY" not in candidates.columns:

        raise ValueError(
            "\nPRIMARY_TAXONOMY is missing from "
            "the candidate dataframe."
        )

    # ==================================================
    # BUILD MODEL INPUT
    # ==================================================

    model_columns = [
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
        "specialty_diversity",
        "PRIMARY_TAXONOMY"
    ]

    model_input = candidates[
        model_columns
    ].copy()

    print("\nModel input columns:")

    for column in model_input.columns:
        print(f"  {column}")

    print(
        f"\nModel input shape: "
        f"{model_input.shape}"
    )

    # ==================================================
    # CHECK NULL VALUES
    # ==================================================

    null_counts = model_input.isnull().sum()

    if null_counts.any():

        print(
            "\nERROR: Missing values found:"
        )

        print(
            null_counts[
                null_counts > 0
            ]
        )

        raise ValueError(
            "\nModel input contains missing values."
        )

    print(
        "\nAll model input values are complete."
    )

    # ==================================================
    # BATCH PREDICTION
    # ==================================================

    print(
        "\nRunning ML-2 batch prediction..."
    )

    predictions = model.predict(
        model_input
    )

    probabilities = model.predict_proba(
        model_input
    )

    # --------------------------------------------------
    # CLASS 1 = ACCESS GAP
    # --------------------------------------------------

    access_gap_scores = (
        probabilities[:, 1]
    )

    # ==================================================
    # BUILD RESULTS
    # ==================================================

    result_columns = [
        "STATE_CLEAN",
        "ZIP_CLEAN",
        "ZCTA_CLEAN",
        "PRIMARY_TAXONOMY",
        "frontend_specialty",
        "population"
    ]

    result_columns = [
        column
        for column in result_columns
        if column in candidates.columns
    ]

    results = candidates[
        result_columns
    ].copy()

    # --------------------------------------------------
    # ADD PREDICTION
    # --------------------------------------------------

    results["prediction"] = (
        predictions.astype(int)
    )

    # --------------------------------------------------
    # ADD ACCESS GAP SCORE
    # --------------------------------------------------

    results["access_gap_score"] = (
        access_gap_scores.astype(float)
    )

    # --------------------------------------------------
    # ADD CATEGORY
    # --------------------------------------------------

    results["gap_category"] = (
        results[
            "access_gap_score"
        ].apply(get_gap_category)
    )

    # ==================================================
    # RANK
    # ==================================================

    results = results.sort_values(
        by="access_gap_score",
        ascending=False
    ).reset_index(drop=True)

    results.insert(
        0,
        "rank",
        range(
            1,
            len(results) + 1
        )
    )

    return results


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # CURRENT TEST
    #
    # Texas + Harris + Cardiology
    # --------------------------------------------------

    results = predict_candidates(
        state="Texas",
        counties=[
            "Harris"
        ],
        frontend_specialty="Cardiology"
    )

    # --------------------------------------------------
    # STOP IF EMPTY
    # --------------------------------------------------

    if results.empty:

        raise SystemExit(
            "\nNo predictions generated."
        )

    # ==================================================
    # RESULTS
    # ==================================================

    print(
        "\n========================================"
    )

    print(
        "ML-2 PREDICTION RESULTS"
    )

    print(
        "========================================"
    )

    print(
        "\nTotal predictions:",
        len(results)
    )

    # --------------------------------------------------
    # TOP 20
    # --------------------------------------------------

    print(
        "\nTop 20 recruitment candidates:"
    )

    print(
        results.head(20).to_string(
            index=False
        )
    )

    # ==================================================
    # SCORE DISTRIBUTION
    # ==================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "ACCESS GAP SCORE DISTRIBUTION"
    )

    print(
        "=" * 60
    )

    print(
        results[
            "access_gap_score"
        ].describe()
    )

    # ==================================================
    # GAP CATEGORY DISTRIBUTION
    # ==================================================

    print(
        "\nGap category distribution:"
    )

    print(
        results[
            "gap_category"
        ].value_counts()
    )

    # ==================================================
    # PREDICTION DISTRIBUTION
    # ==================================================

    print(
        "\nPrediction distribution:"
    )

    print(
        results[
            "prediction"
        ].value_counts()
    )

    # ==================================================
    # EXACT SCORE COUNTS
    # ==================================================

    exact_one_count = (
        results[
            "access_gap_score"
        ] == 1.0
    ).sum()

    exact_zero_count = (
        results[
            "access_gap_score"
        ] == 0.0
    ).sum()

    print(
        "\nCandidates with "
        "access_gap_score = 1.0:",
        exact_one_count
    )

    print(
        "Candidates with "
        "access_gap_score = 0.0:",
        exact_zero_count
    )

    # ==================================================
    # SAVE
    # ==================================================

    results.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        "\n========================================"
    )

    print(
        "ML-2 PREDICTIONS SAVED"
    )

    print(
        "========================================"
    )

    print(
        OUTPUT_PATH
    )