ANALYZE_PROPOSAL = """Eres un experto en análisis de políticas públicas. Tu tarea es extraer la "Demanda Central" de una propuesta ciudadana.

### INSTRUCCIONES:
1. **Clasifica**: ¿La propuesta pide algo CONCRETO (un mecanismo, un programa, un derecho prestacional) o es una declaración GENERAL de principios?
2. **Extrae la Demanda**: Describe en una frase corta qué se pide exactamente.
3. **Identifica el Dominio**: ¿De qué trata el tema (Vivienda, Educación, Salud, etc.)?

### PROPUESTA:
{proposal_text}

### FORMATO DE SALIDA:
Genera un objeto JSON con `is_specific`, `core_demand` y `domain`."""

CLASSIFY_CANDIDATES = """Eres un experto en técnica legislativa. Tu tarea es clasificar una lista de artículos según su naturaleza.

### CATEGORÍAS:
- **Operativo**: Artículos que regulan medidas concretas, crean programas, establecen obligaciones o garantizan derechos específicos.
- **Introductorio**: Artículos de Objeto, Ámbito de aplicación, Fines, Definiciones o Principios Generales que NO regulan una medida concreta por sí mismos.

### ARTÍCULOS:
{candidates_text}

### FORMATO DE SALIDA:
Genera un objeto JSON con las listas `operative_ids` e `introductory_ids`."""

SCORE_CANDIDATE = """Eres un experto en análisis normativo. Evalúa si el siguiente artículo legal cubre la demanda central de una propuesta ciudadana.

### CONTEXTO DE LA PROPUESTA:
- **Demanda Central**: {core_demand}
- **Dominio**: {domain}

### ARTÍCULO A EVALUAR:
{section_text}

---

### CRITERIOS DE VINCULACIÓN:
- **Si el artículo es Operativo**: Solo puntúa `alto` o `medio` si regula EXPLÍCITAMENTE la demanda central.
- **Si el artículo es Introductorio**: Solo puntúa `alto` o `medio` si la demanda es GENERAL y el artículo declara ese mismo principio. Si la demanda es ESPECÍFICA, un artículo introductorio debe marcarse como `ninguno` a menos que mencione la medida textualmente.

### REGLA DE ORO:
Buscamos el encaje más específico posible. Si el artículo solo "comparte el tema" pero no aborda la demanda concreta, el grado es `ninguno`.

Devuelve `degree`, `explanation`, `confidence` y `evidence_quotes`."""
