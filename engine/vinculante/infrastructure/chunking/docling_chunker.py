from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker


class DoclingChunker:
    """Loads and chunks a document using Docling's layout-aware parser."""

    def __init__(self) -> None:
        self._converter = DocumentConverter()
        self._chunker = HierarchicalChunker()

    def chunk(self, file_path: str) -> list[dict]:
        conv_res = self._converter.convert(file_path)
        dl_doc = conv_res.document
        results = []
        for chunk in self._chunker.chunk(dl_doc):
            text = self._chunker.contextualize(chunk)
            text_markdown = self._to_markdown(chunk)
            results.append({
                "text": text,
                "text_markdown": text_markdown,
                "metadata": {
                    "dl_meta": chunk.meta.export_json_dict(),
                },
            })
        return results

    def _to_markdown(self, chunk) -> str:
        parts = []
        for i, heading in enumerate(chunk.meta.headings or []):
            level = "#" * (i + 2)
            parts.append(f"{level} {heading}")
        if parts:
            parts.append("")
        parts.append(chunk.text)
        return "\n\n".join(parts)
