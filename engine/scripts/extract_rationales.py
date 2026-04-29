"""One-time script: extract reviewer rationales from POSIBLES RESULTADOS sections
in the raw eval docx files and write data/eval/rationales.json.

Output format:
{
  "domain": {
    "Artículo N. Title": "rationale text",
    ...
  }
}
"""
import json
import re
from pathlib import Path

import docx


def _extract(path: Path, domain: str) -> dict[str, str]:
    doc = docx.Document(path)
    paras = [p.text.strip() for p in doc.paragraphs]

    start = next(
        i for i, t in enumerate(paras) if "POSIBLES RESULTADOS" in t.upper()
    )

    articles: dict[str, str] = {}
    pending_title: str | None = None
    i = start + 1

    while i < len(paras):
        t = paras[i]
        if not t:
            i += 1
            continue

        # VIVIENDA format: "Artículo N. Title\n rationale" in a single paragraph
        if "\n" in t and re.match(r"Art[ií]culo \d+\.", t):
            parts = t.split("\n", 1)
            title = parts[0].strip()
            rationale = parts[1].strip()
            articles[title] = rationale
            i += 1
            continue

        # EDUCACION format: title alone, then rationale in the next paragraph
        if re.match(r"Art[ií]culo \d+\.", t):
            pending_title = t
            i += 1
            continue

        if pending_title is not None:
            rationale = re.sub(
                r"^Posibles resultados vinculados a este art[ií]culo:\s*",
                "",
                t,
            ).strip()
            articles[pending_title] = rationale
            pending_title = None
            i += 1
            continue

        i += 1

    return articles


def main() -> None:
    root = Path(__file__).parent.parent

    sources = {
        "educacion": root / "data/eval/raw/PILOTO2_ Proyecto de Ley e insumos_EDUCACION.docx",
        "vivienda": root / "data/eval/raw/PILOTO2_ Proyecto de Ley e insumos_VIVIENDA.docx",
    }

    result: dict[str, dict[str, str]] = {}
    for domain, path in sources.items():
        result[domain] = _extract(path, domain)
        print(f"{domain}: extracted {len(result[domain])} article rationales")

    out = root / "data/eval/rationales.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nWritten → {out}")


if __name__ == "__main__":
    main()
