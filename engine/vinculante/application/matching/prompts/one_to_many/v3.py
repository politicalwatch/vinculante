MATCH_PROMPT = """Eres un experto en técnica legislativa. Evalúa la siguiente propuesta ciudadana frente a una lista de artículos candidatos.

### PASO 1: Identifica la naturaleza de la propuesta
- **Propuesta Declarativa (Abstracta):** Expresa un principio, una equiparación de derechos o un deseo general (ej. "la salud mental importa igual que la física", "la vivienda es un derecho").
- **Propuesta Operativa (Concreta):** Exige una medida, recurso o mecanismo específico (ej. "contratar más psicólogos", "más ayudas al alquiler").

### PASO 2: Reglas de Asignación
1. **Si la propuesta es Declarativa:** Tu objetivo prioritario son los artículos introductorios (**Objeto, Ámbito de aplicación, Fines, Principios**). Si alguno menciona el tema de la propuesta, asígnale `alto` o `medio`.
2. **Si la propuesta es Operativa:** Busca el artículo que regule exactamente esa medida. Ese es el Regulador Primario.
3. **Evita la Redundancia:** No puntúes `medio` o `alto` en artículos que solo comparten palabras clave pero no regulan la demanda material. Sé decisivo: prefiere un solo artículo `alto` que repartir varios `medio`.

### PROPUESTA CIUDADANA:
{proposal_text}

### ARTÍCULOS CANDIDATOS:
{candidates_text}

---

Devuelve un análisis comparativo para cada ID. Prioriza la especificidad regulatoria."""
