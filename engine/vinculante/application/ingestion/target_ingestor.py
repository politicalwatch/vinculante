import re
import unicodedata

from vinculante.application.ingestion.spanish_legal_classifier import ChunkClassification, classify
from vinculante.domain.entities import Section, TargetDocument
from vinculante.domain.ports.chunking import ChunkerProtocol
from vinculante.domain.ports.repositories import SectionRepositoryProtocol, TargetRepositoryProtocol

_MD_RE = re.compile(r"[\*_]+")

_LETTER_LIST_DETECT_RE = re.compile(r"(?:^|\s)a\)\s")
_LETTER_LIST_SPLIT_RE = re.compile(r"\s+(?=[a-z]\)\s)")
_LIST_BULLET_RE = re.compile(r"^-\s+", re.MULTILINE)
_LETTER_ITEM_RE = re.compile(r"^[a-z]\)\s")
_NUMBERED_ITEM_SPLIT_RE = re.compile(r"(?<=[.:])\s+(?=\d+\.\s+[A-ZÁÉÍÓÚÑ])")
_LEADING_NUM_RE = re.compile(r"^(\d+)\.\s")


def _strict_letter_seq(letters: list[str]) -> bool:
    if len(letters) < 2:
        return False
    return letters == [chr(ord("a") + i) for i in range(len(letters))]


def _strict_number_seq(nums: list[int]) -> bool:
    if len(nums) < 2:
        return False
    return all(nums[i] == nums[i - 1] + 1 for i in range(1, len(nums)))


def _split_numbered_items(text: str) -> str:
    """Split inline numbered items ('1. … 2. … 3. …') into separate paragraphs.
    Only fires when a digit-dot-space-Capital pattern follows '.' or ':',
    and only when the resulting numbers form a strictly consecutive sequence."""
    parts = [p.strip() for p in _NUMBERED_ITEM_SPLIT_RE.split(text) if p.strip()]
    if len(parts) < 2:
        return text
    nums = [int(m.group(1)) for p in parts if (m := _LEADING_NUM_RE.match(p))]
    if not _strict_number_seq(nums):
        return text
    return "\n\n".join(parts)


def _is_list_item(chunk: dict) -> bool:
    items = (chunk.get("metadata", {}).get("dl_meta") or {}).get("doc_items") or []
    return bool(items) and items[0].get("label") == "list_item"


def _looks_like_continuation(chunk: dict) -> bool:
    if chunk.get("metadata", {}).get("is_heading_only", False):
        return False
    text = (chunk.get("text") or "").lstrip()
    return bool(text) and text[0].islower()


def _reformat_letter_list(joined: str) -> str:
    """Split a run of Docling list_items that contains letter markers (a, b, c…)
    into separate bulleted items. Intro text before the first letter becomes a
    plain paragraph. Runs without an 'a)' marker, or where the letter sequence
    is non-strict (nested same-marker plain text), are returned unchanged."""
    if not _LETTER_LIST_DETECT_RE.search(joined):
        return joined
    cleaned = _LIST_BULLET_RE.sub("", joined)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    pieces = [p.strip() for p in _LETTER_LIST_SPLIT_RE.split(cleaned) if p.strip()]
    letters = [p[0] for p in pieces if _LETTER_ITEM_RE.match(p)]
    if not _strict_letter_seq(letters):
        return joined
    out: list[str] = []
    for piece in pieces:
        out.append(f"- {piece}" if _LETTER_ITEM_RE.match(piece) else piece)
    return "\n\n".join(out)


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold().strip()


def _norm_strip(text: str) -> str:
    return _normalize(_MD_RE.sub("", text))


def _page_number(chunk: dict) -> int | None:
    metadata = chunk.get("metadata", {})
    raw_meta = metadata.get("dl_meta", {})
    doc_items = raw_meta.get("doc_items", [])
    prov = doc_items[0].get("prov", []) if doc_items else []
    return prov[0].get("page_no") if prov else None


class TargetIngestor:
    def __init__(
        self,
        target_repo: TargetRepositoryProtocol,
        section_repo: SectionRepositoryProtocol,
        chunker: ChunkerProtocol,
    ) -> None:
        self.target_repo = target_repo
        self.section_repo = section_repo
        self.chunker = chunker

    def ingest(
        self,
        file_path: str,
        title: str,
        author: str,
        version: str | None = None,
    ) -> TargetDocument:
        target = TargetDocument(title=title, author=author, version=version)
        target = self.target_repo.save(target)

        title_norm = _norm_strip(title)
        chunks = self.chunker.chunk(file_path)
        classifications = classify(chunks)

        # Group chunks into logical sections. A section_start chunk opens a new
        # group; subsequent non-start chunks merge into the open group. Chunks
        # that arrive before any group is open (leading orphans — typically the
        # document title page) are dropped.
        groups: list[list[tuple[dict, ChunkClassification]]] = []
        current: list[tuple[dict, ChunkClassification]] | None = None
        for chunk, cl in zip(chunks, classifications, strict=True):
            if cl.skip:
                continue
            if cl.is_section_start:
                if current:
                    groups.append(current)
                current = [(chunk, cl)]
            elif current is not None:
                current.append((chunk, cl))
        if current:
            groups.append(current)

        sections: list[Section] = []
        for group in groups:
            opening_chunk, opening_cl = group[0]

            # Title dedup: drop if the opening chunk text matches the document
            # title (markdown stripped + normalized, equality or containment).
            opening_norm = _norm_strip(opening_chunk["text"])
            if opening_norm == title_norm:
                continue

            text_parts: list[str] = []
            md_parts: list[str] = []
            opening_seen = False
            i = 0
            while i < len(group):
                chunk, _ = group[i]
                if _is_list_item(chunk):
                    j = i + 1
                    while j < len(group) and (
                        _is_list_item(group[j][0]) or _looks_like_continuation(group[j][0])
                    ):
                        j += 1
                    run_text = "\n".join(group[k][0]["text"] for k in range(i, j))
                    run_md = "\n".join(
                        group[k][0].get("text_markdown") or group[k][0]["text"]
                        for k in range(i, j)
                    )
                    text_parts.append(_split_numbered_items(_reformat_letter_list(run_text)))
                    md_parts.append(_split_numbered_items(_reformat_letter_list(run_md)))
                    opening_seen = True
                    i = j
                    continue
                md = chunk.get("text_markdown") or chunk["text"]
                text_body = chunk["text"]
                md = _split_numbered_items(md)
                text_body = _split_numbered_items(text_body)
                is_heading_only = chunk.get("metadata", {}).get("is_heading_only", False)
                if (
                    is_heading_only
                    and opening_seen
                    and _LEADING_NUM_RE.match(text_body.lstrip())
                ):
                    # Docling's layout model sometimes labels a short colon-terminated
                    # numbered list item ("3. Foo:") as section_header. Inside an
                    # already-opened section, render it as a plain paragraph.
                    md = re.sub(r"^#+\s+", "", md.lstrip())
                elif (
                    not opening_seen
                    and not is_heading_only
                    and opening_cl.section_type != "unknown"
                    and not md.lstrip().startswith("#")
                ):
                    md = f"## {md}"
                opening_seen = True
                text_parts.append(text_body)
                md_parts.append(md)
                i += 1

            text = "\n\n".join(text_parts)
            text_markdown = "\n\n".join(md_parts)

            page_number = next(
                (pn for c, _ in group if (pn := _page_number(c)) is not None),
                None,
            )

            opening_meta = opening_chunk.get("metadata", {})
            raw_meta = opening_meta.get("dl_meta", {})

            sections.append(Section(
                text=text,
                text_markdown=text_markdown,
                clear_language=text,
                page_number=page_number,
                section_type=opening_cl.section_type,
                section_number=opening_cl.section_number,
                meta=raw_meta or None,
                is_matchable=opening_cl.is_matchable,
                target_id=target.id,
            ))
        self.section_repo.bulk_save(sections)
        return target
