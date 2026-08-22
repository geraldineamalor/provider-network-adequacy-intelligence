import joblib
import pandas as pd
import numpy as np
import sys

def load_resources():
    """Load model, metadata, and merged data once at startup."""
    print("📦 Loading model and data...")
    pipeline = joblib.load("artifacts/final_model.joblib")
    metadata = joblib.load("artifacts/model_metadata.joblib")
    
    # Load and merge data for lookup
    df_spec = pd.read_csv("data/provider_network_ml_ready_specialty.csv")
    df_zip = pd.read_csv("data/provider_network_ml_ready.csv")
    
    # Build area_id join key with zero-padding
    for df_ in (df_zip, df_spec):
        if 'area_id' not in df_.columns:
            df_['area_id'] = df_['STATE_CLEAN'].astype(str) + '_' + \
                             df_['ZIP_CLEAN'].astype(str).str.extract(r'(\d+)')[0].str.zfill(5)
    
    context_cols = ['area_id', 'population', 'zip_provider_share_of_state',
                    'individual_provider_ratio', 'organization_provider_ratio',
                    'specialty_diversity']
    available_cols = [c for c in context_cols if c in df_zip.columns]
    df_merged = df_spec.merge(df_zip[available_cols], on='area_id', how='left')
    
    print(f"✅ Loaded {metadata['model_version']} | {len(df_merged)} records ready for lookup")
    return pipeline, metadata, df_merged


def predict_area(pipeline, metadata, df_merged, zip_code, specialty):
    """Look up real features for a ZIP+specialty and predict."""
    # Normalize ZIP input safely
    try:
        zip_clean = str(zip_code).strip().zfill(5)
    except Exception:
        print("⚠️ Invalid ZIP code input.")
        return
    
    if not zip_clean or len(zip_clean) != 5:
        print("⚠️ ZIP code must be exactly 5 digits.")
        return

    # Find matching record using normalized ZIP
    mask = (df_merged['ZIP_CLEAN'].astype(str).str.zfill(5) == zip_clean) & \
           (df_merged['PRIMARY_TAXONOMY'] == specialty)
    matches = df_merged[mask]
    
    if matches.empty:
        print(f"\n❌ No data found for ZIP={zip_clean}, Specialty={specialty}")
        zip_only = df_merged[df_merged['ZIP_CLEAN'].astype(str).str.zfill(5) == zip_clean]
        if not zip_only.empty:
            print(f"   Available specialties for this ZIP:")
            for s in zip_only['PRIMARY_TAXONOMY'].unique()[:10]:
                print(f"     - {s}")
        else:
            print(f"   ZIP {zip_clean} not found in dataset at all.")
        return
    
    row = matches.iloc[0]
    feature_cols = metadata['numeric_features'] + metadata['categorical_features']
    X = row[feature_cols].to_frame().T
    
    prob = pipeline.predict_proba(X)[0][1]
    pred = pipeline.predict(X)[0]
    
    label = "🔴 ACCESS GAP" if pred == 1 else "🟢 ADEQUATE"
    
    # Safe numeric formatter
    def fmt_num(val, decimals=4):
        try:
            return f"{float(val):,.{decimals}f}"
        except (ValueError, TypeError):
            return str(val) if val is not None else "N/A"

    print(f"\n{'='*60}")
    print(f"📍 ZIP: {zip_clean} | Specialty: {specialty}")
    print(f"{'─'*60}")
    print(f"  Population:                  {fmt_num(row.get('population'), 0):>15}")
    print(f"  Provider Share of State:     {fmt_num(row.get('zip_provider_share_of_state')):>15}")
    print(f"  Individual Provider Ratio:   {fmt_num(row.get('individual_provider_ratio')):>15}")
    print(f"  Organization Provider Ratio: {fmt_num(row.get('organization_provider_ratio')):>15}")
    print(f"  Specialty Density (per 1k):  {fmt_num(row.get('specialty_provider_density_per_1000'), 2):>15}")
    print(f"{'─'*60}")
    print(f"  → Prediction:    {label}")
    print(f"  → Gap Score:     {prob:.3f}")
    
    # Ground truth comparison
    try:
        density = float(row.get('specialty_provider_density_per_1000', float('nan')))
        if not np.isnan(density):
            threshold = df_merged[df_merged['PRIMARY_TAXONOMY'] == specialty]['specialty_provider_density_per_1000'].quantile(0.20)
            gt_label = "GAP" if density < threshold else "ADEQUATE"
            print(f"  → Ground Truth:  {gt_label} (bottom 20% threshold: {threshold:.2f})")
    except (ValueError, TypeError):
        print(f"  → Ground Truth:  N/A (non-numeric density)")
    
    # Top drivers
    importances = metadata.get('feature_importances', {})
    top_feats = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"  → Top Drivers:   {', '.join([f'{k} ({v:.1%})' for k, v in top_feats])}")
    print(f"{'='*60}")
    


def main():
    pipeline, metadata, df_merged = load_resources()
    
    # Show available specialties for reference
    unique_specs = df_merged['PRIMARY_TAXONOMY'].unique()
    print(f"\n💡 {len(unique_specs)} specialties available. Common ones:")
    common = ['207R00000X', '207Q00000X', '208D00000X', '2084P0800X', '225100000X']
    for s in common:
        if s in unique_specs:
            name_map = {
                '207R00000X': 'Internal Medicine',
                '207Q00000X': 'Family Medicine', 
                '208D00000X': 'General Practice',
                '2084P0800X': 'Psychiatry',
                '225100000X': 'Physical Therapist'
            }
            print(f"   {s} = {name_map.get(s, 'Unknown')}")
    
    print(f"\nType 'quit' to exit.\n")
    
    while True:
        try:
            zip_input = input("\n🔍 Enter ZIP code (or 'quit'): ").strip()
            if zip_input.lower() in ('quit', 'exit', 'q'):
                print("👋 Goodbye!")
                break
            
            spec_input = input("🏥 Enter PRIMARY_TAXONOMY code: ").strip()
            if not spec_input:
                print("⚠️ Specialty cannot be empty.")
                continue
                
            predict_area(pipeline, metadata, df_merged, zip_input, spec_input)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")


if __name__ == "__main__":
    main()