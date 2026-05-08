PROMPT = """\
Eres un analista de vinculación normativa. Tienes el análisis completo de un proceso de \
participación ciudadana frente a un documento normativo. Escribe la síntesis final.

# Resumen del documento

{overview_intro}

# Áreas de vinculación identificadas

{themes_block}

# Propuestas no recogidas

{gaps_narrative}

# Datos de calibración (no citar cifras en el texto generado)

{stats_block}

---

Proporciona:

1. **vision_general**: 2-3 párrafos con una lectura cualitativa global de la alineación. \
Estructura: un párrafo de visión general del conjunto, luego (si hay datos) un párrafo sobre \
las propuestas ciudadanas y su reflejo en el documento, luego (si hay datos) un párrafo sobre \
las propuestas académicas. Integra patrones transversales \
(sesgos, concentraciones, grupos desatendidos) directamente en estos párrafos, sin \
una sección adicional. Omite el párrafo de un grupo si no hay datos para él. \
Usa adjetivos para calibrar ('amplia', 'concentrada', 'puntual', 'desigual') pero \
NO cites cifras ni conteos.
"""
