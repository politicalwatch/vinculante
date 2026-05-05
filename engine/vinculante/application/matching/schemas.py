from typing import Literal

from pydantic import BaseModel, Field


class MatchScore(BaseModel):
    degree: Literal["alto", "medio", "bajo", "ninguno"] = Field(
        description="Grado de cobertura de la propuesta por el fragmento legal"
    )
    explanation: str = Field(
        description="Razonamiento paso a paso que justifica el grado de vinculación asignado."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confianza en la evaluación, entre 0.0 (ninguna) y 1.0 (total)"
    )
    evidence_quotes: list[str] = Field(
        default_factory=list,
        description=(
            "Lista de citas LITERALES copiadas palabra por palabra del fragmento legal "
            "(cada una entre 15 y 200 caracteres) que respaldan el grado asignado. "
            "Cada cita debe ser una subcadena exacta del texto del artículo. "
            "Puede haber más de una si la evidencia está repartida en varias frases. "
            "Dejar vacío únicamente si el grado es 'ninguno'."
        ),
    )


class OneToManyMatchScore(MatchScore):
    section_id: int = Field(description="ID del artículo evaluado")


class OneToManyMatchResults(BaseModel):
    matches: list[OneToManyMatchScore] = Field(
        description="Resultados de la evaluación para cada artículo candidato"
    )


class ProposalAnalysis(BaseModel):
    """Schema for step 1: extracting the core demand of a proposal."""
    is_specific: bool = Field(
        description="True si la propuesta exige un mecanismo, derecho o acción específica. False si solo declara un deseo general o principio."
    )
    core_demand: str = Field(
        description="La necesidad o acción concreta que pide la propuesta (ej. 'limitar alquileres', 'más psicólogos'). Si es general, el dominio temático."
    )
    domain: str = Field(
        description="El ámbito temático general (ej. 'Vivienda', 'Educación')."
    )


class CandidateClassification(BaseModel):
    """Schema for step 2: classifying candidate articles by type."""
    operative_ids: list[int] = Field(
        description="IDs de los artículos que establecen medidas, regulan mecanismos, otorgan derechos o imponen obligaciones."
    )
    introductory_ids: list[int] = Field(
        description="IDs de los artículos que son meramente declarativos, de objeto, ámbito de aplicación o principios generales."
    )
