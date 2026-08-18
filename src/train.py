import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, precision_recall_curve, auc

# 1. CONFIGURATION
NUMERIC_FEATURES = [
    'provider_density_per_10k', 'specialty_mix_pct', 'medicare_claims_per_provider',
    'avg_services_per_beneficiary', 'pct_population_over_65', 'pct_poverty',
    'distance_to_nearest_provider_miles', 'is_in_healthcare_gov_service_area'
]
CATEGORICAL_FEATURES = ['specialty']
TARGET_COL = 'access_gap_target'

def build_pipeline():
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), NUMERIC_FEATURES),
            ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES)
        ])
    return Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000))
    ])

def train_and_evaluate(df):
    print("Starting training pipeline...")
    df['specialty'] = df['specialty'].fillna('Unknown')
    
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET_COL]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    print("\n=== CLASSIFICATION REPORT ===")
    print(classification_report(y_test, y_pred, target_names=['Adequate (0)', 'Access Gap (1)']))
    
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = auc(recall, precision)
    print(f"PR-AUC: {pr_auc:.4f}")
        
    return pipeline, pr_auc

def save_artifacts(pipeline, pr_auc):
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(pipeline, "artifacts/baseline_model.joblib")
    print("\nModel saved to artifacts/baseline_model.joblib")

if __name__ == "__main__":
    mock_path = "data/mock_provider_data.csv"
    if not os.path.exists(mock_path):
        print("Mock data not found. Generating...")
        from generate_mock_data import generate_mock_data
        generate_mock_data(filepath=mock_path)
    
    df = pd.read_csv(mock_path)
    pipeline, pr_auc = train_and_evaluate(df)
    save_artifacts(pipeline, pr_auc)
    print("\nDay 1 Baseline Pipeline Complete.")