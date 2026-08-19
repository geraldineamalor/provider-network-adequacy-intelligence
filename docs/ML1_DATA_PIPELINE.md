
# ML-1 Data Engineering and Geospatial Feature Engineering

## Project
Provider Network Adequacy and Access Intelligence

## ML-1 Responsibilities
- Dataset acquisition
- Data inspection
- Data cleaning
- Missing-value handling
- Sampling
- Preprocessing
- Specialty-level feature engineering
- Geospatial feature engineering
- EDA
- ML-ready dataset creation
- Dataset documentation

## Main Data Sources
- NPPES Provider Registry
- U.S. Census ZIP-level population data

## Final ML-Ready Datasets

### ZIP-Level Dataset
`provider_network_ml_ready.csv`

Contains area-level provider availability, population and geospatial features.

### ZIP + Specialty-Level Dataset
`provider_network_ml_ready_specialty.csv`

Provides specialty-level provider availability and density using:

- `area_id`
- `PRIMARY_TAXONOMY`
- `specialty_provider_count`
- `specialty_provider_density_per_1000`

The combination of `area_id + PRIMARY_TAXONOMY` is unique.

## Geographic Identifier

`area_id` is constructed as:

STATE_CLEAN + "_" + ZIP_CLEAN

This provides a stable API-friendly geographic join key.

Authoritative geographic coordinates/centroids should be maintained by the appropriate backend/geospatial integration owner.

## Specialty Identifier

`PRIMARY_TAXONOMY` is retained as the NPPES provider taxonomy identifier.

Frontend specialty names such as Cardiology or Psychiatry require an agreed taxonomy mapping/reference before being used directly against this dataset.

## Population and Density

Population is joined at ZIP level.

Specialty density is calculated as:

specialty_provider_count / population * 1000

Density is treated as missing when population is unavailable or zero.

## County Integration

The current ML-1 datasets are ZIP/area level.

If the API receives state + county + specialty, ZIP/ZCTA records should be aggregated to the selected county using an authoritative ZIP/ZCTA-to-county mapping.

County-level provider density should be recomputed from aggregated provider counts and population rather than averaging ZIP-level densities.

## Large Intermediate File

`provider_clean_300000.csv` is retained in the project storage/Drive as an intermediate dataset and is not included in the GitHub repository because of its large size.

## Handoff

ML-1 provides the cleaned, engineered and ML-ready datasets for downstream ML, backend/API and frontend integration.
