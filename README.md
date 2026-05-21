# Vinculante

Herramienta de [Political Watch](https://politicalwatch.es) para vincular automáticamente insumos participativos (propuestas ciudadanas, sociedad civil, academia) con el contenido de un texto normativo.

Por cada propuesta vinculada genera: el grado de incorporación (`fuerte / moderado`) y una explicación razonada producida por LLM. Adicionalmente se genera un resumen ejecutivo y estadísticas sobre el proceso. Los resultados se pueden revisar mediante la interfaz web.

---

## Arquitectura

| Componente | Stack |
|---|---|
| `engine/` | Python 3.13 · FastAPI · LangGraph · Typer CLI |
| `frontend/` | Nuxt 4 · @nuxt/ui 4 · Tailwind 4 |
| Datos | PostgreSQL 17 + pgvector · Redis 8.2 |

El engine sigue una estructura hexagonal: `domain / application / infrastructure / presentation`.

---

## Requisitos

- Docker + Docker Compose
- Node 20+ (solo para desarrollo del frontend en local)
- Clave API del proveedor LLM elegido (Anthropic, OpenAI, Google Gemini, Mistral u Ollama)

---

## Puesta en marcha

```bash
# 1. Configurar variables de entorno
cp engine/.env.example engine/.env       # editar LLM_PROVIDER, API keys, MATCHING_*
cp frontend/.env.example frontend/.env  # editar NUXT_PUBLIC_API_BASE

# 2. Levantar infraestructura + API
docker compose up

# API disponible en http://localhost:8000
# Frontend (dev local):
cd frontend && npm install && npm run dev   # http://localhost:3000
```

---

## Pipeline CLI

Todos los comandos se ejecutan dentro del contenedor engine:

```
docker compose exec engine uv run vinculante <subcomando>
```

### 1. Ingesta

Cargar el texto normativo (documento objetivo):

```bash
docker compose exec engine uv run vinculante ingest target \
  --file data/in/ley-juventud.pdf \
  --title "Anteproyecto de Ley de Juventud" \
  --author "Ministerio de Juventud e Infancia" \
  --version "v1.0"
```

Cargar propuestas participativas (CSV, XLSX, DOCX o PDF):

```bash
docker compose exec engine uv run vinculante ingest proposals \
  --file data/in/propuestas.xlsx \
  --target-id 1 \
  --author-type "citizen"

# Para PDF o DOCX de tipo informe, usar --use-report-loader (extracción asistida por LLM):
docker compose exec engine uv run vinculante ingest proposals \
  --file data/in/informe.pdf \
  --target-id 1 \
  --use-report-loader
```

### 2. Embeddings

Generar embeddings de las secciones del texto normativo:

```bash
docker compose exec engine uv run vinculante embed sections --target-id 1
```

Generar embeddings de las propuestas:

```bash
docker compose exec engine uv run vinculante embed proposals --target-id 1
```

### 3. Matching

Ejecutar la vinculación semántica + verificación crítica por LLM:

```bash
docker compose exec engine uv run vinculante match run --target-id 1

# Filtrar por tema (omite el resumen ejecutivo automático):
docker compose exec engine uv run vinculante match run --target-id 1 --topic "vivienda"

# Reutilizar vinculaciones ya calculadas (no recalcula):
docker compose exec engine uv run vinculante match run --target-id 1 --skip-matched
```

### Generación auxiliar

Generar o regenerar lenguaje claro para las secciones. Estos se generan de forma automática durante el proceso normal de ingesta y match, pero pueden ejecutarse de forma manual si fuese necesario (por ejemplo, al excluirlos mediante flag).

```bash
docker compose exec engine uv run vinculante generate clear-language --target-id 1 [--force]
```

Generar o regenerar resumen ejecutivo:

```bash
docker compose exec engine uv run vinculante generate summary 1
```

### Exportación

```bash
# Exportar a CSV (por defecto):
docker compose exec engine uv run vinculante export matches --target-id 1

# Exportar a XLSX filtrado por estado:
docker compose exec engine uv run vinculante export matches \
  --target-id 1 \
  --format xlsx \
  --match-status confirmed
```

### Evaluación

Evaluar calidad del matching contra un testset de referencia:

```bash
docker compose exec engine uv run vinculante evaluate run \
  --testset data/eval/testset.json \
  --domain igualdad \
  --min-degree bajo

# Auditar recall de recuperación (antes de ajustar top_k):
docker compose exec engine uv run vinculante evaluate retrieval --domain igualdad

# Ver un informe guardado:
docker compose exec engine uv run vinculante evaluate show data/eval/results/run_001.json
```

### Base de datos

```bash
# Resetear todas las tablas (destructivo):
docker compose exec engine uv run vinculante db reset --yes
```

---

## Ejemplo end-to-end

```bash
docker compose exec engine uv run vinculante ingest target \
  --file data/in/ley.pdf --title "Ley de Juventud" --author "Ministerio de Juventud e Infancia"

docker compose exec engine uv run vinculante ingest proposals \
  --file data/in/propuestas.xlsx --target-id 1

docker compose exec engine uv run vinculante embed sections --target-id 1
docker compose exec engine uv run vinculante embed proposals --target-id 1

docker compose exec engine uv run vinculante match run --target-id 1
```

---

## Servicios Docker

| Archivo | Uso |
|---|---|
| `docker-compose.yml` | Desarrollo: postgres + redis + engine (hot-reload) |
| `docker-compose-pro.yml` | Producción: añade el frontend (`politicalwatch/vinculante:latest`) |

Scripts de utilidad: `backup.sh`, `restore.sh`, `reset_db.sh`, `reset_db_pro.sh`.

---

## Estructura del repositorio

```
vinculante/
├── engine/               # Backend (FastAPI + CLI)
│   ├── vinculante/       # Código fuente (domain, application, infrastructure, presentation)
│   ├── alembic/          # Migraciones de base de datos
│   ├── data/             # Datos de evaluación y exportación
│   └── tests/
├── frontend/             # Aplicación Nuxt 4
│   └── app/              # pages/, components/, composables/
├── docs/                 # Documentación adicional
├── notebooks/            # Exploración y análisis
└── backups/              # Copias de seguridad
```

---

## Tests

```bash
# Engine
docker compose exec engine uv run pytest

# Frontend
cd frontend
npm run test          # Vitest (unitarios)
npm run test:e2e      # Playwright (end-to-end)
```

---

## Créditos

Proyecto desarrollado por [Political Watch](https://politicalwatch.es).

Licenciado bajo la [GNU Affero General Public License v3.0](LICENSE.txt) — cualquier despliegue del software (incluyendo uso en red) debe poner a disposición su código fuente bajo la misma licencia.
