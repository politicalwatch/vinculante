from typing import Protocol


class ChunkerProtocol(Protocol):
    """Port for splitting a document into text chunks."""

    def chunk(self, file_path: str) -> list[dict]: ...
