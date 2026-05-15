import logging
import re
import unicodedata

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from vinculante.application.ingestion.report_schemas import (
    AuthorExtraction,
    ExtractedProposalList,
)

_logger = logging.getLogger(__name__)

# Tier 1 keyword sets for proposal-table header detection (accent-stripped, lowercase)
_TITLE_KW = frozenset({"titulo", "criterio", "argumento", "propuesta", "medida", "nombre", "tema"})
_BODY_KW = frozenset({"desarrollo", "explicacion", "descripcion", "justificacion", "contenido", "posicion", "texto"})

# Headings that signal non-proposal content — skip LLM extraction on these
_SKIP_HEADINGS = frozenset({"bibliograf", "referencias", "bibliography", "references", "anexo", "apendice"})

# Headings that are subitems (propuesta/medida/criterio + N, or X.Y... nested numbering)
_SUBITEM_RE = re.compile(
    r"^\s*(propuesta|medida|criterio|argumento|articulo|art\.)\s+\d+",
    re.IGNORECASE,
)
_NESTED_NUM_RE = re.compile(r"^\s*\d+\.\d+")

# Vertical-keyed Medida/Título/Descripción table layout (committee/government reports)
_MEDIDA_HEADER_RE = re.compile(
    r"^\s*(medida|propuesta|recomendaci[oó]n|criterio)\s+(n[uú]mero\s+)?\d+\b",
    re.IGNORECASE,
)
_TITULO_PREFIX_RE = re.compile(r"^\s*t[ií]tulo\s*[\.\:]\s*", re.IGNORECASE)
_DESC_PREFIX_RE   = re.compile(r"^\s*descripci[oó]n\s*[\.\:]\s*", re.IGNORECASE)
# Combined: strips "Título. " / "Descripción: " at start of any line (table cells + LLM output)
_FIELD_PREFIX_RE  = re.compile(
    r"^\s*(t[ií]tulo\s*[\.\:]|descripci[oó]n\s*[\.\:])\s*",
    re.IGNORECASE | re.MULTILINE,
)

# Max characters from start of document for author extraction (~2 pages)
_AUTHOR_WINDOW = 2500

_AUTHOR_PROMPT = """\
Extrae el nombre del autor o autores de este documento académico a partir del texto de las primeras páginas.

- Si son varios individuos, devuelve sus nombres separados por coma.
- Si es una organización o colectivo, devuelve el nombre de la entidad.
- Si aparecen tanto individuos como una organización editora, devuelve primero los individuos \
seguidos de la organización entre paréntesis.
- Si no puedes determinarlo con certeza, devuelve "Desconocido".

TEXTO:
{text}"""

_EXTRACT_PROMPT = """\
Eres un extractor de propuestas políticas de documentos académicos.

El siguiente texto es el contenido completo de un documento, con marcadores de sección \
(## Sección / Subsección) para indicar la estructura.

Extrae todas las propuestas, medidas, recomendaciones o criterios políticos concretos del \
documento. Una propuesta es cualquier demanda o medida específica con un verbo de obligación, \
recomendación o compromiso (debe, deberá, se recomienda, se propone, hay que, sugerimos, etc.).

Para cada propuesta extrae:
- text: Texto VERBATIM del documento. Copia las oraciones exactamente como aparecen, incluyendo \
todo el desarrollo, justificación, listas con viñetas y ejemplos. NO resumas ni parafrasees. \
Preferir el texto más completo cuando la misma propuesta aparezca en varias secciones. \
Si la propuesta va precedida por una línea "Título. <frase>" en el documento, incluye esa \
frase verbatim como primera oración de text (sin el prefijo "Título."). \
Si la propuesta va seguida de una enumeración con viñetas (•, -) o de párrafos de aclaración \
inmediatamente posteriores (definiciones tipo "Se entiende como X a:…", matizaciones, ámbitos \
de aplicación), inclúyelos verbatim como parte del mismo text. NO los separes en propuestas \
distintas.
- title: Identificador del CONTENIDO de la propuesta si aparece explícitamente \
(e.g., "Etiquetado en dispositivos digitales", "Estado emprendedor"). \
NO uses etiquetas de numeración como "Medida 3" o "Medida número 5" — déjalo en null en ese caso.
- topic: Primera parte del encabezado más cercano (la parte ANTES de " / " si hay dos niveles). \
Cópialo tal como aparece en el texto, SIN el prefijo ##. Ignora etiquetas de numeración \
como "Medida número N" al elegir el topic; usa el encabezado temático más cercano.
- subtopic: Segunda parte del encabezado (la parte DESPUÉS de " / ") si existe y es diferente al topic. \
null si solo hay un nivel de encabezado. SIN el prefijo ##.

Ejemplo de encabezado con dos niveles:
  ## 3. Medidas económicas / 3.1.1. Vivienda
  → topic: "3. Medidas económicas"   subtopic: "3.1.1. Vivienda"

Ejemplo de encabezado con un nivel:
  ## 2.4. Reforzar el Consejo de la Juventud
  → topic: "2.4. Reforzar el Consejo de la Juventud"   subtopic: null
- indicators: Indicadores de seguimiento explícitos. Lista vacía si no hay.
- targets: Metas o compromisos cuantificados explícitos. Lista vacía si no hay.

Reglas críticas:
- Si la misma propuesta aparece en el RESUMEN, la INTRODUCCIÓN, el cuerpo del documento Y la \
CONCLUSIÓN, devuélvela UNA SOLA VEZ usando el texto más completo y detallado.
- No incluyas títulos de sección, etiquetas de categoría, textos introductorios, resúmenes \
generales del documento, ni paráfrasis de otras propuestas.
- No incluyas citas bibliográficas ni referencias.
- Devuelve lista vacía si el texto no contiene propuestas concretas.

DOCUMENTO:
{text}"""


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", t).lower().strip()


def _slugify(text: str) -> str:
    t = _normalize(text)
    t = re.sub(r"[^\w\s-]", "", t)
    t = re.sub(r"[\s_-]+", "-", t)
    return t.strip("-")[:80]


def _make_ref(seed: str, seen: dict[str, int]) -> str:
    base = _slugify(seed) or "proposal"
    if base in seen:
        seen[base] += 1
        return f"{base}-{seen[base]}"
    seen[base] = 0
    return base


def _norm_verbatim(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _is_verbatim(extracted: str, source: str) -> bool:
    return _norm_verbatim(extracted) in _norm_verbatim(source)


def _build_table_grid(table_data) -> list[list[str]]:
    grid: dict[tuple[int, int], str] = {}
    for cell in table_data.table_cells:
        key = (cell.start_row_offset_idx, cell.start_col_offset_idx)
        if key not in grid:
            grid[key] = (cell.text or "").strip()
    return [
        [grid.get((r, c), "") for c in range(table_data.num_cols)]
        for r in range(table_data.num_rows)
    ]


def _dedup_by_reference(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in rows:
        ref = row.get("reference", "")
        if ref not in seen:
            seen.add(ref)
            deduped.append(row)
    dropped = len(rows) - len(deduped)
    if dropped:
        _logger.info("Deduplicated %d proposal(s)", dropped)
    return deduped


def _format_prose_for_llm(prose_parts: list[tuple[list[str], str]]) -> str:
    sections: list[str] = []
    last_headings: list[str] = []
    for headings, text in prose_parts:
        non_empty = [h for h in headings if h and h.strip()]
        if non_empty != last_headings:
            sections.append("## " + " / ".join(non_empty))
            last_headings = non_empty
        sections.append(text)
    return "\n\n".join(sections)


def _is_subitem_heading(h: str) -> bool:
    return bool(_SUBITEM_RE.match(h) or _NESTED_NUM_RE.match(h))


def _clean_heading(h: str | None) -> str | None:
    if not h:
        return None
    return re.sub(r"^#+\s*", "", h).strip() or None


def _dedup_seed_tokens(seed: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for tok in seed.split():
        key = _normalize(tok)
        if key and key not in seen:
            seen.add(key)
            out.append(tok)
    return " ".join(out)


def _compute_topic_subtopic(headings: list[str]) -> tuple[str | None, str | None]:
    non_empty = [h for h in headings if h and h.strip()]
    if not non_empty:
        return None, None
    if len(non_empty) == 1:
        return non_empty[-1], None
    return non_empty[-2], non_empty[-1]


def _strip_field_prefixes(text: str) -> str:
    return _FIELD_PREFIX_RE.sub("", text)


def _looks_like_full_title(text: str) -> bool:
    """True when a medida-label heading has meaningful content beyond the 'Medida N' prefix."""
    m = _MEDIDA_HEADER_RE.match(text)
    if not m:
        return False
    remainder = text[m.end():].strip()
    return len(re.findall(r'\w{2,}', remainder)) >= 1


class ReportLoader:
    """Loads proposals from long-form reports (PDF or DOCX).

    Suitable for academic papers, government reports, NGO position papers, and
    similar documents. Uses Docling for layout-aware parsing and a two-tier
    extraction strategy:
    - Tier 1: structural table extraction for well-organized table-based sections.
    - Tier 2: LLM-based extraction for prose-heavy sections.
    """

    def __init__(self, llm=None, settings=None) -> None:
        from vinculante.infrastructure.config.settings import get_settings
        from vinculante.infrastructure.llm.factory import create_report_llm_from_env

        s = settings or get_settings()
        llm = llm or create_report_llm_from_env(s)
        self._author_llm = llm.with_structured_output(AuthorExtraction)
        self._extract_llm = llm.with_structured_output(ExtractedProposalList)
        # do_table_structure=False prevents Docling's table structure recognition
        # from truncating long table cells (e.g. multi-paragraph description cells
        # in committee-report PDFs). Content flows as text/list items instead.
        _pdf_opts = PdfPipelineOptions(do_table_structure=False)
        self._converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=_pdf_opts)}
        )

    def load(self, file_path: str) -> list[dict]:
        conv_res = self._converter.convert(file_path)
        dl_doc = conv_res.document

        author = self._extract_author(dl_doc)
        rows = self._extract_proposals(dl_doc)
        for row in rows:
            row["author"] = author
        return _dedup_by_reference(rows)

    # ------------------------------------------------------------------ author

    def _extract_author(self, dl_doc) -> str:
        parts: list[str] = []
        total = 0
        for item, _ in dl_doc.iterate_items():
            t = (getattr(item, "text", "") or "").strip()
            if t:
                parts.append(t)
                total += len(t)
                if total >= _AUTHOR_WINDOW:
                    break
        try:
            result = self._author_llm.invoke(_AUTHOR_PROMPT.format(text="\n".join(parts)))
            return result.author
        except Exception:
            _logger.exception("Author extraction failed; defaulting to 'Desconocido'")
            return "Desconocido"

    # ------------------------------------------------------------------ main extraction

    def _extract_proposals(self, dl_doc) -> list[dict]:
        tier1_rows: list[dict] = []
        tier1_keys: set[tuple[str | None, str | None]] = set()
        prose_parts: list[tuple[list[str], str]] = []
        seen_refs: dict[str, int] = {}
        current_theme: str | None = None
        current_subitem: str | None = None
        buf: list[str] = []

        def flush() -> None:
            if not buf:
                return
            headings = [h for h in (current_theme, current_subitem) if h]
            if headings:
                last = _normalize(headings[-1])
                if any(kw in last for kw in _SKIP_HEADINGS):
                    buf.clear()
                    return
            prose_parts.append((headings, "\n\n".join(buf)))
            buf.clear()

        for item, _ in dl_doc.iterate_items():
            label = str(getattr(item, "label", ""))
            text = (getattr(item, "text", "") or "").strip()
            level = getattr(item, "level", None)

            if label in ("section_header", "title"):
                if not text:
                    continue
                flush()
                if label == "section_header" and _MEDIDA_HEADER_RE.match(text) \
                        and not _looks_like_full_title(text):
                    buf.append(text)
                    continue
                if level is not None and level >= 2:
                    # DOCX: trust explicit hierarchy (level 2=theme, level 3+=subitem)
                    if level >= 3:
                        current_subitem = text
                    else:
                        current_theme, current_subitem = text, None
                elif _is_subitem_heading(text):
                    # PDF flat (all level=1): classify via text regex
                    current_subitem = text
                else:
                    current_theme, current_subitem = text, None
            elif label == "table":
                flush()
                headings = [h for h in (current_theme, current_subitem) if h]
                tier1 = self._try_tier1(item, headings, seen_refs)
                if tier1:
                    tier1_rows.extend(tier1)
                    tier1_keys.add((current_theme, current_subitem))
                else:
                    try:
                        md = item.export_to_markdown(dl_doc)
                        if md:
                            buf.append(_strip_field_prefixes(md))
                    except Exception:
                        _logger.exception("table markdown export failed")
            elif text:
                if (current_theme, current_subitem) in tier1_keys:
                    continue
                buf.append(text)

        flush()

        llm_rows: list[dict] = []
        if prose_parts:
            prose_blob = _format_prose_for_llm(prose_parts)
            llm_rows = self._llm_extract_doc(prose_blob, seen_refs)

        return tier1_rows + llm_rows

    def _llm_extract_doc(self, prose_blob: str, seen_refs: dict[str, int]) -> list[dict]:
        try:
            result = self._extract_llm.invoke(_EXTRACT_PROMPT.format(text=prose_blob))
            proposals = result.proposals
        except Exception:
            _logger.exception("LLM proposal extraction failed")
            return []

        rows: list[dict] = []
        for p in proposals:
            if not _is_verbatim(p.text, prose_blob):
                _logger.debug("Extracted text not verbatim in source: %.80s...", p.text)
            text = _strip_field_prefixes(p.text)
            if p.indicators:
                text += "\n\nIndicadores: " + "; ".join(p.indicators)
            if p.targets:
                text += "\n\nMetas: " + "; ".join(p.targets)
            ref_seed = _dedup_seed_tokens(
                f"{p.subtopic or p.topic or ''} {p.title or ' '.join(text.split()[:8])}"
            )
            rows.append({
                "text": text,
                "reference": _make_ref(ref_seed, seen_refs),
                "topic": _clean_heading(p.topic),
                "subtopic": _clean_heading(p.subtopic),
            })
        return rows

    # ------------------------------------------------------------------ Tier 1

    def _try_tier1(
        self,
        table_item,
        headings: list[str],
        seen_refs: dict[str, int],
    ) -> list[dict]:
        try:
            table_data = table_item.data
        except AttributeError:
            return []
        if table_data is None:
            return []

        if table_data.num_cols not in (2, 3):
            return []

        grid = _build_table_grid(table_data)
        if len(grid) < 2:
            return []

        header = [_normalize(cell) for cell in grid[0]]
        title_col = next(
            (i for i, h in enumerate(header) if any(kw in h for kw in _TITLE_KW)), None
        )
        body_col = next(
            (i for i, h in enumerate(header) if any(kw in h for kw in _BODY_KW)), None
        )

        if title_col is None or body_col is None or title_col == body_col:
            return []

        topic, subtopic = _compute_topic_subtopic(headings)
        rows: list[dict] = []
        for row in grid[1:]:
            title = row[title_col] if title_col < len(row) else ""
            body = row[body_col] if body_col < len(row) else ""
            if not body:
                continue
            text = f"{title}\n\n{body}" if title and body else (title or body)
            ref_seed = f"{subtopic or topic or ''} {title or ' '.join(body.split()[:8])}"
            rows.append({
                "text": text,
                "reference": _make_ref(ref_seed, seen_refs),
                "topic": topic,
                "subtopic": subtopic,
            })
        return rows
