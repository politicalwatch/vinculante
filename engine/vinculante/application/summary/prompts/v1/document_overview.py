PROMPT = """\
Eres un analista normativo. Tu tarea es identificar los ejes temáticos principales de un documento \
y escribir una introducción breve para alguien que no conoce el documento.

# Documento

**Título:** {title}
**Autor/Institución:** {author}
{version_line}

## Secciones del documento

{sections_block}

---

Proporciona:
1. Una introducción de 4-7 frases que explique de qué trata el documento. \
No menciones propuestas ciudadanas ni resultados de análisis de vinculación.
2. Una lista de 3-5 ejes temáticos principales del documento
(nombres cortos, sin descripciones largas).
"""
