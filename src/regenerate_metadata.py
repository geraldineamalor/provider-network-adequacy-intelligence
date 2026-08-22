import joblib
import os

# Authoritative v3.2 evaluation metrics from the actual training run
CORRECTED_METADATA = {
    "model_version": "v3.2-specialty-context-merged",
    "model_type": "random_forest",
    "pr_auc": 0.3793,
    "roc_auc": 0.7449,
    "accuracy": 0.76,
    "precision_gap": 0.41,
    "recall_gap": 0.48,
    "f1_gap": 0.44,
    "test_set_size": 32259,
    "numeric_features": [
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
        "specialty_diversity"
    ],
    "categorical_features": ["PRIMARY_TAXONOMY"],
    "feature_importances": {
        "zip_provider_share_of_state": 0.4076,
        "PRIMARY_TAXONOMY": 0.2679,
        "organization_provider_ratio": 0.1629,
        "individual_provider_ratio": 0.1617
    },
    "target_definition": "Bottom 20% specialty-specific density per ZIP",
    "drop_population": False,
    "log_population": False
}

os.makedirs("artifacts", exist_ok=True)
output_path = "artifacts/model_metadata.joblib"
joblib.dump(CORRECTED_METADATA, output_path)

# Verify round-trip integrity
loaded = joblib.load(output_path)
assert loaded["pr_auc"] == 0.3793, "PR-AUC mismatch after save!"
assert loaded["model_version"] == "v3.2-specialty-context-merged"
print(f"✅ Corrected metadata saved to {output_path}")
print(f"   PR-AUC: {loaded['pr_auc']}")
print(f"   ROC-AUC: {loaded['roc_auc']}")
print(f"   Features: {len(loaded['numeric_features'])} numeric + {len(loaded['categorical_features'])} categorical")