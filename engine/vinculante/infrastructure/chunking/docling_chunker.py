import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from math import ceil

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
from docling_core.types.doc.document import ContentLayer

_INLINE_MD_RE = re.compile(r"[\*_]+")

_MIN_PAGES_FOR_DETECTION = 3
_FURNITURE_PAGE_RATIO = 0.3
_MIN_FURNITURE_LINE_LENGTH = 6
_LIST_MARKER_RE = re.compile(r"^(?:\d+\.|[a-z]\)|-)\s")
_FURNITURE_LABELS = {"page_header", "page_footer"}
_HEADER_ZONE_TOP_PCT = 0.12    # t < 12% of page height → header zone (TOPLEFT origin)
_FOOTER_ZONE_BOTTOM_PCT = 0.93  # b > 93% of page height → footer zone (TOPLEFT origin)
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_TEMPLATE_DIGIT_RE = re.compile(r"\d+")
_TEMPLATE_MAX_LITERAL_LEN = 10  # excludes dates ("11 de abril de 2025"), keeps "Pág. ", "Núm. -"


def _strip_inline_md(s: str) -> str:
    return _INLINE_MD_RE.sub("", s)


def _normalize_line(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).casefold().strip()


def _is_plausible_furniture(norm: str) -> bool:
    if len(norm) < _MIN_FURNITURE_LINE_LENGTH:
        return False
    if _LIST_MARKER_RE.match(norm):
        return False
    if re.fullmatch(r"[\d\s.,;:\-/]+", norm):
        return False
    return True


def _strip_phrase(text: str, phrase: str) -> str:
    """Remove `phrase` from `text` with whitespace-flexible matching."""
    tokens = phrase.split()
    if not tokens:
        return text
    pattern = re.compile(r"\s*".join(re.escape(t) for t in tokens), re.IGNORECASE)
    return pattern.sub("", text)


@dataclass
class _FurnitureMatchers:
    lines: set[str] = field(default_factory=set)        # normalized full lines to strip
    refs: set[str] = field(default_factory=set)          # doc-item self_refs to strip by substring
    phrases: dict[str, str] = field(default_factory=dict)  # ref -> raw text phrase
    templates: list = field(default_factory=list)        # compiled regex patterns for templated phrases


def _detect_furniture(dl_doc) -> _FurnitureMatchers:
    """Detect page-furniture items via label/layer, text repetition, and bbox position.

    Combines three signals:
    1. Docling's own label (page_header/page_footer) or ContentLayer.FURNITURE.
    2. Text-repetition: any normalized line appearing on ≥ threshold distinct pages.
    3. Bbox-zone: items in the top-12% or bottom-7% of their page (TOPLEFT origin),
       confirmed when such items exist on ≥ threshold distinct pages AND the
       individual item's text repeats across ≥ threshold zone pages or matches a
       numeric template that does. This guards against stripping unique body lines
       whose bbox happens to land near the top of a page.
    """
    num_pages = dl_doc.num_pages()
    threshold = max(2, ceil(num_pages * _FURNITURE_PAGE_RATIO))

    auto_lines: set[str] = set()
    page_occurrences: dict[str, set[int]] = defaultdict(set)

    # For bbox-zone detection: (self_ref, raw_text, page_no)
    zone_pages: set[int] = set()
    zone_items: list[tuple[str, str, int]] = []

    for item, _ in dl_doc.iterate_items(included_content_layers=set(ContentLayer)):
        text = getattr(item, "text", None)
        if not text:
            continue
        prov = getattr(item, "prov", None)
        if not prov:
            continue
        page_no = prov[0].page_no
        ref = getattr(item, "self_ref", None)

        label = str(getattr(item, "label", "") or "")
        content_layer = getattr(item, "content_layer", None)
        is_labeled_furniture = (
            label in _FURNITURE_LABELS
            or content_layer == ContentLayer.FURNITURE
        )

        norm = _normalize_line(text)
        if not norm:
            continue

        # Signal 1: Docling label / content layer
        if is_labeled_furniture:
            auto_lines.add(norm)

        # Signal 2: text repetition (constant text across pages)
        if num_pages >= _MIN_PAGES_FOR_DETECTION and _is_plausible_furniture(norm):
            page_occurrences[norm].add(page_no)

        # Signal 3: bbox zone
        bbox = getattr(prov[0], "bbox", None)
        if bbox is not None and ref and num_pages >= _MIN_PAGES_FOR_DETECTION:
            page_info = dl_doc.pages.get(page_no)
            if page_info is not None:
                H = page_info.size.height
                if H > 0:
                    try:
                        bbox_tl = bbox.to_top_left_origin(H)
                        in_header = bbox_tl.t < H * _HEADER_ZONE_TOP_PCT
                        in_footer = bbox_tl.b > H * _FOOTER_ZONE_BOTTOM_PCT
                        if in_header or in_footer:
                            zone_pages.add(page_no)
                            zone_items.append((ref, text, page_no))
                    except Exception:
                        pass

    repeated_lines = {
        norm
        for norm, pages in page_occurrences.items()
        if len(pages) >= threshold
    }

    matchers = _FurnitureMatchers(lines=auto_lines | repeated_lines)

    # Promote zone candidates only when the overall zone is confirmed AND each
    # individual phrase recurs on ≥ threshold zone pages (identical text or
    # numeric-template match). This prevents unique body lines that happen to
    # land at the top of a page from being treated as furniture.
    if len(zone_pages) >= threshold:
        zone_text_pages: dict[str, set[int]] = defaultdict(set)
        zone_text_refs: dict[str, list[tuple[str, str]]] = defaultdict(list)
        zone_tmpl_pages: dict[str, set[int]] = defaultdict(set)
        zone_tmpl_refs: dict[str, list[tuple[str, str]]] = defaultdict(list)

        for ref, phrase, page_no in zone_items:
            norm = _normalize_line(phrase)
            zone_text_pages[norm].add(page_no)
            zone_text_refs[norm].append((ref, phrase))
            if _TEMPLATE_DIGIT_RE.search(phrase):
                tmpl = _TEMPLATE_DIGIT_RE.sub("\x00", phrase)
                zone_tmpl_pages[tmpl].add(page_no)
                zone_tmpl_refs[tmpl].append((ref, phrase))

        # Identical-text groups spanning ≥ threshold zone pages
        for norm, pages in zone_text_pages.items():
            if len(pages) >= threshold:
                matchers.lines.add(norm)
                for ref, phrase in zone_text_refs[norm]:
                    matchers.refs.add(ref)
                    matchers.phrases[ref] = phrase

        # Numeric-template groups ("Pág. N", "Núm. N-N" …)
        # (e.g. "Pág. 1"…"Pág. 37" → pattern r"Pág\.\s*\d+" applied document-wide).
        # This catches furniture fused into body items by the OCR engine.
        for tmpl, pages in zone_tmpl_pages.items():
            if len(pages) >= threshold:
                literal_only = tmpl.replace("\x00", "")
                if len(literal_only) < _TEMPLATE_MAX_LITERAL_LEN:
                    parts = tmpl.split("\x00")
                    pattern_str = r"\d+".join(re.escape(p) for p in parts)
                    matchers.templates.append(re.compile(pattern_str, re.IGNORECASE))
                    for ref, phrase in zone_tmpl_refs[tmpl]:
                        matchers.refs.add(ref)
                        matchers.phrases[ref] = phrase
                        matchers.lines.add(_normalize_line(phrase))

        # Substring promotion: zone items whose normalized text is fully contained
        # in an already-confirmed furniture phrase. Catches per-page variants where
        # Docling emits column elements as separate DocItems ("Serie A" + "Núm. 52-1"
        # on some pages) rather than as one joined item ("Serie A Núm. 52-1").
        confirmed_norms = {n for n in matchers.lines if len(n) >= _MIN_FURNITURE_LINE_LENGTH}
        for ref, phrase, _pg in zone_items:
            if ref in matchers.refs:
                continue
            norm = _normalize_line(phrase)
            if len(norm) < _MIN_FURNITURE_LINE_LENGTH:
                continue
            for big in confirmed_norms:
                if norm != big and norm in big:
                    matchers.refs.add(ref)
                    matchers.phrases[ref] = phrase
                    matchers.lines.add(norm)
                    break

    return matchers


def _apply_furniture_strip(text: str, matchers: _FurnitureMatchers, doc_items) -> str:
    """Strip furniture from a body chunk's text using both ref-based and line-based methods."""
    # Phrase removal: strip every known furniture phrase from the text.
    # Docling sometimes assigns a furniture DocItem to a neighboring chunk's
    # doc_items, so we can't rely on the current chunk owning the ref —
    # iterate all known phrases instead.
    for phrase in matchers.phrases.values():
        if phrase:
            text = _strip_phrase(text, phrase)

    # Template-based strip: catches furniture fused into body items by OCR
    # (e.g. "…del Pág. 19" where no separate Pág. 19 DocItem exists on that page)
    for pat in matchers.templates:
        text = pat.sub("", text)

    # Line-level stripping: handles furniture on its own line
    if matchers.lines:
        lines = text.split("\n")
        text = "\n".join(l for l in lines if _normalize_line(l) not in matchers.lines)

    # Normalize residual whitespace
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


# Spanish legal-document structural keywords. When docling's layout pass fuses
# adjacent headings into a single section_header item (e.g. document title +
# first chapter), we re-split the text on these keywords.
LEGAL_HEADING_KEYWORDS = (
    "Libro",
    "Título",
    "Capítulo",
    "Sección",
    "Subsección",
    "Parte",
    "Anexo",
    "Disposición",
    "Artículo",
    "Exposición",
)
_HEADING_SPLIT_RE = re.compile(
    r"(?<=\S)\s+(?=(?:" + "|".join(LEGAL_HEADING_KEYWORDS) + r")\b)"
)


def _split_merged_heading(text: str) -> list[str]:
    return [p.strip() for p in _HEADING_SPLIT_RE.split(text) if p.strip()]


class DoclingChunker:
    """Loads and chunks a document using Docling's layout-aware parser.

    Output entries are dicts with keys ``text``, ``text_markdown``, ``metadata``.
    Body entries carry ``metadata.headings`` and ``metadata.dl_meta`` from the
    HierarchicalChunker. Heading-only entries (chapter titles with no body of
    their own) are emitted in reading order with ``metadata.is_heading_only``.
    """

    def __init__(self) -> None:
        self._converter = DocumentConverter()
        self._chunker = HierarchicalChunker()

    def chunk(self, file_path: str) -> list[dict]:
        conv_res = self._converter.convert(file_path)
        dl_doc = conv_res.document

        body_chunks = list(self._chunker.chunk(dl_doc))
        matchers = _detect_furniture(dl_doc)
        has_furniture = bool(matchers.lines or matchers.refs)

        # Map first doc_item self_ref -> chunk index, so reading-order traversal
        # can splice each body chunk in at the right position.
        chunk_by_first_ref: dict[str, int] = {}
        for i, ch in enumerate(body_chunks):
            if ch.meta.doc_items:
                first_ref = getattr(ch.meta.doc_items[0], "self_ref", None)
                if first_ref is not None:
                    chunk_by_first_ref[first_ref] = i
        emitted_chunks: set[int] = set()

        results: list[dict] = []
        for item, _tree_level in dl_doc.iterate_items():
            label = str(getattr(item, "label", "") or "")
            ref = getattr(item, "self_ref", None)

            if label == "section_header":
                text = (getattr(item, "text", "") or "").strip()
                if not text:
                    continue
                level = getattr(item, "level", 1) or 1
                for piece in _split_merged_heading(text):
                    if has_furniture and _normalize_line(piece) in matchers.lines:
                        continue
                    if has_furniture and ref in matchers.refs:
                        continue
                    results.append({
                        "text": _strip_inline_md(piece),
                        "text_markdown": ("#" * (level + 1)) + " " + piece,
                        "metadata": {
                            "is_heading_only": True,
                            "dl_meta": {"doc_items": [{"label": "section_header"}]},
                        },
                    })
                continue

            idx = chunk_by_first_ref.get(ref)
            if idx is None or idx in emitted_chunks:
                continue
            emitted_chunks.add(idx)
            ch = body_chunks[idx]
            raw_text = _strip_inline_md(ch.text)
            raw_md = ch.text
            if has_furniture:
                raw_text = _apply_furniture_strip(raw_text, matchers, ch.meta.doc_items)
                raw_md = _apply_furniture_strip(raw_md, matchers, ch.meta.doc_items)
            if not raw_text:
                continue
            results.append({
                "text": raw_text,
                "text_markdown": raw_md,
                "metadata": {
                    "dl_meta": ch.meta.export_json_dict(),
                    "headings": list(ch.meta.headings or []),
                    "is_heading_only": False,
                },
            })

        return results
