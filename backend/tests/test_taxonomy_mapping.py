import pytest

from app.data.specialties import Specialty
from app.data.specialty_taxonomy import (
    TaxonomyMappingError,
    resolve_specialty,
    specialties_for_taxonomy,
    taxonomy_codes,
    taxonomy_count,
    mapping_index,
    _load_rows,
)

EXPECTED_OVERLAPS = {
    "2080P0202X": {"Cardiology", "Pediatrics"},
    "2080P0204X": {"Pediatrics", "Emergency Medicine"},
    "207PP0204X": {"Pediatrics", "Emergency Medicine"},
    "2080P0205X": {"Pediatrics", "Endocrinology"},
    "2080P0207X": {"Pediatrics", "Oncology"},
    "207VX0201X": {"Oncology", "Obstetrics & Gynecology"},
    "207VE0102X": {"Obstetrics & Gynecology", "Endocrinology"},
    "2084P0301X": {"Psychiatry", "Neurology"},
    "2084B0040X": {"Psychiatry", "Neurology"},
}


def test_mapping_has_exactly_132_approved_rows():
    rows = _load_rows()
    assert len(rows) == 132
    assert all(row["mapping_status"] == "approved" for row in rows)


def test_all_12_canonical_specialties_have_mappings():
    for specialty in Specialty:
        codes = taxonomy_codes(specialty)
        assert codes, f"No taxonomy mapping for {specialty.value}"
        assert len(set(codes)) == len(codes), (
            f"Duplicate taxonomy codes for {specialty.value}"
        )


def test_no_non_canonical_frontend_specialty_exists():
    specialties_in_mapping = {row["frontend_specialty"] for row in _load_rows()}
    canonical = {specialty.value for specialty in Specialty}
    assert specialties_in_mapping == canonical


def test_every_mapped_taxonomy_code_exists_in_mapping():
    specialty_to_rows, code_to_specialties = mapping_index()
    all_codes = set(code_to_specialties)
    for specialty, rows in specialty_to_rows.items():
        for row in rows:
            assert row["code"] in all_codes
            assert specialties_for_taxonomy(row["code"]), (
                f"Code {row['code']} resolves to no specialty"
            )


def test_overlapping_codes_resolve_to_all_approved_specialties():
    for code, expected in EXPECTED_OVERLAPS.items():
        resolved = set(specialties_for_taxonomy(code))
        assert resolved == expected, (
            f"Code {code} resolves to {resolved}, expected {expected}"
        )


def test_overlap_specialties_resolve_back_to_overlapping_code():
    for code in EXPECTED_OVERLAPS:
        for specialty in specialties_for_taxonomy(code):
            assert code in taxonomy_codes(specialty)


def test_unknown_specialty_rejected():
    with pytest.raises(TaxonomyMappingError):
        resolve_specialty("NotASpecialty")


def test_taxonomy_codes_include_all_resolved_rows():
    for specialty in Specialty:
        resolved = resolve_specialty(specialty)
        assert taxonomy_codes(specialty) == [r["code"] for r in resolved]
        for row in resolved:
            assert row["description"], f"Missing description for {row['code']}"
            assert row["mapping_status"] == "approved"
            assert row["code"].endswith("X"), f"Malformed code {row['code']}"


def test_specialties_endpoint_still_returns_twelve():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/specialties")
    assert response.status_code == 200
    assert len(response.json()) == 12