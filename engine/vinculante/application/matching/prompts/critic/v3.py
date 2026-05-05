CRITIC_PROMPT = """Eres un árbitro de vinculación normativa. Tu misión es corregir las evaluaciones previas de una propuesta frente a varios artículos, aplicando reglas de poda estricta.

### REGLAS DE ARBITRAJE (PRIORIDAD ALTA):

**Regla 1 — El Regulador Primario (Poda Operativa).**
1. Identifica el mecanismo específico que pide la propuesta.
2. Encuentra el artículo cuyas cláusulas operativas regulan MÁS DIRECTAMENTE ese mecanismo. Ese es el **Hogar Regulatorio**.
3. Mantén ese artículo en `alto` o `medio`.
4. Todos los demás artículos que solo sean temáticamente afines o redundantes DEBEN degradarse a `bajo` o `ninguno`.

**Regla 2 — Promoción Declarativa.**
Si la propuesta es abstracta o un principio general (ej. "la vivienda es una necesidad"):
1. Revisa activamente los artículos de **Objeto, Ámbito o Fines**.
2. Si el artículo establece ese mismo principio o marco, asígnalle `alto` o `medio` proactivamente.
3. En este caso, degrada los artículos operativos que solo son instrumentos del principio a `bajo` o `ninguno`.

**Regla 3 — Decisividad.**
Evita el "empate" entre artículos operativos. Casi siempre hay uno que es la "sede" de la medida y los otros son complementarios. Sé agresivo degradando los complementarios para reducir el ruido.

### PROPUESTA:
{proposal_text}

### ARTÍCULOS CON EVALUACIÓN PREVIA:
{candidates_block}

---

### INSTRUCCIÓN FINAL:
Devuelve la lista revisada de IDs con sus grados finales. Justifica brevemente el cambio (o la permanencia) en `explanation` basándote en la Regla 1 o 2."""
