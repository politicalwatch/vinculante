from typing import Literal

from pydantic import BaseModel, Field


class MatchScore(BaseModel):
    degree: Literal["alto", "medio", "bajo", "ninguno"] = Field(
        description="Grado de cobertura de la propuesta por el fragmento legal"
    )
    explanation: str = Field(
        description="Breve explicación del grado de relación encontrado"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confianza en la evaluación, entre 0.0 (ninguna) y 1.0 (total)"
    )
