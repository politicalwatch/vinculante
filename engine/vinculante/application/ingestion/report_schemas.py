from pydantic import BaseModel, Field


class AuthorExtraction(BaseModel):
    author: str = Field(
        description=(
            "Nombre(s) del autor o autores tal como aparecen en el documento. "
            "Si son varios individuos, separados por coma. "
            "Si es una organización o colectivo, el nombre de la entidad. "
            "Si aparecen individuos y organización editora, primero los individuos "
            "seguidos de la organización entre paréntesis. "
            "Si no se puede determinar, devuelve 'Desconocido'."
        )
    )


class ExtractedProposal(BaseModel):
    title: str | None = Field(
        default=None,
        description=(
            "Título corto o identificador de la propuesta si aparece explícitamente "
            "(e.g., 'Medida 3', 'Estado emprendedor', 'Propuesta 1'). "
            "null si no hay identificador explícito."
        ),
    )
    text: str = Field(
        description=(
            "Texto VERBATIM de la propuesta tal como aparece en el documento original. "
            "Copia las oraciones exactamente, incluyendo todo el desarrollo, justificación, "
            "listas con viñetas y ejemplos. NO resumas, NO parafrasees, NO recortes listas. "
            "Si la propuesta va precedida por una línea 'Título. <frase>', incluye esa frase "
            "verbatim como primera oración (sin el prefijo 'Título.')."
        )
    )
    indicators: list[str] = Field(
        default_factory=list,
        description=(
            "Indicadores de seguimiento o evaluación que aparecen explícitamente "
            "en el texto para esta propuesta. Lista vacía si no hay."
        ),
    )
    targets: list[str] = Field(
        default_factory=list,
        description=(
            "Metas, compromisos o hitos cuantificados que aparecen explícitamente "
            "en el texto para esta propuesta. Lista vacía si no hay."
        ),
    )
    topic: str | None = Field(
        default=None,
        description="Sección principal donde aparece la propuesta (heading de mayor nivel).",
    )
    subtopic: str | None = Field(
        default=None,
        description="Subsección si existe y es diferente al topic. null si no hay.",
    )


class ExtractedProposalList(BaseModel):
    proposals: list[ExtractedProposal] = Field(
        default_factory=list,
        description=(
            "Lista de propuestas extraídas del fragmento. "
            "Lista vacía si el fragmento no contiene propuestas concretas."
        ),
    )
