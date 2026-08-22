"""
Train a specialty-level, geospatially-aware Random Forest classifier that
predicts healthcare "access gap" ZIP-specialty combinations (bottom-20%
provider density within specialty).

Enhancements over the original script:
  - Removed a redundant/dead BallTree computation loop in
    compute_geospatial_features (was ~2x the geospatial compute cost for
    no benefit).
  - Added logging (with --quiet) instead of raw prints.
  - Added --random-state, --test-size, --output-dir, --cv-folds CLI args.
  - Added optional stratified k-fold cross-validation alongside the
    holdout split for a more robust performance estimate.
  - Added upfront column validation with clear error messages.
  - Added type hints throughout.
  - Metadata now records sklearn version, random_state, test_size, and
    CV results for full run provenance.
"""

import argparse
import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (auc, classification_report,
                              precision_recall_curve, roc_auc_score)
from sklearn.model_selection import (StratifiedKFold, cross_validate,
                                      train_test_split)
from sklearn.neighbors import BallTree
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET_COL = "access_gap_target"
MIN_SPECIALTY_GROUP_SIZE_DEFAULT = 20
LEAKAGE_WARNING_THRESHOLD = 0.75
EARTH_RADIUS_KM = 6371.0
SEARCH_RADIUS_KM = 30.0

NUMERIC_FEATURES = [
    "population",
    "nearest_specialist_distance_km",
    "specialists_within_30km",
    "individual_provider_ratio",
    "organization_provider_ratio",
    "specialty_diversity",
]
CATEGORICAL_FEATURES = ["PRIMARY_TAXONOMY"]

logger = logging.getLogger("access_gap_trainer")


def configure_logging(quiet: bool = False) -> None:
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )


def _zero_pad_zip(series: pd.Series) -> pd.Series:
    """Normalize ZIP codes to 5-char zero-padded strings."""
    return series.astype(str).str.extract(r"(\d+)")[0].str.zfill(5)


def _require_columns(df: pd.DataFrame, cols: List[str], context: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing required columns for {context}: {missing}")


def compute_geospatial_features(df_spec: pd.DataFrame, df_zip: pd.DataFrame) -> pd.DataFrame:
    """Compute nearest specialist distance and count within 30km using BallTree.

    Uses provider-level lat/lon from NPPES (via specialty CSV) and ZIP centroids
    from the ZIP-level CSV. Falls back gracefully when coordinates are missing.
    """
    logger.info("🌍 Computing geospatial features...")

    lat_col = next((c for c in df_spec.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df_spec.columns if "lon" in c.lower() or "lng" in c.lower()), None)

    if not lat_col or not lon_col:
        logger.warning("⚠️ Lat/lon columns not found in specialty data. Skipping geospatial features.")
        df_spec["nearest_specialist_distance_km"] = np.nan
        df_spec["specialists_within_30km"] = np.nan
        return df_spec

    zip_lat_col = next((c for c in df_zip.columns if "lat" in c.lower()), None)
    zip_lon_col = next((c for c in df_zip.columns if "lon" in c.lower() or "lng" in c.lower()), None)

    if not zip_lat_col or not zip_lon_col:
        logger.warning("⚠️ Lat/lon columns not found in ZIP data. Skipping geospatial features.")
        df_spec["nearest_specialist_distance_km"] = np.nan
        df_spec["specialists_within_30km"] = np.nan
        return df_spec

    # Build area_id for both datasets if missing
    for df_ in (df_spec, df_zip):
        if "area_id" not in df_.columns:
            df_["area_id"] = df_["STATE_CLEAN"].astype(str) + "_" + _zero_pad_zip(df_["ZIP_CLEAN"])

    zip_centroids = df_zip[[zip_lat_col, zip_lon_col]].dropna().copy()
    zip_centroids.columns = ["zip_lat", "zip_lon"]

    if zip_centroids.empty:
        logger.warning("⚠️ No valid ZIP centroids found. Skipping geospatial features.")
        df_spec["nearest_specialist_distance_km"] = np.nan
        df_spec["specialists_within_30km"] = np.nan
        return df_spec

    unique_taxonomies = df_spec["PRIMARY_TAXONOMY"].unique()

    # Single, vectorized-per-taxonomy pass: build one BallTree per specialty
    # and query all ZIP centroids against it once. (The original script built
    # this same tree and ran this same query twice per specialty via a dead
    # first loop that discarded its results — removed here.)
    provider_locs = df_spec[[lat_col, lon_col, "PRIMARY_TAXONOMY", "area_id"]].dropna(
        subset=[lat_col, lon_col]
    ).copy()
    provider_locs.columns = ["prov_lat", "prov_lon", "taxonomy", "prov_area_id"]

    zip_locs = df_zip[["area_id", zip_lat_col, zip_lon_col]].dropna(
        subset=[zip_lat_col, zip_lon_col]
    ).copy()
    zip_locs.columns = ["zip_area_id", "zip_lat", "zip_lon"]
    zip_rad = np.radians(zip_locs[["zip_lat", "zip_lon"]].values)

    results = []
    total = len(unique_taxonomies)
    for i, taxonomy in enumerate(unique_taxonomies):
        if (i + 1) % 50 == 0:
            logger.info(f"  Processing specialty {i + 1}/{total}: {taxonomy}")

        tax_providers = provider_locs[provider_locs["taxonomy"] == taxonomy]
        if tax_providers.empty:
            continue

        prov_rad = np.radians(tax_providers[["prov_lat", "prov_lon"]].values)
        tree = BallTree(prov_rad, metric="haversine")

        dists, _ = tree.query(zip_rad, k=1)
        nearest_km = dists.flatten() * EARTH_RADIUS_KM

        counts = tree.query_radius(zip_rad, r=SEARCH_RADIUS_KM / EARTH_RADIUS_KM, count_only=True)

        results.append(pd.DataFrame({
            "zip_area_id": zip_locs["zip_area_id"].values,
            "PRIMARY_TAXONOMY": taxonomy,
            "nearest_specialist_distance_km": nearest_km,
            "specialists_within_30km": counts,
        }))

    if results:
        geo_df = pd.concat(results, ignore_index=True)
        geo_df = geo_df.rename(columns={"zip_area_id": "area_id"})
        df_spec = df_spec.merge(geo_df, on=["area_id", "PRIMARY_TAXONOMY"], how="left")
        logger.info(f"✅ Geospatial features computed for {len(geo_df)} ZIP-specialty combinations")
    else:
        df_spec["nearest_specialist_distance_km"] = np.nan
        df_spec["specialists_within_30km"] = np.nan
        logger.warning("⚠️ No geospatial features could be computed")

    return df_spec


def load_and_merge_data(
    drop_population: bool = False, log_population: bool = False
) -> Tuple[pd.DataFrame, List[str]]:
    """Load specialty-level data, compute geospatial features, and merge ZIP context."""
    logger.info("🔍 Loading specialty-level dataset...")
    spec_paths = [
        "data/processed/provider_network_ml_ready_specialty.csv",
        "data/provider_network_ml_ready_specialty.csv",
    ]
    spec_path = next((p for p in spec_paths if os.path.exists(p)), None)
    if not spec_path:
        raise FileNotFoundError("❌ Could not find provider_network_ml_ready_specialty.csv")

    logger.info("🔍 Loading ZIP-level dataset for context features...")
    zip_paths = [
        "data/processed/provider_network_ml_ready.csv",
        "data/provider_network_ml_ready.csv",
    ]
    zip_path = next((p for p in zip_paths if os.path.exists(p)), None)
    if not zip_path:
        raise FileNotFoundError("❌ Could not find provider_network_ml_ready.csv")

    df_spec = pd.read_csv(spec_path)
    df_zip = pd.read_csv(zip_path)

    _require_columns(df_spec, ["PRIMARY_TAXONOMY"], "specialty dataset")

    df_spec = compute_geospatial_features(df_spec, df_zip)

    for df_ in (df_zip, df_spec):
        if "area_id" not in df_.columns:
            _require_columns(df_, ["STATE_CLEAN", "ZIP_CLEAN"], "area_id construction")
            df_["area_id"] = df_["STATE_CLEAN"].astype(str) + "_" + _zero_pad_zip(df_["ZIP_CLEAN"])

    zip_context_cols = [
        "area_id", "population", "individual_provider_ratio",
        "organization_provider_ratio", "specialty_diversity",
    ]
    available_zip_cols = [c for c in zip_context_cols if c in df_zip.columns]
    df_zip_context = df_zip[available_zip_cols].drop_duplicates(subset=["area_id"])

    before = len(df_spec)
    df = df_spec.merge(df_zip_context, on="area_id", how="left")
    after = len(df)

    if after != before:
        logger.warning(f"🚨 Row count changed during merge ({before} → {after})")
    logger.info(f"✅ Merged {len(df_zip_context)} ZIP context records into {before} specialty rows → {after} rows")

    available_numeric = [c for c in NUMERIC_FEATURES if c in df.columns]
    missing = set(NUMERIC_FEATURES) - set(available_numeric)
    if missing:
        logger.warning(f"⚠️ Missing numeric features after merge: {missing}")
    else:
        logger.info(f"✅ All {len(available_numeric)} numeric features available")

    if drop_population and "population" in available_numeric:
        available_numeric = [c for c in available_numeric if c != "population"]
        logger.info("ℹ️ --drop-population: excluding population from training")
    elif log_population and "population" in df.columns:
        df["log_population"] = np.log1p(df["population"])
        available_numeric = ["log_population" if c == "population" else c for c in available_numeric]
        logger.info("ℹ️ --log-population: using log1p(population)")

    logger.info(f"🏥 Unique specialties: {df['PRIMARY_TAXONOMY'].nunique()}")
    return df, available_numeric


def define_access_gap_target(df: pd.DataFrame, min_group_size: int = MIN_SPECIALTY_GROUP_SIZE_DEFAULT) -> pd.DataFrame:
    """Define per-specialty bottom-20% access gap target."""
    logger.info("🎯 Defining Specialty-Level Access Gap Target...")
    density_col = "specialty_provider_density_per_1000"
    _require_columns(df, [density_col, "PRIMARY_TAXONOMY"], "target definition")

    initial = len(df)
    df = df.dropna(subset=[density_col]).copy()
    logger.info(f"  ℹ️ Dropped {initial - len(df)} rows with missing density")

    if df.empty:
        raise ValueError("❌ No rows remain after dropping missing density values.")

    group_sizes = df.groupby("PRIMARY_TAXONOMY").size()
    small_groups = group_sizes[group_sizes < min_group_size]
    if len(small_groups) > 0:
        logger.warning(f"  ⚠️ {len(small_groups)} specialties have <{min_group_size} rows ({small_groups.sum()} total)")

    df[TARGET_COL] = df.groupby("PRIMARY_TAXONOMY")[density_col].transform(
        lambda x: (x < x.quantile(0.20)).astype(int)
    )

    gap_count = df[TARGET_COL].sum()
    rate = gap_count / len(df) if len(df) else 0.0
    logger.info(f"✅ Target: {gap_count} gaps ({rate:.1%}) out of {len(df)} records")
    return df


def build_pipeline(
    numeric_features: List[str],
    categorical_features: List[str],
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    min_samples_leaf: int = 1,
    min_frequency: int = MIN_SPECIALTY_GROUP_SIZE_DEFAULT,
    random_state: int = 42,
) -> Pipeline:
    """Build preprocessing + RF pipeline."""
    preprocessor = ColumnTransformer(transformers=[
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=min_frequency), categorical_features),
    ])
    model = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        min_samples_leaf=min_samples_leaf, class_weight="balanced",
        random_state=random_state, n_jobs=-1,
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def run_cross_validation(
    pipeline: Pipeline, X: pd.DataFrame, y: pd.Series, cv_folds: int, random_state: int
) -> dict:
    """Run stratified k-fold CV and report mean/std PR-AUC and ROC-AUC."""
    logger.info(f"\n🔁 Running {cv_folds}-fold stratified cross-validation...")
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    scoring = {"roc_auc": "roc_auc", "average_precision": "average_precision"}
    cv_results = cross_validate(pipeline, X, y, cv=skf, scoring=scoring, n_jobs=-1)

    roc_mean, roc_std = cv_results["test_roc_auc"].mean(), cv_results["test_roc_auc"].std()
    pr_mean, pr_std = cv_results["test_average_precision"].mean(), cv_results["test_average_precision"].std()

    logger.info(f"  ROC-AUC: {roc_mean:.4f} ± {roc_std:.4f}")
    logger.info(f"  PR-AUC:  {pr_mean:.4f} ± {pr_std:.4f}")

    return {
        "roc_auc_mean": float(roc_mean), "roc_auc_std": float(roc_std),
        "pr_auc_mean": float(pr_mean), "pr_auc_std": float(pr_std),
        "n_folds": cv_folds,
    }


def evaluate_model(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[float, float]:
    """Evaluate and print classification report + AUC metrics."""
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    logger.info(f"\n{'=' * 50}")
    logger.info("📊 RANDOM FOREST REPORT (Geospatial + Context)")
    logger.info("=" * 50)
    logger.info("\n" + classification_report(y_test, y_pred, target_names=["Adequate (0)", "Access Gap (1)"]))

    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = auc(recall, precision)
    roc_auc = roc_auc_score(y_test, y_prob)
    logger.info(f"📈 PR-AUC:  {pr_auc:.4f}")
    logger.info(f"📈 ROC-AUC: {roc_auc:.4f}")
    logger.info("=" * 50)
    return pr_auc, roc_auc


def get_feature_importances(
    pipeline: Pipeline, numeric_features: List[str], categorical_features: List[str], top_n: int = 10
) -> List[Tuple[str, float]]:
    """Extract and roll up feature importances with leakage warning."""
    model = pipeline.named_steps["model"]
    encoder = pipeline.named_steps["preprocessor"].named_transformers_["cat"]
    cat_names = list(encoder.get_feature_names_out(categorical_features))
    all_names = numeric_features + cat_names
    importances = model.feature_importances_

    rolled = {feat: 0.0 for feat in numeric_features + categorical_features}
    for name, imp in zip(all_names, importances):
        matched_cat = next((c for c in categorical_features if name.startswith(f"{c}_") or name == c), None)
        key = matched_cat if matched_cat else name
        rolled[key] = rolled.get(key, 0.0) + imp

    ranked = sorted(rolled.items(), key=lambda x: x[1], reverse=True)
    logger.info("\n🌲 Feature Importances (rolled up)")
    logger.info("-" * 40)
    for name, score in ranked[:top_n]:
        logger.info(f"  {name:<40} {score:.4f}")
    logger.info("-" * 40)

    top_name, top_score = ranked[0]
    if top_score >= LEAKAGE_WARNING_THRESHOLD:
        logger.warning(f"\n🚨 LEAKAGE WARNING: '{top_name}' = {top_score:.1%} importance")

    return ranked


def save_artifacts(
    pipeline: Pipeline, pr_auc: float, roc_auc: float,
    numeric_features: List[str], categorical_features: List[str],
    feature_importances: List[Tuple[str, float]],
    args: argparse.Namespace, cv_results: Optional[dict] = None,
) -> None:
    """Save model and metadata artifacts."""
    os.makedirs(args.output_dir, exist_ok=True)
    joblib.dump(pipeline, os.path.join(args.output_dir, "final_model.joblib"))
    metadata = {
        "model_version": "v3.4-geospatial-context",
        "model_type": "random_forest",
        "trained_at_utc": datetime.utcnow().isoformat(),
        "sklearn_version": sklearn.__version__,
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "cross_validation": cv_results,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "feature_importances": {k: float(v) for k, v in feature_importances},
        "target_definition": "Bottom 20% specialty-specific density per ZIP",
        "geospatial_features": ["nearest_specialist_distance_km", "specialists_within_30km"],
        "search_radius_km": SEARCH_RADIUS_KM,
        "drop_population": args.drop_population,
        "log_population": args.log_population,
        "random_state": args.random_state,
        "test_size": args.test_size,
    }
    joblib.dump(metadata, os.path.join(args.output_dir, "model_metadata.joblib"))
    logger.info(f"\n💾 Model + metadata saved to {args.output_dir}/ (v3.4-geospatial)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train geospatial-aware access-gap RF")
    parser.add_argument("--drop-population", action="store_true")
    parser.add_argument("--log-population", action="store_true")
    parser.add_argument("--min-specialty-size", type=int, default=MIN_SPECIALTY_GROUP_SIZE_DEFAULT)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--output-dir", type=str, default="artifacts")
    parser.add_argument("--cv-folds", type=int, default=0,
                         help="If > 1, run stratified k-fold CV in addition to the holdout split.")
    parser.add_argument("--quiet", action="store_true", help="Only log warnings and errors.")
    args = parser.parse_args()
    if args.drop_population and args.log_population:
        parser.error("--drop-population and --log-population are mutually exclusive")
    if not (0.0 < args.test_size < 1.0):
        parser.error("--test-size must be between 0 and 1")
    return args


def main() -> None:
    args = parse_args()
    configure_logging(quiet=args.quiet)

    df, numeric_features = load_and_merge_data(
        drop_population=args.drop_population,
        log_population=args.log_population,
    )
    df = define_access_gap_target(df, min_group_size=args.min_specialty_size)

    X = df[numeric_features + CATEGORICAL_FEATURES]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )

    logger.info("\n🚀 Training Geospatial-Aware RF...")
    pipeline = build_pipeline(
        numeric_features, CATEGORICAL_FEATURES,
        n_estimators=args.n_estimators, max_depth=args.max_depth,
        min_frequency=args.min_specialty_size, random_state=args.random_state,
    )

    cv_results = None
    if args.cv_folds and args.cv_folds > 1:
        cv_results = run_cross_validation(pipeline, X, y, args.cv_folds, args.random_state)

    pipeline.fit(X_train, y_train)

    pr_auc, roc_auc = evaluate_model(pipeline, X_test, y_test)
    fi = get_feature_importances(pipeline, numeric_features, CATEGORICAL_FEATURES)
    save_artifacts(pipeline, pr_auc, roc_auc, numeric_features, CATEGORICAL_FEATURES, fi, args, cv_results)

    logger.info("\n✅ Geospatial-Aware Training Complete!")


if __name__ == "__main__":
    main()