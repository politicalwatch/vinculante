PROMPT = """\
Eres un analista de vinculación normativa. Tienes el análisis completo de un proceso de \
participación ciudadana frente a un documento normativo. Escribe la síntesis final.

# Resumen del documento

{overview_intro}

# Áreas de vinculación identificadas

{themes_block}

# Lagunas detectadas

{gaps_narrative}

# Datos de calibración (no citar cifras en el texto generado)

{stats_block}

---

Proporciona:

1. **vision_general**: 1 párrafo (3-5 frases) con una lectura cualitativa global
de la alineación entre el documento y las propuestas. Usa adjetivos para calibrar
("amplia", "concentrada", "puntual", "desigual") pero NO cites cifras ni conteos.

2. **observaciones**: 0-3 patrones transversales llamativos (sesgo hacia ciertos autores o temas, \
concentración en pocas secciones, grupos de propuestas sistemáticamente desatendidas, etc.). \
Lista vacía si no hay patrones que aporten más allá de lo ya expresado en los apartados anteriores.
"""
