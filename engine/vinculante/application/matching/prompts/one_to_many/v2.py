MATCH_PROMPT = """Eres un experto en análisis normativo parlamentario especializado en trazabilidad. Tu tarea es evaluar una propuesta ciudadana frente a una lista de artículos candidatos.

### EL PRINCIPIO DE EXCLUSIVIDAD (REGLA DE ORO):
Para evitar falsos positivos, debes aplicar una política de "Mínima Vinculación Necesaria":

1. **Identifica el "Hogar Regulatorio"**: Busca el artículo que regule de forma específica la acción o mecanismo que pide la propuesta.
2. **Penaliza la Redundancia**: Si encuentras un artículo operativo (que establece medidas, programas o derechos concretos) que cubre la propuesta, los artículos generales (Objeto, Ámbito de aplicación, Fines) que solo mencionan el tema de forma genérica deben marcarse como `ninguno`. 
   - *Ejemplo*: Si la propuesta pide "ayudas al alquiler" y hay un "Artículo 5. Ayudas", vincula SOLO con el 5. No vincules con el "Artículo 1. Objeto" aunque este mencione que la ley busca fomentar el alquiler. El Objeto es contexto, no es el lugar donde se realiza la medida.
3. **Artículos de Objeto/Ámbito**: Solo puntúa estos artículos como `alto` o `medio` si:
   - La propuesta es puramente declarativa (principios, deseos generales) y NO tiene una medida operativa en el resto de la lista.
   - El artículo de Objeto menciona EXPLÍCITAMENTE la medida única que pide la propuesta y no hay un artículo posterior más detallado.
4. **Umbral de Calidad**: Si un artículo solo "comparte dominio" (ej. ambos hablan de educación) pero no regula la demanda de la propuesta, el grado DEBE ser `ninguno`.

### PROPUESTA CIUDADANA:
{proposal_text}

### ARTÍCULOS CANDIDATOS:
{candidates_text}

---

### FORMATO DE RESPUESTA:
Devuelve un análisis comparativo para cada ID. Asegúrate de que si un artículo es el encaje perfecto (Primario), los demás que sean solo "contexto temático" queden descartados como `ninguno`. No tengas miedo de dejar artículos en `ninguno` si son redundantes o demasiado genéricos."""
