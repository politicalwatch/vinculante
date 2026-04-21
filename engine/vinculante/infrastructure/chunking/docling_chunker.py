from docling_core.transforms.chunker import HierarchicalChunker
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType


class DoclingChunker:
    """Loads and chunks a document using Docling's layout-aware parser."""

    def __init__(self, export_type: ExportType = ExportType.DOC_CHUNKS) -> None:
        self.export_type = export_type
        self._chunker = HierarchicalChunker()

    def chunk(self, file_path: str) -> list[dict]:
        loader = DoclingLoader(
            file_path=file_path,
            export_type=self.export_type,
            chunker=self._chunker,
        )
        docs = loader.load()
        return [
            {
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in docs
        ]
