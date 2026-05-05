MATCH_PROMPT = """Eres un experto en análisis normativo. Tu tarea es evaluar si un fragmento de texto legal cubre, total o parcialmente, una propuesta ciudadana.

Propuesta ciudadana:
{proposal_text}

Fragmento legal:
{section_text}

Evalúa el grado de cobertura:
- "alto": el fragmento cubre directamente y de forma sustancial la propuesta.
- "medio": el fragmento cubre parcialmente la propuesta o de forma indirecta.
- "bajo": existe una relación débil o tangencial.
- "ninguno": no hay relación relevante.

Devuelve el grado, una explicación breve y tu nivel de confianza."""