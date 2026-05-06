PROMPT = """\
Eres un analista de vinculación normativa. Selecciona las vinculaciones más destacadas entre \
propuestas y un documento normativo.

# Áreas temáticas identificadas

{themes_block}

# Vinculaciones de grado alto con evidencia verificada

{highlights_block}

---

Selecciona 3-5 vinculaciones específicas que mejor ilustren el análisis. \
Elige vinculaciones de diferentes áreas temáticas cuando sea posible.

Para cada una proporciona:
- El autor (nombre del autor o etiqueta anonimizada).
- Una descripción breve de lo que pide la propuesta (1 frase).
- La referencia a la sección del documento en formato "Sección X (p. Y)" \
(si no hay página disponible, usa solo "Sección X").
- Por qué esta vinculación es relevante o destacable (1 frase).
"""
