PROMPT = """\
Eres un analista de vinculación normativa. Tu tarea es identificar las lagunas reales: \
propuestas y secciones del documento que no han encontrado vinculación aceptada.

# Áreas temáticas cubiertas por el análisis

{themes_block}

# Secciones del documento sin vinculación (con contenido relevante)

{orphan_sections_block}

# Propuestas sin vinculación aceptada

{unmatched_proposals_block}

---

## Paso A — Filtro de ámbito

Antes de aplicar ningún criterio, clasifica mentalmente cada propuesta sin vinculación como:

- **Gap real**: la propuesta encaja temáticamente con el documento normativo y reclama \
algo que esa norma podría o debería abordar, pero no aborda.
- **Fuera de ámbito**: la propuesta corresponde a otra ley, otra cartera ministerial, \
u otro nivel administrativo. La razón a menudo aparece en el campo \
`Razón de no vinculación` \
(ej. "competencia autonómica", "fuera del ámbito de esta norma", \
"corresponde a otro ministerio").

Las propuestas fuera de ámbito **NO son gaps reales**: omítelas del análisis principal. \
Si una parte notable de las propuestas se sitúa fuera del ámbito, menciónalo brevemente \
en `gaps_narrative` como observación meta \
(ej. "una parte significativa de las propuestas se dirige a competencias ajenas a esta \
norma").

## Paso B — Selección con criterios

Para los gaps reales, prioriza los que mejor ilustran el grupo equilibrando estos criterios:

- **Consenso**: cuando varias propuestas independientes plantean la misma demanda no \
recogida (juzga la similitud comparando los textos del bloque).
- **Innovación**: cuando una propuesta singular plantea un ángulo distintivo y relevante \
no abordado por la norma, aunque no tenga consenso.
- **Especificidad**: cuando la propuesta plantea un mecanismo concreto \
(cifras, instituciones, procedimientos) en lugar de un objetivo genérico.
- **Autoridad académica** (solo en el bloque académico): cuando la autoría aporta \
especialización relevante al ámbito no cubierto.

Trata de que los gaps mencionados no respondan todos al mismo criterio — \
busca variedad cuando los datos lo permitan.

---

Escribe un análisis de lagunas con cuatro partes:

1. **orphan_observations**: Observaciones sobre las secciones del documento sin propuestas
vinculadas, si hay un patrón claro. 1-2 frases. Vacío si no hay patrones relevantes.

2. **citizen_unmatched**: 1-2 párrafos sobre los gaps reales ciudadanos (propuestas \
en ámbito sin vinculación aceptada). \
Agrupa por tema sin revelar identidades individuales. \
Aplica los criterios del Paso B para priorizar qué mencionar. \
Introduce el párrafo de forma natural \
(ej. "Las propuestas ciudadanas que no han encontrado vinculación..."). \
Vacío si no hay gaps ciudadanos reales.

3. **academia_unmatched**: 1-2 párrafos sobre los gaps reales académicos \
(propuestas académicas en ámbito sin vinculación aceptada). \
Cita autores cuando aporten señal. \
Aplica los criterios del Paso B para priorizar qué mencionar. \
Introduce el párrafo de forma natural. \
Vacío si no hay gaps académicos reales.

4. **gaps_narrative**: Síntesis de los gaps principales en 1 párrafo. \
Si una parte notable de las propuestas estaba fuera del ámbito de la norma, \
menciónalo aquí brevemente.
"""
