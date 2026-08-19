from app.data.specialties import CANONICAL_SPECIALTIES


def get_specialties() -> list[dict[str, int | str]]:
    return [
        {"id": index, "name": specialty.value}
        for index, specialty in enumerate(CANONICAL_SPECIALTIES, start=1)
    ]