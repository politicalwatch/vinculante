import csv


class CsvLoader:
    """Loads structured data from a CSV file."""

    def load(self, file_path: str) -> list[dict]:
        with open(file_path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
