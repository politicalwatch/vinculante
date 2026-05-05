MATCH_PROMPT = """Eres un experto en análisis normativo parlamentario. Tu tarea es evaluar si un fragmento de texto legal cubre lo que pide una propuesta ciudadana.

PRINCIPIO: el grado se determina por lo que el fragmento realmente dispone, no por la mera afinidad temática con el dominio (vivienda, educación, etc.). Un artículo cubre una propuesta cuando sus disposiciones abordan la misma necesidad, derecho o acción, aunque la propuesta lo exprese con otras palabras o en lenguaje coloquial.

Propuesta ciudadana:
{proposal_text}

Fragmento legal:
{section_text}

Criterios (elige el grado más alto que se cumpla):

- "alto": el fragmento menciona de forma explícita la acción, mecanismo o garantía que pide la propuesta. Existe correspondencia clara entre lo que la propuesta pide y lo que el artículo dispone.

- "medio": las disposiciones del fragmento abordan lo que pide la propuesta, aunque con otra formulación, o lo incluyen como parte de un mecanismo más amplio. La propuesta encaja dentro del alcance textual del artículo, aunque no sea su foco principal. Paráfrasis y equivalencias semánticas cuentan como cobertura (p. ej. "profesionales preparados para escuchar y ayudar" ↔ "incorporación de orientadores y psicólogos"; "jóvenes puedan independizarse" ↔ artículo que prioriza a jóvenes en la vivienda pública).

- "bajo": el fragmento toca el asunto específico que plantea la propuesta, pero con tratamiento limitado o colateral. Hay mención al tema concreto (no sólo al dominio general), pero el artículo no regula el mecanismo exacto que pide la propuesta.

- "ninguno": el fragmento sólo comparte el dominio temático con la propuesta pero no aborda la cuestión específica. Utiliza este grado cuando:
  * el fragmento habla del ámbito general (vivienda, educación, etc.) sin abordar la necesidad o acción concreta de la propuesta;
  * la propuesta sólo encajaría por interpretación muy amplia o inferencia remota;
  * el fragmento coincidiría igualmente con cualquier propuesta del dominio (señal de que no hay correspondencia específica).

Consideraciones importantes:
- La propuesta suele estar en lenguaje coloquial y el artículo en lenguaje técnico-jurídico. Busca correspondencia de fondo, no literal. No exijas que el artículo use las mismas palabras que la propuesta.
- Un artículo de "Objeto" o "Ámbito de aplicación" cubre una propuesta sólo cuando ésta se refiere al propósito o alcance de la ley (p. ej. "la vivienda es un derecho" ↔ Objeto), no a cualquier medida concreta del dominio.
- Si el fragmento regula varias materias, pregúntate si alguna de ellas corresponde específicamente a lo que pide la propuesta.

REGLA DE AUTOCOMPROBACIÓN (crítica):
Antes de asignar el grado, revisa tu propia explicación. Si contiene alguna de estas fórmulas hedging — "de forma indirecta", "aborda la idea", "recoge la idea", "sin embargo no regula", "sin embargo no establece", "no formula expresamente", "no establece una regla directa", "no regula de forma expresa", "puede contribuir", "contribuye a", "de forma general" — entonces el artículo NO cubre la propuesta: el grado debe ser `ninguno`.
Un artículo que sólo "aborda la idea" o "contribuye" al tema sin regular la acción o mecanismo concreto de la propuesta NO es cobertura.

CITAS TEXTUALES (obligatorio para grado alto/medio/bajo):
Incluye en `evidence_quotes` una lista con las frases o disposiciones del fragmento legal que respaldan tu evaluación. Copia cada cita LITERALMENTE del texto del artículo (entre 15 y 200 caracteres cada una). Puede haber más de una si la evidencia está en varias partes del artículo. Si no encuentras ninguna cita textual que sustente un grado distinto de `ninguno`, el grado debe ser `ninguno` y `evidence_quotes` debe ser una lista vacía.

Devuelve el grado, una explicación breve, tu nivel de confianza y las citas textuales."""
