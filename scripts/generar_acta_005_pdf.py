from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Acta 005 Comite Beneficios Incentivos Junio 2026.pdf"


def money(value: int) -> str:
    return f"${value:,.0f}".replace(",", ".")


def build_pdf() -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=12,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Result",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0F766E"),
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Acta 005 Comite Beneficios Incentivos Junio 2026",
        author="Metropolitana de Transporte La Carolina",
    )

    story = []
    story.append(Paragraph("METROPOLITANA DE TRANSPORTE LA CAROLINA", styles["Small"]))
    story.append(Paragraph("Acta 005 - Comite de Beneficios e Incentivos", styles["TitleCenter"]))
    story.append(Paragraph("Incentivos Conductores - Recaudo Junio 2026", styles["TitleCenter"]))

    meta = Table(
        [
            ["Fecha", "2026-05-22", "Estado", "Final"],
            ["Tema", "Incentivos conductores", "Periodo", "Junio 2026"],
        ],
        colWidths=[1.0 * inch, 2.4 * inch, 1.0 * inch, 2.4 * inch],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Objetivo", styles["Section"]))
    story.append(
        Paragraph(
            "Definir el valor de recaudo proyectado para cubrir el incentivo de conductores correspondiente "
            "al mes de junio de 2026, tomando como base el numero de vehiculos activos y el valor diario por vehiculo.",
            styles["Small"],
        )
    )

    story.append(Paragraph("Base de calculo", styles["Section"]))
    base = Table(
        [
            ["Concepto", "Valor"],
            ["Valor diario por vehiculo", money(2177)],
            ["Vehiculos base", "147"],
            ["Dias de junio", "30"],
        ],
        colWidths=[4.2 * inch, 2.0 * inch],
    )
    base.setStyle(table_style())
    story.append(base)

    story.append(Paragraph("Calculos", styles["Section"]))
    calc = Table(
        [
            ["Operacion", "Resultado"],
            [f"{money(2177)} x 147 vehiculos", f"{money(2177 * 147)} por dia"],
            [f"{money(2177 * 147)} por dia x 30 dias", money(2177 * 147 * 30)],
            [f"{money(2177)} x 7 dias", f"{money(2177 * 7)} por vehiculo semanal"],
            [f"{money(2177)} x 30 dias", f"{money(2177 * 30)} por vehiculo en junio"],
        ],
        colWidths=[3.4 * inch, 2.8 * inch],
    )
    calc.setStyle(table_style())
    story.append(calc)

    story.append(Spacer(1, 8))
    result = Table([[Paragraph("TOTAL PROYECTADO A RECAUDAR", styles["Small"])], [Paragraph(money(2177 * 147 * 30), styles["Result"])]], colWidths=[6.2 * inch])
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#0F766E")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(result)

    story.append(Paragraph("Vehiculos nuevos considerados", styles["Section"]))
    story.append(
        Paragraph(
            "Para el conteo de flota se revisaron los vehiculos nuevos con numero interno iniciado en 1.",
            styles["Small"],
        )
    )
    vehicles = [
        ["Vehiculo", "Placa", "Marca"],
        ["1025", "LJO715", "CHEVROLET"],
        ["1024", "LJO714", "CHEVROLET"],
        ["1055", "LJO698", "YUTONG"],
        ["1056", "LJO699", "YUTONG"],
        ["1057", "LJO700", "YUTONG"],
        ["1022", "LJO712", "CHEVROLET"],
        ["1026", "LJO716", "CHEVROLET"],
        ["1027", "LJO844", "CHEVROLET"],
        ["1034", "LJO845", "CHEVROLET"],
    ]
    vehicle_table = Table(vehicles, colWidths=[1.7 * inch, 2.0 * inch, 2.5 * inch])
    vehicle_table.setStyle(table_style())
    story.append(vehicle_table)

    story.append(Paragraph("Acuerdo", styles["Section"]))
    story.append(
        Paragraph(
            f"Se establece como base de recaudo para junio de 2026 el valor de {money(2177)} diarios "
            f"por vehiculo, aplicado sobre 147 vehiculos durante 30 dias, para un total de "
            f"{money(2177 * 147 * 30)}.",
            styles["Small"],
        )
    )

    story.append(Spacer(1, 18))
    story.append(
        KeepTogether(
            [
                Paragraph("Firmas", styles["Section"]),
                signature_table(),
            ]
        )
    )

    doc.build(story)


def table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )


def signature_table() -> Table:
    table = Table(
        [
            ["Nombre", "Firma"],
            ["", ""],
            ["", ""],
            ["", ""],
        ],
        colWidths=[3.1 * inch, 3.1 * inch],
        rowHeights=[0.25 * inch, 0.45 * inch, 0.45 * inch, 0.45 * inch],
    )
    table.setStyle(table_style())
    return table


if __name__ == "__main__":
    build_pdf()
    print(OUT)
