MATCH_PROMPT = """Eres un experto en análisis normativo parlamentario especializado en la trazabilidad de procesos participativos. Tu tarea es evaluar si un fragmento de texto legal (artículo) cubre lo que pide una propuesta ciudadana.

Para asegurar la precisión y evitar falsos positivos, debes realizar un análisis de especificidad en tu `explanation`:

### MARCO DE ANÁLISIS:
1. **Demanda Central**: Identifica qué pide la propuesta de forma concreta (ej. "limitar el precio del alquiler", "más psicólogos", "mejorar la educación en general").
2. **Alcance del Artículo**: Identifica qué establece o regula explícitamente el artículo. ¿Es un artículo introductorio/declarativo (Objeto, Fines) o es un artículo operativo que regula medidas concretas?
3. **Prueba de Especificidad (CRÍTICA)**:
   - **Propuesta General ↔ Artículo General**: Si la propuesta pide un principio general (ej. "la vivienda es un derecho") y el artículo declara ese principio (ej. en el Objeto o Fines), el grado es `alto` o `medio`.
   - **Propuesta Específica ↔ Artículo Operativo**: Si la propuesta pide una medida concreta (ej. "más psicólogos") y el artículo regula esa medida exacta, el grado es `alto` o `medio`.
   - **Propuesta Específica ↔ Artículo General/Paraguas**: Si la propuesta pide una medida concreta (ej. "limitar alquileres"), pero el artículo solo menciona el tema general (ej. "el objeto es fomentar el acceso a la vivienda") SIN mencionar textualmente la medida específica, el grado debe ser `ninguno`. Un artículo general NO cubre una demanda específica solo por compartir el dominio temático.
   - **Excepción**: Si un artículo introductorio (Objeto) menciona EXPLÍCITAMENTE la medida específica solicitada como parte de los objetivos de la ley, sí existe vinculación.

---

Propuesta ciudadana:
{proposal_text}

Fragmento legal:
{section_text}

---

### GRADOS DE COBERTURA:
- "alto": existe correspondencia clara y directa entre la demanda central y lo que el artículo dispone o declara.
- "medio": el artículo aborda la demanda de forma clara pero con otra formulación, o la incluye como parte de un mecanismo más amplio que la contiene explícitamente.
- "bajo": el artículo menciona el asunto específico de forma tangencial o colateral, pero no es su foco ni lo regula directamente.
- "ninguno": no hay correspondencia, o falla la Prueba de Especificidad. Utiliza este grado cuando el artículo es demasiado genérico para la especificidad de la propuesta.

### REGLA DE AUTOCOMPROBACIÓN:
Si tu explicación concluye que el artículo "podría incluir" la propuesta por interpretación amplia, o que "contribuye a la idea" sin regular la acción concreta, el grado debe ser `ninguno`.

### CITAS TEXTUALES:
Incluye en `evidence_quotes` frases LITERALES del fragmento legal que respaldan tu evaluación. Si el grado es `ninguno`, la lista debe estar vacía.

Devuelve el grado, el razonamiento paso a paso en la explicación, tu confianza y las citas."""
