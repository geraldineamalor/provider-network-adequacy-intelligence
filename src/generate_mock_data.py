import pandas as pd
import numpy as np
import os

def generate_mock_data(num_samples=1000, filepath="data/mock_provider_data.csv"):
    np.random.seed(42)
    data = {
        'zip_code': [f"{np.random.randint(10000, 99999)}" for _ in range(num_samples)],
        'specialty': np.random.choice(['Primary Care', 'Cardiology', 'Mental Health'], num_samples),
        'provider_density_per_10k': np.random.uniform(0.5, 8.0, num_samples),
        'specialty_mix_pct': np.random.uniform(0.1, 0.8, num_samples),
        'medicare_claims_per_provider': np.random.uniform(50, 600, num_samples),
        'avg_services_per_beneficiary': np.random.uniform(1.0, 6.0, num_samples),
        'pct_population_over_65': np.random.uniform(0.10, 0.35, num_samples),
        'pct_poverty': np.random.uniform(0.05, 0.30, num_samples),
        'distance_to_nearest_provider_miles': np.random.uniform(1.0, 20.0, num_samples),
        'is_in_healthcare_gov_service_area': np.random.choice([0, 1], num_samples, p=[0.3, 0.7]),
    }
    df = pd.DataFrame(data)
    
    # Create target logic
    risk_score = (
        (df['distance_to_nearest_provider_miles'] / 20.0) * 0.4 +
        ((8.0 - df['provider_density_per_10k']) / 8.0) * 0.4 +
        (df['medicare_claims_per_provider'] / 600.0) * 0.2
    )
    noise = np.random.normal(0, 0.1, num_samples)
    df['access_gap_target'] = ((risk_score + noise) > 0.55).astype(int)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"✅ Mock data saved to {filepath}")

if __name__ == "__main__":
    generate_mock_data()