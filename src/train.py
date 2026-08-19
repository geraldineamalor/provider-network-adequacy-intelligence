import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, precision_recall_curve, auc

TARGET_COL = 'access_gap_target'

# 🎯 EXPLICIT FEATURE LIST
# We only train on contextual/ratio features. We intentionally exclude raw counts and density to prevent leakage.
ALLOWED_FEATURES = [
    'population',
    'zip_provider_share_of_state',
    'individual_provider_ratio',
    'organization_provider_ratio',
    'specialty_diversity'  # Included if ML-1 created it
]


def load_and_prepare_data():
    print("🔍 Searching for ML-1's real dataset...")
    possible_paths = ["data/processed/provider_network_ml_ready.csv", "data/provider_network_ml_ready.csv"]

    filepath = next((path for path in possible_paths if os.path.exists(path)), None)
    if not filepath:
        raise FileNotFoundError("❌ Could not find provider_network_ml_ready.csv")

    print(f"✅ Loading data from: {filepath}")
    df = pd.read_csv(filepath)

    # Filter to only allowed features that actually exist in the dataframe
    training_features = [col for col in ALLOWED_FEATURES if col in df.columns]

    print(f"📊 Dataset shape: {df.shape}")
    print(f"📈 Training on {len(training_features)} contextual features: {training_features}")

    return df, training_features


def define_access_gap_target(df):
    print("🎯 Defining Access Gap Target...")

    density_col = 'providers_per_10000'
    if density_col not in df.columns:
        raise ValueError(f"❌ Target definition column '{density_col}' not found in dataset.")

    # Drop rows where density is NaN so we can calculate a clean threshold and label
    initial_rows = len(df)
    df = df.dropna(subset=[density_col]).copy()
    print(f"  ℹ️ Dropped {initial_rows - len(df)} rows with missing density for target definition.")

    # Bottom 20% of valid areas
    threshold = df[density_col].quantile(0.20)
    print(f"  ℹ️ Density threshold (20th percentile): {threshold:.2f} providers per 10k")

    # Define Target: 1 if in bottom 20%, else 0
    df[TARGET_COL] = (df[density_col] < threshold).astype(int)

    gap_count = df[TARGET_COL].sum()
    print(f"✅ Target defined: {gap_count} Access Gaps ({gap_count/len(df):.1%}) out of {len(df)} areas.")

    return df


def build_pipeline(n_estimators=100, max_depth=None, min_samples_leaf=1, random_state=42):
    """Build the Random Forest pipeline. Hyperparameters are exposed as
    arguments so they can be tuned (e.g. via grid/random search) without
    editing the function body."""
    imputer = SimpleImputer(strategy='median')
    scaler = StandardScaler()  # kept for consistency / future model swaps; RF doesn't strictly need it

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        class_weight='balanced',
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline(steps=[('imputer', imputer), ('scaler', scaler), ('model', model)])


def evaluate_model(pipeline, X_test, y_test, model_name="Random Forest"):
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    print(f"\n{'='*40}")
    print(f"📊 {model_name.upper()} REPORT")
    print('='*40)
    print(classification_report(y_test, y_pred, target_names=['Adequate (0)', 'Access Gap (1)']))

    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = auc(recall, precision)
    print(f"📈 {model_name} PR-AUC: {pr_auc:.4f}")
    print('='*40)
    return pr_auc


def get_feature_importances(pipeline, feature_names):
    """Extract and print Random-Forest feature importances (a nice bonus
    that wasn't available in the logistic-regression comparison)."""
    importances = pipeline.named_steps['model'].feature_importances_
    ranked = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)

    print("\n🌲 Feature Importances")
    print('-'*40)
    for name, score in ranked:
        print(f"  {name:<35} {score:.4f}")
    print('-'*40)

    return ranked


def save_artifacts(pipeline, pr_auc, features_used, feature_importances):
    os.makedirs("artifacts", exist_ok=True)
    model_path = "artifacts/final_model.joblib"
    joblib.dump(pipeline, model_path)
    print(f"\n💾 🏆 MODEL (random_forest) saved to {model_path}")

    metadata = {
        "model_version": "v2.4-rf-only",
        "model_type": "random_forest",
        "pr_auc": float(pr_auc),
        "features_used": features_used,
        "feature_importances": {name: float(score) for name, score in feature_importances},
    }
    joblib.dump(metadata, "artifacts/model_metadata.joblib")
    print("💾 Metadata saved to artifacts/model_metadata.joblib")


if __name__ == "__main__":
    df, training_features = load_and_prepare_data()
    df = define_access_gap_target(df)

    X = df[training_features]
    y = df[TARGET_COL]

    # Stratify ensures the 20% gap ratio is maintained in train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n🚀 Training Random Forest...")
    rf_pipeline = build_pipeline()
    rf_pipeline.fit(X_train, y_train)

    rf_pr_auc = evaluate_model(rf_pipeline, X_test, y_test, "Random Forest")
    feature_importances = get_feature_importances(rf_pipeline, training_features)

    save_artifacts(rf_pipeline, rf_pr_auc, training_features, feature_importances)

    print("\n✅ Random Forest Training Complete!")
