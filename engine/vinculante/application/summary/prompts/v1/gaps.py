PROMPT = """\
Eres un analista de vinculación normativa. Tu tarea es identificar las lagunas: propuestas \
y secciones del documento que no han encontrado vinculación aceptada.

# Áreas temáticas cubiertas por el análisis

{themes_block}

# Secciones del documento sin vinculación (con contenido relevante)

{orphan_sections_block}

# Propuestas sin vinculación aceptada

{unmatched_proposals_block}

---

Escribe un análisis de lagunas con tres partes:

1. **orphan_observations**: Observaciones sobre las secciones del documento sin propuestas
vinculadas, si hay un patrón claro. 1-2 frases. Vacío si no hay patrones relevantes.

2. **unmatched_clusters**: Descripción de grupos de propuestas sin vinculación, agrupados por tema \
o perfil de autor. Menciona qué piden y por qué pueden ser relevantes. 1-2 párrafos. \
Para propuestas ciudadanas, agrupa por tema sin revelar identidades individuales.

3. **gaps_narrative**: Síntesis de las lagunas principales en 1 párrafo.
"""
