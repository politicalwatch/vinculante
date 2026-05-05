MATCH_PROMPT = """Eres un experto en análisis normativo parlamentario. Tu tarea es evaluar una propuesta ciudadana frente a una lista de artículos candidatos extraídos de un texto legal.

Debes identificar qué artículos cubren realmente la propuesta, diferenciando entre la vinculación "Primaria" (donde se regula la medida específica) y la vinculación por "Afinidad Temática" (que suele ser ruido o contexto general).

### PROPUESTA CIUDADANA:
{proposal_text}

### ARTÍCULOS CANDIDATOS:
{candidates_text}

---

### INSTRUCCIONES DE EVALUACIÓN:
1. **Análisis Comparativo**: Revisa todos los artículos antes de calificar ninguno. A menudo, un artículo operativo regula exactamente lo que pide la propuesta, mientras que otros artículos (Objeto, Ámbito) solo mencionan el tema de forma genérica.
2. **Prioriza la Especificidad**: Si encuentras un artículo que regula el mecanismo específico solicitado, marca ese como `alto` o `medio`. Los artículos que solo comparten el dominio temático pero no regulan la acción concreta deben marcarse como `ninguno`.
3. **Regla del Objeto/Ámbito**: Solo vincula con artículos de "Objeto" o "Ámbito de aplicación" si la propuesta es una declaración de principios general o si el artículo menciona EXPLÍCITAMENTE la medida concreta. Si hay un artículo operativo mejor, prefiere calificar el operativo y dejar el de Objeto como `ninguno` o `bajo` para evitar redundancia.

### FORMATO DE RESPUESTA:
Para cada artículo (por su ID), proporciona:
- `degree`: "alto", "medio", "bajo" o "ninguno".
- `explanation`: Razonamiento de por qué este artículo es (o no) una vinculación válida comparado con los demás.
- `confidence`: Nivel de certeza.
- `evidence_quotes`: Citas textuales si el grado no es `ninguno`.

Identifica el mejor encaje y evita los falsos positivos por mera coincidencia de palabras clave."""
