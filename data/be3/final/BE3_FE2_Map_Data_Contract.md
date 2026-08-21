# BE-3 → FE-2 Map Data Contract

## 1. Purpose

This document defines the map-data interface produced by BE-3
(Geospatial / External Integration / Cloud) for FE-2 (Frontend).

The handoff contains provider-level geographic identifiers,
coordinates, geographic confidence/provenance, spatial metric
features, and geographic policy metadata required for map
visualization and frontend filtering.

The handoff preserves all 281,478 geographically eligible U.S.
provider records from the BE-3 processing layer.

---

## 2. Source

Primary BE-3 source:

- `be3_final_281478.csv`
- 281,478 rows
- 46 columns

FE-2 map handoff:

- `be3_fe2_map_handoff_281478.parquet`
- `be3_fe2_map_handoff_281478.csv`
- `be3_fe2_map_handoff_manifest.json`

FE-2 handoff dimensions:

- Rows: 281,478
- Columns: 34
- Unique NPIs: 281,478

---

## 3. Coordinate Representation

Each provider row has one of three coordinate types:

| Coordinate type | Rows | Meaning |
|---|---:|---|
| `provider_coordinate` | 2,349 | Actual provider-level Census-geocoded coordinate |
| `zcta_centroid` | 274,994 | 2020 Census ZCTA centroid used as an area-level fallback |
| `unresolved` | 4,135 | No usable spatial coordinate |

Total rows: 281,478.

Rows with usable coordinates:

- 277,343

Rows without coordinates:

- 4,135

### Critical frontend rule

`zcta_centroid` MUST NOT be presented as if it were the exact
physical location of an individual provider.

It represents the geographic area associated with the provider's
ZCTA.

---

## 4. Coordinate Provenance

### provider_coordinate

Source:

- U.S. Census Geocoder
- Benchmark: `Public_AR_Current`

Coordinate confidence:

- `geocoded_address`

These coordinates represent provider-level geographic locations.

### zcta_centroid

Source:

- 2020 U.S. Census ZCTA Gazetteer

Source label:

- `Census_ZCTA_Gazetteer_2020`

These coordinates represent the centroid of the provider's ZCTA
and are used only as an area-level spatial fallback.

### unresolved

No usable coordinate was available.

These rows MUST NOT be plotted as geographic points.

---

## 5. Spatial Metric Policy

Each row has a `spatial_metric_policy` value:

| Policy | Rows | Meaning |
|---|---:|---|
| `provider_level` | 2,349 | Provider-level spatial calculations are available |
| `area_level_fallback` | 274,994 | Spatial calculations are based on ZCTA centroid / area representation |
| `unresolved` | 4,135 | No usable spatial representation |

Frontend logic MUST preserve this distinction.

Provider-level and area-level metrics MUST NOT be silently mixed.

---

## 6. FE-2 Map Eligibility

A row is map-coordinate eligible when:

- `spatial_latitude` is present
- `spatial_longitude` is present
- `spatial_coordinate_type` is either:
  - `provider_coordinate`, or
  - `zcta_centroid`

Expected map-coordinate eligible rows:

- 277,343

Unresolved rows:

- 4,135

Unresolved rows should remain available for filtering/table views
but should not be rendered as geographic points.

---

## 7. Provider-Level Spatial Features

The following 12 numerical features are provider-level features:

1. `nearest_provider_distance_miles`
2. `second_nearest_provider_distance_miles`
3. `provider_count_5mi`
4. `provider_count_10mi`
5. `provider_count_25mi`
6. `provider_count_50mi`
7. `provider_count_100mi`
8. `same_taxonomy_count_5mi`
9. `same_taxonomy_count_10mi`
10. `same_taxonomy_count_25mi`
11. `same_taxonomy_count_50mi`
12. `same_taxonomy_count_100mi`

These features are populated only for the 2,349
`provider_level` rows.

They are NOT populated for:

- ZCTA centroid rows
- unresolved rows

### Distance interpretation

Provider-to-provider distance features were calculated using
provider-level coordinates and are based on great-circle
(Haversine) distance.

ZCTA centroid coordinates were NOT substituted into provider-level
nearest-provider or provider-density calculations.

---

## 8. Area-Level Spatial Features

The following 10 numerical features are area-level features:

1. `area_provider_count_5mi`
2. `area_provider_count_10mi`
3. `area_provider_count_25mi`
4. `area_provider_count_50mi`
5. `area_provider_count_100mi`
6. `area_same_taxonomy_count_5mi`
7. `area_same_taxonomy_count_10mi`
8. `area_same_taxonomy_count_25mi`
9. `area_same_taxonomy_count_50mi`
10. `area_same_taxonomy_count_100mi`

These features are populated only for the 274,994
`area_level_fallback` rows.

They are not populated for unresolved rows.

---

## 9. Reference Provider IDs

The full BE-3 spatial layer contains nearest-provider reference IDs,
but the FE-2 map handoff intentionally contains only the numerical
distance features for the nearest-provider metrics.

FE-2 should use:

- `nearest_provider_distance_miles`
- `second_nearest_provider_distance_miles`

for geographic visualization/filtering.

---

## 10. Geographic Identifiers

The handoff includes:

- `zip_clean`
- `zcta_clean`
- `county_fips`
- City
- State

The ZCTA field represents the cleaned five-digit ZCTA/ZIP geographic
identifier used by the BE-3 geographic processing layer.

County assignment is based on the BE-3 Census ZCTA/county geographic
reference processing.

---

## 11. Required FE-2 Columns

The handoff contains exactly 34 columns:

1. `NPI`
2. `spatial_latitude`
3. `spatial_longitude`
4. `spatial_coordinate_type`
5. `spatial_coordinate_source`
6. `spatial_coordinate_confidence`
7. `Provider Business Practice Location Address City Name`
8. `Provider Business Practice Location Address State Name`
9. `zip_clean`
10. `zcta_clean`
11. `county_fips`
12. `spatial_metric_policy`
13. `nearest_provider_distance_miles`
14. `second_nearest_provider_distance_miles`
15. `provider_count_5mi`
16. `provider_count_10mi`
17. `provider_count_25mi`
18. `provider_count_50mi`
19. `provider_count_100mi`
20. `same_taxonomy_count_5mi`
21. `same_taxonomy_count_10mi`
22. `same_taxonomy_count_25mi`
23. `same_taxonomy_count_50mi`
24. `same_taxonomy_count_100mi`
25. `area_provider_count_5mi`
26. `area_provider_count_10mi`
27. `area_provider_count_25mi`
28. `area_provider_count_50mi`
29. `area_provider_count_100mi`
30. `area_same_taxonomy_count_5mi`
31. `area_same_taxonomy_count_10mi`
32. `area_same_taxonomy_count_25mi`
33. `area_same_taxonomy_count_50mi`
34. `area_same_taxonomy_count_100mi`

---

## 12. Data Quality Guarantees

The exported handoff was validated for:

- 281,478 rows
- 34 columns
- unique NPI
- no duplicate column names
- complete coordinate pairs
- valid latitude/longitude ranges
- correct coordinate-type counts
- correct spatial-policy counts
- provider-level feature isolation
- area-level feature isolation
- unresolved-feature exclusion
- non-negative spatial counts
- Parquet reload integrity
- CSV reload integrity
- Parquet/CSV NPI identity
- manifest consistency

Validation status: PASS.

---

## 13. Frontend Rendering Rules

### Exact provider location

When:

`spatial_coordinate_type == "provider_coordinate"`

FE-2 may display the coordinate as a provider-level location.

### Area representation

When:

`spatial_coordinate_type == "zcta_centroid"`

FE-2 should communicate that the coordinate represents the
provider's ZCTA/area rather than an exact provider location.

### Unresolved

When:

`spatial_coordinate_type == "unresolved"`

FE-2 should not plot the record geographically.

The record can still be retained for non-map views or filtering.

---

## 14. Recommended Map Usage

FE-2 may use the following fields for geographic filtering and
visualization:

- `spatial_latitude`
- `spatial_longitude`
- `spatial_coordinate_type`
- `spatial_coordinate_confidence`
- City
- State
- `zip_clean`
- `zcta_clean`
- `county_fips`
- spatial density/count features
- nearest-provider distance features
- `spatial_metric_policy`

The frontend should expose or internally preserve the distinction
between provider-level and area-level spatial information.

---

## 15. Important Limitations

1. Provider-level geocoded coordinates are available for only 2,349
   of the 281,478 rows.

2. Most geographically usable rows (274,994) use ZCTA centroids.

3. ZCTA centroid coordinates are area representations, not exact
   provider locations.

4. 4,135 rows have no usable spatial coordinate.

5. Provider-level nearest-provider and density features are available
   only where provider-level coordinates exist.

6. Area-level density features are calculated from unique ZCTA
   centroid locations and provider counts associated with those ZCTAs.

7. FE-2 must not infer an exact provider address from a ZCTA centroid.

---

## 16. Export Artifacts

All artifacts are stored under:

`/content/drive/MyDrive/data/be3_final/`

Files:

- `be3_fe2_map_handoff_281478.parquet`
- `be3_fe2_map_handoff_281478.csv`
- `be3_fe2_map_handoff_manifest.json`
- `BE3_FE2_Map_Data_Contract.md`

---

## 17. Handoff Status

BE-3 FE-2 map-data handoff:

**COMPLETE**

Export validation:

**PASSED**

Reload validation:

**PASSED**

Cross-file identity validation:

**PASSED**

FE-2 can consume the Parquet or CSV handoff according to the
coordinate and spatial-policy rules defined in this contract.
