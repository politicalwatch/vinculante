"""Spanish legal document section classifier.

Classifies Docling chunks from Spanish legislative documents by section type
and determines whether each section should participate in proposal matching.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ChunkClassification:
    section_type: str
    section_number: str | None
    is_matchable: bool
    skip: bool  # True = do not create a Section row (hard skip)
    is_section_start: bool  # True = this chunk opens a new logical section


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_SEPARATOR_RE = re.compile(r"^[-_=*\s]{3,}$")
_TOC_RE = re.compile(r"^[íi]ndice$", re.IGNORECASE)
_FELIPE_RE = re.compile(r"^(?:FELIPE|JUAN\s+CARLOS)\s+[IVX]+\b", re.IGNORECASE)
_PREAMBULO_RE = re.compile(r"^REY DE ESPA[ÑN]A\b", re.IGNORECASE)
_EXPOSICION_RE = re.compile(r"^EXPOSICI[ÓO]N DE MOTIVOS\b", re.IGNORECASE)
_TITULO_RE = re.compile(r"^T[ÍI]TULO\s+(PRELIMINAR|[IVX]+)\b", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"^CAP[ÍI]TULO\s+[IVX]+\b", re.IGNORECASE)
_SECCION_RE = re.compile(r"^SECCI[ÓO]N\s+[IVX0-9]+\b", re.IGNORECASE)
_ARTICULO_RE = re.compile(r"^Art[íi]culo\s+(\d+(?:\s*bis|\s*ter)?)\s*\.", re.IGNORECASE)

# Ordinal: word(s), roman numerals, or digits — permissive so it spans all
# Spanish legal ordinals (única, primera … vigesimotercera, I, II, 1, 2 …)
_ORDINAL = r"(?:[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+)?|[IVX]+|\d+)"
_DISP_RE = re.compile(
    r"^Disposici[óo]n\s+(adicional|transitoria|derogatoria|final)\s+(" + _ORDINAL + r")\b",
    re.IGNORECASE,
)

# Natural order of disposiciones: earlier types may appear as references inside later ones
_DISP_ORDER: dict[str, int] = {
    "disp_adicional": 1,
    "disp_transitoria": 2,
    "disp_derogatoria": 3,
    "disp_final": 4,
}

# section_types whose body content must NOT be embedded or matched
_NON_MATCHABLE = frozenset({
    "exposicion_motivos",
    "preambulo",
    "titulo",
    "capitulo",
    "seccion",
    "disp_transitoria",
    "disp_derogatoria",
    "disp_final",
})

# section_types that should produce no Section row at all
_HARD_SKIP = frozenset({"toc", "separator"})

# Removes markdown bold/italic markers so regexes work on Docling's formatted output
_MARKDOWN_RE = re.compile(r"[\*_]+")

# Types that propagate their classification to subsequent unknown body chunks.
# articulo and disp_adicional are included so their body paragraphs and list
# items merge into the same logical section (all still matchable).
_PROPAGATING_CONTEXTS = frozenset({
    "exposicion_motivos",
    "preambulo",
    "articulo",
    "disp_adicional",
    "disp_transitoria",
    "disp_derogatoria",
    "disp_final",
})

# Types that reset the context (structural containers with no body of their own)
_CONTEXT_RESET = frozenset({
    "titulo",
    "capitulo",
    "seccion",
    "toc",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_text(text: str) -> tuple[str, str | None]:
    """Return (section_type, section_number) for a heading or marker text."""
    raw = text.strip()
    if _SEPARATOR_RE.fullmatch(raw):
        return "separator", None
    t = _MARKDOWN_RE.sub("", raw).strip()

    if _TOC_RE.match(t):
        return "toc", None
    if _FELIPE_RE.match(t):
        return "preambulo", None
    if _PREAMBULO_RE.match(t):
        return "preambulo", None
    if _EXPOSICION_RE.match(t):
        return "exposicion_motivos", None
    m = _TITULO_RE.match(t)
    if m:
        return "titulo", m.group(1).strip()
    if _CAPITULO_RE.match(t):
        return "capitulo", None
    if _SECCION_RE.match(t):
        return "seccion", None
    m = _ARTICULO_RE.match(t)
    if m:
        return "articulo", m.group(1).strip()
    m = _DISP_RE.match(t)
    if m:
        kind = m.group(1).lower()
        ordinal = m.group(2).lower()
        return f"disp_{kind}", f"{kind} {ordinal}"

    return "unknown", None


def _classify_by_headings(headings: list[str]) -> tuple[str, str | None]:
    """Classify a body chunk using its Docling heading context.

    Scans from innermost (last) heading outward. Structural containers
    (titulo/capitulo/seccion) are treated as fail-open so their body content
    stays matchable — those headings have no body themselves, only articles do.
    """
    for h in reversed(headings):
        stype, snum = _classify_text(h)
        if stype == "unknown":
            continue
        if stype in ("titulo", "capitulo", "seccion"):
            return "unknown", None
        return stype, snum

    return "unknown", None


def _first_doc_item_label(metadata: dict) -> str | None:
    """Return Docling's label for the first doc_item in a chunk's metadata."""
    items = (metadata.get("dl_meta") or {}).get("doc_items") or []
    return items[0].get("label") if items else None


class _RegionTracker:
    """One-pass state for resolving region-dependent ambiguities."""

    __slots__ = ("in_toc", "in_disposiciones", "current_context_type", "current_context_number")

    def __init__(self) -> None:
        self.in_toc = False
        self.in_disposiciones = False
        # Sticky context: when set, unknown body chunks inherit this classification
        # so content that Docling couldn't attribute to a heading still gets the
        # correct type and matchability (article body, disp_final body, etc.).
        self.current_context_type: str | None = None
        self.current_context_number: str | None = None

    def update(self, section_type: str, section_number: str | None) -> None:
        if section_type == "toc":
            self.in_toc = True
        elif section_type != "unknown":
            self.in_toc = False

        if section_type.startswith("disp_"):
            self.in_disposiciones = True

        if section_type in _PROPAGATING_CONTEXTS:
            self.current_context_type = section_type
            self.current_context_number = section_number
        elif section_type in _CONTEXT_RESET:
            self.current_context_type = None
            self.current_context_number = None
        # "unknown" leaves current_context unchanged


# ---------------------------------------------------------------------------
# Disposition-context absorption
# ---------------------------------------------------------------------------

def _absorb_into_disp_context(
    stype: str, snum: str | None, tracker: _RegionTracker
) -> tuple[str, str | None]:
    """Reclassify chunks that appear as references inside an outer disp_* context.

    Two cases:
      - articulo inside any disp_* → inherit parent disp.
      - disp_X inside disp_Y where order(X) < order(Y) → inherit parent disp.
    Returns (unknown, None) when there is no usable parent disp context.
    """
    ctx_type = tracker.current_context_type
    ctx_num = tracker.current_context_number
    parent_is_disp = bool(ctx_type and ctx_type.startswith("disp_"))

    is_articulo_in_disp = stype == "articulo" and tracker.in_disposiciones
    is_earlier_disp = (
        stype.startswith("disp_")
        and parent_is_disp
        and _DISP_ORDER.get(stype, 0) < _DISP_ORDER.get(ctx_type, 0)
    )

    if not (is_articulo_in_disp or is_earlier_disp):
        return stype, snum
    if parent_is_disp:
        return ctx_type, ctx_num
    return "unknown", None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(chunks: list[dict]) -> list[ChunkClassification]:
    """Classify Docling chunks from a Spanish legal document.

    Returns one ChunkClassification per input chunk, in the same order.
    Each classification includes an ``is_section_start`` flag indicating
    whether this chunk opens a new logical section (used by the ingestor
    to group body chunks into a single Section row).
    """
    tracker = _RegionTracker()
    result: list[ChunkClassification] = []

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        is_heading_only = bool(metadata.get("is_heading_only"))
        headings: list[str] = list(metadata.get("headings") or [])
        text: str = (chunk.get("text") or "").strip()
        first_label = _first_doc_item_label(metadata)

        if is_heading_only:
            stype, snum = _classify_text(text)
            stype, snum = _absorb_into_disp_context(stype, snum, tracker)
            # Inherited-context chunks (same type+number as parent) must not open a
            # new group even though they are heading-only chunks.
            is_section_start = stype != "unknown" and not (
                stype == tracker.current_context_type
                and snum == tracker.current_context_number
            )

        else:
            # TOC entries are emitted by Docling as list_item chunks
            if tracker.in_toc and first_label == "list_item":
                stype, snum = "toc", None
                is_section_start = False

            else:
                # 1. Direct text match
                stype, snum = _classify_text(text)
                if stype != "unknown":
                    stype, snum = _absorb_into_disp_context(stype, snum, tracker)
                    # Only a new boundary if type/number differs from current context
                    is_section_start = (
                        stype != tracker.current_context_type
                        or snum != tracker.current_context_number
                    )

                else:
                    # 2. Propagation: inherit current context if set (preferred over
                    # potentially-stale heading metadata from docling)
                    if tracker.current_context_type is not None:
                        stype = tracker.current_context_type
                        snum = tracker.current_context_number
                        is_section_start = False

                    else:
                        # 3. Heading-context match (only when no current context —
                        # typically right after titulo/capitulo/seccion reset)
                        stype, snum = _classify_by_headings(headings)
                        if stype != "unknown":
                            stype, snum = _absorb_into_disp_context(stype, snum, tracker)
                            is_section_start = (
                                stype != tracker.current_context_type
                                or snum != tracker.current_context_number
                            )

                        else:
                            # 4. Unknown — no context
                            stype, snum = "unknown", None
                            is_section_start = False

        tracker.update(stype, snum)

        skip = stype in _HARD_SKIP
        is_matchable = not skip and stype not in _NON_MATCHABLE

        result.append(ChunkClassification(
            section_type=stype,
            section_number=snum,
            is_matchable=is_matchable,
            skip=skip,
            is_section_start=is_section_start,
        ))

    return result
