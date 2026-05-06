PROMPT = """\
Eres un analista de vinculación normativa. Tienes los resultados de un proceso de participación \
ciudadana en el que propuestas han sido analizadas frente a un documento normativo.

# Contexto del documento

{document_overview}

# Vinculaciones aceptadas (grado alto o medio), agrupadas por sección

{matches_block}

---

Identifica 3-5 áreas temáticas donde el documento y las propuestas convergen con mayor fuerza.
Para cada área proporciona un nombre corto y 1-2 frases que describan
en qué consiste la convergencia.

Agrupa las vinculaciones existentes; no inventes áreas sin respaldo en los datos.
"""
