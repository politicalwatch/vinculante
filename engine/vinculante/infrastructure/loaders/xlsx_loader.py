import pandas as pd


class XlsxLoader:
    """Loads structured data from an Excel file."""

    def load(self, file_path: str) -> list[dict]:
        df = pd.read_excel(file_path)
        return df.to_dict(orient="records")
