from typing import Protocol


class FileLoaderProtocol(Protocol):
    """Port for loading structured data from files (docx, xlsx)."""

    def load(self, file_path: str) -> list[dict]: ...
