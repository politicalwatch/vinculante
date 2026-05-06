from pydantic import BaseModel, Field


class DocumentOverview(BaseModel):
    intro: str = Field(
        description=(
            "1-2 párrafos que resumen los ejes principales del documento. "
            "No mencionar propuestas ciudadanas ni resultados del análisis de vinculación."
        )
    )
    axes: list[str] = Field(
        description=(
            "Lista de 3-5 ejes temáticos principales del documento "
            "(nombres cortos, sin descripciones largas)."
        )
    )


class ThematicCluster(BaseModel):
    label: str = Field(
        description=(
            "Nombre corto del área temática de vinculación "
            "(ej. 'Acceso a vivienda pública')."
        )
    )
    description: str = Field(
        description=(
            "1-2 frases que describen cómo el documento y las propuestas convergen en esta área."
        )
    )


class ThemeAnalysis(BaseModel):
    clusters: list[ThematicCluster] = Field(
        description=(
            "3-5 áreas temáticas donde el documento y las propuestas convergen con mayor fuerza."
        )
    )


class Highlight(BaseModel):
    author_label: str = Field(
        description=(
            "Nombre del autor (institución/académico) "
            "o etiqueta anonimizada ('propuesta ciudadana')."
        )
    )
    proposal_claim: str = Field(
        description="Descripción breve de lo que pide la propuesta (1 frase)."
    )
    section_ref: str = Field(
        description="Referencia a la sección del documento, en formato 'Sección X (p. Y)'."
    )
    relevance: str = Field(
        description="Por qué esta vinculación es relevante o destacable (1 frase)."
    )


class HighlightExtraction(BaseModel):
    highlights: list[Highlight] = Field(
        description=(
            "3-5 vinculaciones específicas de alta confianza que mejor ilustran el análisis."
        )
    )


class GapAnalysis(BaseModel):
    orphan_observations: str = Field(
        description=(
            "Observaciones sobre secciones del documento sin propuestas vinculadas, "
            "si hay un patrón claro. "
            "1-2 frases. Puede dejarse vacío si no hay patrones relevantes."
        )
    )
    unmatched_clusters: str = Field(
        description=(
            "Descripción de grupos de propuestas sin vinculación aceptada, "
            "agrupados por tema o perfil de autor. "
            "Mencionar qué piden y por qué pueden ser relevantes. 1-2 párrafos."
        )
    )
    gaps_narrative: str = Field(
        description="Síntesis de las lagunas principales detectadas. 1 párrafo."
    )


class Synthesis(BaseModel):
    vision_general: str = Field(
        description=(
            "1 párrafo (3-5 frases) con una lectura cualitativa global de la alineación "
            "entre el documento y las propuestas. "
            "Usar adjetivos para calibrar ('amplia', 'concentrada', 'puntual') "
            "pero NO citar cifras ni porcentajes."
        )
    )
    observaciones: list[str] = Field(
        description=(
            "0-3 patrones transversales llamativos: sesgo hacia ciertos autores o temas, "
            "concentración en pocas secciones, grupos de propuestas desatendidas, etc. "
            "Lista vacía si no hay patrones que aporten más allá de lo ya dicho."
        )
    )
