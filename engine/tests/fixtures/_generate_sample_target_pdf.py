"""Regenerate tests/fixtures/sample_target.pdf.

Run inside the engine container:
    docker compose exec engine uv run python tests/fixtures/_generate_sample_target_pdf.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).parent / "sample_target.pdf"

styles = getSampleStyleSheet()

story = [
    Paragraph("Ley de ejemplo", styles["Title"]),
    Spacer(1, 12),
    Paragraph("Capítulo I — Disposiciones generales", styles["Heading1"]),
    Paragraph(
        "La presente ley tiene por objeto establecer un marco de ejemplo para la "
        "validación de procesos de ingesta y segmentación en pruebas automatizadas.",
        styles["BodyText"],
    ),
    Spacer(1, 6),
    Paragraph("Artículo 1. Objeto", styles["Heading2"]),
    Paragraph(
        "Este artículo describe el alcance del documento y sirve como párrafo "
        "representativo para el chunker.",
        styles["BodyText"],
    ),
    Spacer(1, 6),
    Paragraph("Artículo 2. Principios", styles["Heading2"]),
    Paragraph("Los principios rectores son los siguientes:", styles["BodyText"]),
    ListFlowable(
        [
            ListItem(Paragraph("Transparencia en los procesos.", styles["BodyText"])),
            ListItem(Paragraph("Participación ciudadana efectiva.", styles["BodyText"])),
            ListItem(Paragraph("Rendición de cuentas permanente.", styles["BodyText"])),
        ],
        bulletType="bullet",
    ),
    Spacer(1, 12),
    Paragraph("Capítulo II — Aplicación", styles["Heading1"]),
    Paragraph(
        "Las disposiciones del presente capítulo regulan la aplicación práctica "
        "de los principios enunciados previamente.",
        styles["BodyText"],
    ),
]

SimpleDocTemplate(str(OUT), pagesize=A4).build(story)
print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
