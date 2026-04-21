import pandas as pd


class DocxLoader:
    """Loads structured proposal data from a .docx file via pandas."""

    def load(self, file_path: str) -> list[dict]:
        df = pd.read_excel(file_path) if file_path.endswith((".xlsx", ".xls")) else self._read_docx(file_path)
        return df.to_dict(orient="records")

    def _read_docx(self, file_path: str) -> pd.DataFrame:
        from docx import Document
        doc = Document(file_path)
        rows = [para.text for para in doc.paragraphs if para.text.strip()]
        return pd.DataFrame({"text": rows})
