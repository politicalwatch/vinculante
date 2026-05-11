import re

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker

_INLINE_MD_RE = re.compile(r"[\*_]+")


def _strip_inline_md(s: str) -> str:
    return _INLINE_MD_RE.sub("", s)

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
            results.append({
                "text": _strip_inline_md(ch.text),
                "text_markdown": ch.text,
                "metadata": {
                    "dl_meta": ch.meta.export_json_dict(),
                    "headings": list(ch.meta.headings or []),
                    "is_heading_only": False,
                },
            })

        return results
