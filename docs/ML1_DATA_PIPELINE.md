# ML-1 Data Engineering and Geospatial Feature Engineering

## Project
Provider Network Adequacy and Access Intelligence

## Role
ML-1: Data Engineering and Geospatial Feature Engineering

## Objective
Prepare a clean, aggregated, geographic and ML-ready dataset for downstream machine learning.

## Data Sources

### 1. NPPES NPI Registry
Used for provider information, provider type, specialty, state and ZIP code.

The full NPPES file is very large, so a 300,000-record working sample was used for the hackathon pipeline.

### 2. Census ACS 2023 5-Year
Used to obtain population estimates at the ZCTA/ZIP level.

Dataset:
B01003 - Total Population

## Geographic Coordinates and Centroids

ML-1 uses STATE_CLEAN, ZIP_CLEAN, and area_id as geographic identifiers for feature engineering.

ML-1 does not create a competing authoritative centroid dataset.

Authoritative geographic coordinates/area centroids will be handled by BE-3 for application, mapping, and geographic integration.

The ML datasets can be joined to BE-3 geographic data using area_id.

## Pipeline

NPPES Provider Data
        ↓
Sampling
        ↓
Data Inspection
        ↓
Data Cleaning
        ↓
Provider Type Processing
        ↓
Specialty Processing
        ↓
ZIP/State Standardization
        ↓
ZIP-Level Provider Aggregation
        ↓
Census Population Integration
        ↓
Provider Density Features
        ↓
EDA
        ↓
ML-Ready Dataset

## Sampling

A 300,000-record sample of NPPES was used because the complete NPPES monthly file is several GB in size.

The sampling approach was selected to make the pipeline practical to execute in Google Colab.

Important limitation:
The resulting dataset should be considered a hackathon working dataset and is not guaranteed to represent the complete US provider network.

## Geographic Feature Engineering

Providers were aggregated at ZIP level.

Generated geographic/provider features include:

- Provider count
- Individual provider count
- Organization provider count
- Unique specialty count
- Specialty diversity ratio
- State provider count
- ZIP share of state providers
- Individual provider ratio
- Organization provider ratio

## Population Integration

2023 Census ACS 5-Year ZCTA population data was joined using standardized ZIP/ZCTA identifiers.

Provider ZIP records: 16,934

Population matched: 16,202

Population match rate: 95.68%

Population records without a Census match: 732

Missing population values were retained as missing values and were NOT replaced with zero.

## Density Features

The following features were created:

- Providers per 10,000 population
- Individual providers per 10,000 population
- Organization providers per 10,000 population

Density features are calculated only where population is available and greater than zero.

## Final ML-Ready Dataset

File:

data/processed/provider_network_ml_ready.csv

Rows: 16,934

Features: 16

Duplicate rows: 0

## Final Features

1. STATE_CLEAN
2. ZIP_CLEAN
3. provider_count
4. individual_provider_count
5. organization_provider_count
6. unique_specialty_count
7. providers_with_specialty
8. specialty_diversity_ratio
9. state_provider_count
10. zip_provider_share_of_state
11. individual_provider_ratio
12. organization_provider_ratio
13. population
14. providers_per_10000
15. individual_providers_per_10000
16. organization_providers_per_10000

## EDA

Exploratory Data Analysis was performed on:

- Provider count distribution
- Provider density distribution
- Specialty diversity
- Population distribution
- Geographic/provider feature distributions

The distributions show strong skew in several provider and population-related variables.

## Important Limitations

1. NPPES data was sampled rather than using the complete provider registry.
2. ZIP code and Census ZCTA are related but are not exactly identical geographic concepts.
3. Some ZIP records do not have a matching Census population value.
4. Provider density can contain extreme values in areas with very small populations.
5. Provider count does not directly measure appointment availability, provider capacity, wait time or quality.
6. Target definition and final ML model selection are outside the ML-1 responsibility.

## Handoff to ML-2

The final ML-ready dataset is prepared for downstream:

- Target definition
- Feature selection
- Model development
- Model evaluation
- Provider access-gap prediction

ML-2 should consider appropriate handling of skewed density variables, including log transformation, robust scaling or winsorization where appropriate.

## Files

- ml/ML1_provider_pipeline.ipynb
- data/processed/provider_network_ml_ready.csv
- data/processed/provider_network_ml_ready_specialty.csv
- data/processed/provider_geo_features_zip.csv
- data/processed/census_zip_population_2023.csv
- data/processed/ML1_data_dictionary.csv
- data/processed/ML1_summary.txt

## Raw Data Policy

Large raw NPPES files and large intermediate files are intentionally not committed to GitHub.

They remain in Google Drive/local storage so that the GitHub repository remains lightweight.

