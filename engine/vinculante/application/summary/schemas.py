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
            "Nombre del autor académico "
            "o etiqueta anonimizada ('propuesta ciudadana')."
        )
    )
    proposal_claim: str = Field(
        description="Descripción breve de lo que pide la propuesta (1 frase)."
    )
    section_ref: str = Field(
        description=(
            "Referencia descriptiva al artículo o sección del documento, citando el título o "
            "primera frase representativa y, entre paréntesis, la página cuando esté "
            "disponible (ej. 'Tarifas reducidas para estudiantes (p. 12)'). "
            "Si la página no aparece en los datos, omítela."
        )
    )
    relevance: str = Field(
        description="Por qué esta vinculación es relevante o destacable (1 frase)."
    )


class HighlightExtraction(BaseModel):
    citizen_intro: str = Field(
        description=(
            "Una frase de prosa que introduce las vinculaciones ciudadanas destacadas. "
            "Vacío si no hay vinculaciones ciudadanas destacadas."
        )
    )
    citizen_highlights: list[Highlight] = Field(
        description=(
            "Vinculaciones de alta confianza de propuestas ciudadanas. "
            "Lista vacía si no hay."
        )
    )
    academia_intro: str = Field(
        description=(
            "Una frase de prosa que introduce las vinculaciones académicas "
            "destacadas. Vacío si no hay vinculaciones académicas destacadas."
        )
    )
    academia_highlights: list[Highlight] = Field(
        description=(
            "Vinculaciones de alta confianza de propuestas académicas. "
            "Lista vacía si no hay."
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
    citizen_unmatched: str = Field(
        description=(
            "1-2 párrafos sobre los gaps reales ciudadanos: propuestas en ámbito de la norma "
            "sin vinculación aceptada. Excluir propuestas fuera del ámbito (otra ley, otro ministerio). "
            "Agrupar por tema sin revelar identidades individuales. "
            "Priorizar por consenso, innovación, especificidad. "
            "Introducir el párrafo de forma natural. "
            "Vacío si no hay gaps ciudadanos reales."
        )
    )
    academia_unmatched: str = Field(
        description=(
            "1-2 párrafos sobre los gaps reales académicos: propuestas académicas en ámbito de la norma "
            "sin vinculación aceptada. Excluir propuestas fuera del ámbito. "
            "Citar autores cuando aporten señal. "
            "Priorizar por consenso, innovación, especificidad, autoridad académica. "
            "Introducir el párrafo de forma natural. "
            "Vacío si no hay gaps académicos reales."
        )
    )
    gaps_narrative: str = Field(
        description=(
            "Síntesis de los gaps principales detectados en 1 párrafo. "
            "Si una parte notable de las propuestas estaba fuera del ámbito de la norma, "
            "menciónalo brevemente aquí como observación meta."
        )
    )


class Synthesis(BaseModel):
    vision_general: str = Field(
        description=(
            "2-3 párrafos con una lectura cualitativa global de la alineación. "
            "Primer párrafo: visión general del conjunto. "
            "Si hay propuestas ciudadanas, un párrafo sobre las vinculaciones con ellas. "
            "Si hay propuestas académicas, otro párrafo sobre ellas. "
            "Integrar patrones transversales (sesgos, concentraciones, grupos desatendidos) "
            "directamente en el texto, sin sección separada. "
            "Omitir el párrafo de un grupo si no hay datos. "
            "Usar adjetivos para calibrar ('amplia', 'concentrada', 'puntual', 'desigual'); "
            "NO citar cifras ni porcentajes."
        )
    )
