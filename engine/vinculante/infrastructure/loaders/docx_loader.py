import re
import unicodedata

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\.", "-", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def _is_header_row(row) -> bool:
    texts = [c.text.strip().lower() for c in row.cells]
    return any("titulo" in t or "título" in t or "desarrollo" in t for t in texts)


def _cell_text(cell) -> str:
    return "\n".join(p.text for p in cell.paragraphs if p.text.strip()).strip()


def _iter_block_items(doc):
    for child in doc.element.body:
        if child.tag == qn("w:p"):
            yield DocxParagraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield DocxTable(child, doc)


class DocxLoader:
    """Loads structured proposal data from a semi-structured .docx file.

    Heading 1 paragraphs are read as topic, Heading 2 as subtopic.
    Tables are parsed row-by-row (first row treated as header if it contains
    "título"/"desarrollo"). Two-column tables yield title + body; single-column
    tables yield body only.
    """

    def load(self, file_path: str) -> list[dict]:
        doc = Document(file_path)
        rows: list[dict] = []
        theme: str | None = None
        subtheme: str | None = None
        seen_refs: dict[str, int] = {}

        for block in _iter_block_items(doc):
            if isinstance(block, DocxParagraph):
                style = block.style.name if block.style else ""
                text = block.text.strip()
                if not text:
                    continue
                if "Heading 1" in style:
                    theme = text
                    subtheme = None
                elif "Heading 2" in style:
                    subtheme = text

            elif isinstance(block, DocxTable):
                table_rows = list(block.rows)
                if not table_rows:
                    continue
                data_rows = table_rows[1:] if _is_header_row(table_rows[0]) else table_rows
                ncols = len(block.columns)

                for row in data_rows:
                    cells = row.cells
                    if ncols >= 2:
                        title = _cell_text(cells[0])
                        body = _cell_text(cells[1])
                        if not title and not body:
                            continue
                        text = f"{title}\n\n{body}" if title and body else (title or body)
                        fallback = " ".join(body.split()[:8])
                        ref_seed = f"{subtheme or theme or ''} {title or fallback}"
                    else:
                        body = _cell_text(cells[0])
                        if not body:
                            continue
                        text = body
                        ref_seed = f"{subtheme or theme or ''} {' '.join(body.split()[:8])}"

                    ref_base = _slugify(ref_seed)
                    if ref_base in seen_refs:
                        seen_refs[ref_base] += 1
                        ref = f"{ref_base}-{seen_refs[ref_base]}"
                    else:
                        seen_refs[ref_base] = 0
                        ref = ref_base

                    rows.append({
                        "text": text,
                        "reference": ref,
                        "topic": theme,
                        "subtopic": subtheme,
                    })

        return rows
