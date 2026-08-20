"""
Canonical frontend specialty -> NPPES PRIMARY_TAXONOMY resolution layer.

Sources:
    - Canonical specialties: app.data.specialties.Specialty (unchanged).
    - Taxonomy mapping: specialty_taxonomy_mapping.csv (NUCC-derived,
      132 approved rows, one-to-many and approved cross-specialty overlaps).
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.data.specialties import Specialty

MAPPING_CSV = Path(__file__).resolve().parent / "specialty_taxonomy_mapping.csv"


class TaxonomyMappingError(ValueError):
    """Raised when a taxonomy resolution request cannot be satisfied."""


@lru_cache(maxsize=1)
def _load_rows() -> tuple[dict[str, str], ...]:
    with MAPPING_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        return tuple(csv.DictReader(file))


def _build_index() -> tuple[dict[str, list[dict[str, str]]], dict[str, list[str]]]:
    """Return (specialty -> rows, taxonomy_code -> specialty names)."""
    specialty_to_rows: dict[str, list[dict[str, str]]] = {}
    code_to_specialties: dict[str, list[str]] = {}

    for row in _load_rows():
        specialty = row["frontend_specialty"]
        code = row["PRIMARY_TAXONOMY"]
        description = row["taxonomy_description"]
        status = row["mapping_status"]

        if not specialty or not code or not description or not status:
            raise TaxonomyMappingError(
                f"Invalid taxonomy mapping row: {row!r}"
            )
        if status != "approved":
            raise TaxonomyMappingError(
                f"Non-approved mapping_status {status!r} for code {code!r}"
            )
        if specialty not in Specialty._value2member_map_:
            raise TaxonomyMappingError(
                f"Non-canonical frontend specialty in mapping: {specialty!r}"
            )

        specialty_to_rows.setdefault(specialty, []).append(
            {
                "code": code,
                "description": description,
                "mapping_status": status,
                "mapping_notes": row["mapping_notes"],
            }
        )
        code_to_specialties.setdefault(code, []).append(specialty)

    missing = [s.value for s in Specialty if s.value not in specialty_to_rows]
    if missing:
        raise TaxonomyMappingError(
            f"Canonical specialties missing from taxonomy mapping: {missing}"
        )

    return specialty_to_rows, code_to_specialties


@lru_cache(maxsize=1)
def _index() -> tuple[dict[str, list[dict[str, str]]], dict[str, list[str]]]:
    return _build_index()


def _normalize_specialty(specialty: Specialty | str) -> str:
    if isinstance(specialty, Specialty):
        return specialty.value
    if isinstance(specialty, str):
        try:
            return Specialty(specialty).value
        except ValueError as exc:
            raise TaxonomyMappingError(
                f"Unknown frontend specialty: {specialty!r}"
            ) from exc
    raise TaxonomyMappingError(
        f"Invalid specialty type: {type(specialty).__name__}"
    )


def resolve_specialty(specialty: Specialty | str) -> list[dict[str, str]]:
    """Return all PRIMARY_TAXONOMY rows for a frontend specialty."""
    specialty_to_rows, _ = _index()
    return specialty_to_rows[_normalize_specialty(specialty)]


def taxonomy_codes(specialty: Specialty | str) -> list[str]:
    """Return PRIMARY_TAXONOMY codes for a frontend specialty."""
    return [row["code"] for row in resolve_specialty(specialty)]


def specialties_for_taxonomy(code: str) -> list[str]:
    """Return every frontend specialty a taxonomy code resolves to."""
    _, code_to_specialties = _index()
    return list(code_to_specialties.get(code, []))


def taxonomy_count() -> int:
    """Total number of rows in the mapping."""
    return len(_load_rows())


def mapping_index() -> tuple[dict[str, list[dict[str, str]]], dict[str, list[str]]]:
    """Expose the underlying mapping index (specialty->rows, code->specialties)."""
    return _index()


def _as_records() -> list[dict[str, Any]]:
    return [dict(row) for row in _load_rows()]