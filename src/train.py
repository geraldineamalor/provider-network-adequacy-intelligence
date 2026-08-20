import argparse
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, precision_recall_curve, auc, roc_auc_score

TARGET_COL = 'access_gap_target'
MIN_SPECIALTY_GROUP_SIZE_DEFAULT = 20
LEAKAGE_WARNING_THRESHOLD = 0.75  # single feature importance share that triggers a leakage warning

# Features from ZIP-level dataset to merge into specialty-level data
ZIP_CONTEXT_FEATURES = [
    'population',
    'zip_provider_share_of_state',
    'individual_provider_ratio',
    'organization_provider_ratio',
    'specialty_diversity'
]

# NOTE: 'population' is a known leakage risk — it's very likely the
# denominator used to compute 'specialty_provider_density_per_1000', which
# the target is derived from. It's kept here by default for comparison, but
# use --drop-population (or --log-population) to test whether the model
# still performs well without it. See the leakage warning this script
# prints at the importance-rollup stage.
NUMERIC_FEATURES = [
    'population',
    'zip_provider_share_of_state',
    'individual_provider_ratio',
    'organization_provider_ratio',
    'specialty_diversity'
]
CATEGORICAL_FEATURES = ['PRIMARY_TAXONOMY']


def _zero_pad_zip(series):
    """Normalize ZIP codes to 5-char zero-padded strings so joins don't
    silently fail when one file stored ZIPs as int (dropping leading
    zeros) and another stored them as string."""
    return series.astype(str).str.extract(r'(\d+)')[0].str.zfill(5)


def load_and_merge_data(drop_population=False, log_population=False):
    """Load specialty-level data and merge ZIP-level contextual features."""
    print("🔍 Loading specialty-level dataset...")
    spec_paths = ["data/processed/provider_network_ml_ready_specialty.csv",
                  "data/provider_network_ml_ready_specialty.csv"]
    spec_path = next((p for p in spec_paths if os.path.exists(p)), None)
    if not spec_path:
        raise FileNotFoundError("❌ Could not find provider_network_ml_ready_specialty.csv")

    print("🔍 Loading ZIP-level dataset for context features...")
    zip_paths = ["data/processed/provider_network_ml_ready.csv",
                 "data/provider_network_ml_ready.csv"]
    zip_path = next((p for p in zip_paths if os.path.exists(p)), None)
    if not zip_path:
        raise FileNotFoundError("❌ Could not find provider_network_ml_ready.csv")

    df_spec = pd.read_csv(spec_path)
    df_zip = pd.read_csv(zip_path)

    # Build area_id join key if missing. ZIP codes are zero-padded before
    # concatenation so "07030" in one file and 7030 (read as int) in the
    # other still match instead of silently failing to join.
    for df_ in (df_zip, df_spec):
        if 'area_id' not in df_.columns:
            df_['area_id'] = df_['STATE_CLEAN'].astype(str) + '_' + _zero_pad_zip(df_['ZIP_CLEAN'])

    # Select only the context features + join key from ZIP data
    zip_cols = ['area_id'] + [c for c in ZIP_CONTEXT_FEATURES if c in df_zip.columns]
    df_zip_context = df_zip[zip_cols].drop_duplicates(subset=['area_id'])

    # Merge
    before = len(df_spec)
    df = df_spec.merge(df_zip_context, on='area_id', how='left')
    after = len(df)
    if after != before:
        print(
            f"  🚨 Row count changed during merge ({before} → {after}). The ZIP context "
            "table likely has duplicate area_id values that weren't caught by "
            "drop_duplicates — investigate before trusting this model."
        )
    print(f"✅ Merged {len(df_zip_context)} ZIP context records into {before} specialty rows → {after} rows")

    # Verify features are now present, and check the merge actually matched
    available_numeric = [c for c in NUMERIC_FEATURES if c in df.columns]
    missing = set(NUMERIC_FEATURES) - set(available_numeric)
    if missing:
        print(f"⚠️ Still missing numeric features after merge: {missing}")
    else:
        print(f"✅ All {len(available_numeric)} numeric context features available")

    if available_numeric:
        unmatched = df[available_numeric[0]].isna().sum()
        if unmatched > 0:
            print(
                f"  ⚠️ {unmatched} rows ({unmatched/after:.1%}) had no matching area_id "
                "in the ZIP context table and will get median-imputed context features. "
                "If this is a large share, check ZIP/state formatting between the two files."
            )

    if drop_population and 'population' in available_numeric:
        available_numeric = [c for c in available_numeric if c != 'population']
        print("  ℹ️ --drop-population set: excluding 'population' from training features")
    elif log_population and 'population' in df.columns:
        df['log_population'] = np.log1p(df['population'])
        available_numeric = ['log_population' if c == 'population' else c for c in available_numeric]
        print("  ℹ️ --log-population set: using log1p(population) instead of raw population")

    print(f"🏥 Unique specialties: {df['PRIMARY_TAXONOMY'].nunique()}")
    return df, available_numeric


def define_access_gap_target(df, min_group_size=MIN_SPECIALTY_GROUP_SIZE_DEFAULT):
    print("🎯 Defining Specialty-Level Access Gap Target...")
    density_col = 'specialty_provider_density_per_1000'
    if density_col not in df.columns:
        raise ValueError(f"❌ '{density_col}' not found.")

    initial = len(df)
    df = df.dropna(subset=[density_col]).copy()
    print(f"  ℹ️ Dropped {initial - len(df)} rows with missing density")

    group_sizes = df.groupby('PRIMARY_TAXONOMY').size()
    small_groups = group_sizes[group_sizes < min_group_size]
    if len(small_groups) > 0:
        print(
            f"  ⚠️ {len(small_groups)} specialties have fewer than {min_group_size} rows "
            f"({small_groups.sum()} rows total) — their per-specialty threshold will be noisy."
        )

    # Per-specialty bottom 20% threshold
    df[TARGET_COL] = df.groupby('PRIMARY_TAXONOMY')[density_col].transform(
        lambda x: (x < x.quantile(0.20)).astype(int)
    )

    gap_count = df[TARGET_COL].sum()
    print(f"✅ Target: {gap_count} gaps ({gap_count/len(df):.1%}) out of {len(df)} records")
    return df


def build_pipeline(
    numeric_features,
    categorical_features,
    n_estimators=100,
    max_depth=None,
    min_samples_leaf=1,
    min_frequency=MIN_SPECIALTY_GROUP_SIZE_DEFAULT,
    random_state=42,
):
    preprocessor = ColumnTransformer(transformers=[
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore', min_frequency=min_frequency), categorical_features)
    ])
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        class_weight='balanced',
        random_state=random_state,
        n_jobs=-1
    )
    return Pipeline(steps=[('preprocessor', preprocessor), ('model', model)])


def evaluate_model(pipeline, X_test, y_test):
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    print(f"\n{'='*50}")
    print("📊 RANDOM FOREST REPORT (Specialty-Aware + Context)")
    print('='*50)
    print(classification_report(y_test, y_pred, target_names=['Adequate (0)', 'Access Gap (1)']))

    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = auc(recall, precision)
    roc_auc = roc_auc_score(y_test, y_prob)
    print(f"📈 PR-AUC:  {pr_auc:.4f}")
    print(f"📈 ROC-AUC: {roc_auc:.4f}")
    print('='*50)
    return pr_auc, roc_auc


def get_feature_importances(pipeline, numeric_features, categorical_features, top_n=10):
    model = pipeline.named_steps['model']
    encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat']
    cat_names = list(encoder.get_feature_names_out(categorical_features))
    all_names = numeric_features + cat_names
    importances = model.feature_importances_

    # Roll up one-hot encoded specialty importances back into their parent
    # categorical column. FIX: match on the full categorical column name
    # (e.g. "PRIMARY_TAXONOMY"), not name.split('_')[0], which previously
    # truncated "PRIMARY_TAXONOMY_207Q00000X" down to just "PRIMARY".
    rolled = {feat: 0.0 for feat in numeric_features + categorical_features}
    for name, imp in zip(all_names, importances):
        matched_cat = next((c for c in categorical_features if name.startswith(f"{c}_") or name == c), None)
        rolled[matched_cat if matched_cat else name] = rolled.get(matched_cat if matched_cat else name, 0.0) + imp

    ranked = sorted(rolled.items(), key=lambda x: x[1], reverse=True)
    print("\n🌲 Feature Importances (rolled up)")
    print('-'*40)
    for name, score in ranked[:top_n]:
        print(f"  {name:<35} {score:.4f}")
    print('-'*40)

    top_name, top_score = ranked[0]
    if top_score >= LEAKAGE_WARNING_THRESHOLD:
        print(
            f"\n🚨 LEAKAGE WARNING: '{top_name}' alone accounts for {top_score:.1%} of "
            "importance. If this feature feeds into the density calculation the target "
            "is derived from (e.g. as its denominator), the model may mostly be learning "
            "that arithmetic rather than real access-gap signal. Try --drop-population "
            "or --log-population and compare PR-AUC before trusting this model."
        )

    return ranked


def save_artifacts(pipeline, pr_auc, roc_auc, numeric_features, categorical_features, feature_importances, args):
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(pipeline, "artifacts/final_model.joblib")
    metadata = {
        "model_version": "v3.2-specialty-context-merged",
        "model_type": "random_forest",
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "feature_importances": {k: float(v) for k, v in feature_importances},
        "target_definition": "Bottom 20% specialty-specific density per ZIP",
        "drop_population": args.drop_population,
        "log_population": args.log_population,
    }
    joblib.dump(metadata, "artifacts/model_metadata.joblib")
    print(f"\n💾 Model + metadata saved (v3.2)")


def parse_args():
    parser = argparse.ArgumentParser(description="Train specialty-aware access-gap Random Forest")
    parser.add_argument('--drop-population', action='store_true',
                         help="Exclude 'population' entirely (leakage ablation)")
    parser.add_argument('--log-population', action='store_true',
                         help="Use log1p(population) instead of raw population (softens leakage/skew)")
    parser.add_argument('--min-specialty-size', type=int, default=MIN_SPECIALTY_GROUP_SIZE_DEFAULT,
                         help="Specialties with fewer rows get a noisy target threshold + get OHE-bucketed")
    parser.add_argument('--n-estimators', type=int, default=100)
    parser.add_argument('--max-depth', type=int, default=None)
    args = parser.parse_args()
    if args.drop_population and args.log_population:
        parser.error("--drop-population and --log-population are mutually exclusive")
    return args


if __name__ == "__main__":
    args = parse_args()

    df, numeric_features = load_and_merge_data(
        drop_population=args.drop_population,
        log_population=args.log_population,
    )
    df = define_access_gap_target(df, min_group_size=args.min_specialty_size)

    X = df[numeric_features + CATEGORICAL_FEATURES]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n🚀 Training Specialty-Aware RF with Merged Context...")
    pipeline = build_pipeline(
        numeric_features,
        CATEGORICAL_FEATURES,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_frequency=args.min_specialty_size,
    )
    pipeline.fit(X_train, y_train)

    pr_auc, roc_auc = evaluate_model(pipeline, X_test, y_test)
    fi = get_feature_importances(pipeline, numeric_features, CATEGORICAL_FEATURES)
    save_artifacts(pipeline, pr_auc, roc_auc, numeric_features, CATEGORICAL_FEATURES, fi, args)

    print("\n✅ Specialty-Aware + Context Training Complete!")