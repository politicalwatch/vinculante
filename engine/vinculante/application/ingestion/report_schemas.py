from pydantic import BaseModel, Field


class AuthorExtraction(BaseModel):
    authors: list[str] = Field(
        default_factory=list,
        description=(
            "Proponentes del documento, un elemento por proponente, tal como aparecen. "
            "Si lo firma una organización o colectivo, solo el nombre de la entidad. "
            "Si lo firman personas, un elemento por persona con su organización entre "
            "paréntesis cuando se conozca: 'Nombre Apellido (Organización)'. "
            "Lista vacía si no se puede determinar."
        ),
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
