from pydantic import BaseModel


class SpecialtyItem(BaseModel):
    id: int
    name: str