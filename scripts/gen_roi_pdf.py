import sys
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = r"C:\Users\administradordatos\TRANSPORTES LA CAROLINA\Administracion Datos - Documentos\La Carolina De Transporte"
LOGO = r"C:\Users\administradordatos\TRANSPORTES LA CAROLINA\Administracion Datos - Documentos\La Carolina De Transporte\Projects\danos-busetas-conductores\src\img\logo.jpg"
OUT  = os.path.join(BASE, "Wiki", "informes", "ROI Proyectos IA 2026-05-26.pdf")

# ── Colores corporativos ────────────────────────────────────────────────────
C_GOLD   = colors.HexColor("#B8982A")
C_DARK   = colors.HexColor("#1A1A1A")
C_RED    = colors.HexColor("#C0392B")
C_GRAY   = colors.HexColor("#5D6D7E")
C_LGRAY  = colors.HexColor("#F4F4F4")
C_WHITE  = colors.white
C_ACCENT = colors.HexColor("#2C3E50")

W, H = A4  # 595 x 842 pt

# ── Estilos ─────────────────────────────────────────────────────────────────
def style(name, **kw):
    base = {
        "fontName": "Helvetica", "fontSize": 10,
        "leading": 14, "textColor": C_DARK,
        "spaceAfter": 4, "spaceBefore": 0,
    }
    base.update(kw)
    return ParagraphStyle(name, **base)

S_TITLE   = style("title",   fontName="Helvetica-Bold", fontSize=18, textColor=C_DARK,   leading=22, spaceAfter=2)
S_SUB     = style("sub",     fontName="Helvetica",       fontSize=11, textColor=C_GRAY,   leading=14, spaceAfter=8)
S_H2      = style("h2",      fontName="Helvetica-Bold", fontSize=12, textColor=C_GOLD,   leading=16, spaceBefore=14, spaceAfter=4)
S_H3      = style("h3",      fontName="Helvetica-Bold", fontSize=10, textColor=C_ACCENT, leading=13, spaceBefore=8,  spaceAfter=3)
S_BODY    = style("body",    fontSize=9,  leading=13, textColor=C_DARK, alignment=TA_JUSTIFY)
S_SMALL   = style("small",   fontSize=8,  leading=11, textColor=C_GRAY)
S_NOTE    = style("note",    fontSize=8,  leading=12, textColor=C_ACCENT, leftIndent=8)
S_BOLD    = style("bold",    fontName="Helvetica-Bold", fontSize=9, leading=13)
S_CENTER  = style("center",  fontSize=9,  leading=13, alignment=TA_CENTER)
S_FOOTER  = style("footer",  fontSize=7.5, textColor=C_GRAY, alignment=TA_CENTER)

def hr(color=C_GOLD, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=6)

def kpi_table(data):
    """4 KPI boxes in one row."""
    t = Table(data, colWidths=[(W - 4*cm) / len(data)])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_DARK),
        ("TEXTCOLOR",    (0,0), (-1,-1), C_WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0),  18),
        ("FONTNAME",     (0,1), (-1,1),  "Helvetica"),
        ("FONTSIZE",     (0,1), (-1,1),  8),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_DARK]),
        ("ROUNDEDCORNERS",[4]),
        ("TOPPADDING",   (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, C_GRAY),
        ("BOX",          (0,0), (-1,-1), 0, C_DARK),
    ]))
    return t

def proj_table(rows, col_widths=None):
    if col_widths is None:
        col_widths = [3.8*cm, (W - 4*cm - 3.8*cm)]
    t = Table(rows, colWidths=col_widths, repeatRows=0)
    style_cmds = [
        ("BACKGROUND",  (0,0), (-1,0),  C_ACCENT),
        ("TEXTCOLOR",   (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_LGRAY, C_WHITE]),
        ("ALIGN",       (0,0), (-1,-1), "LEFT"),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING",(0,0), (-1,-1), 7),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("FONTNAME",    (0,1), (0,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",   (0,1), (0,-1),  C_ACCENT),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

def main_table(rows, col_widths=None):
    if col_widths is None:
        col_widths = [5.5*cm, 3.5*cm, 4.5*cm, 2.5*cm]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  C_GOLD),
        ("TEXTCOLOR",    (0,0), (-1,0),  C_DARK),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_LGRAY, C_WHITE]),
        ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        ("ALIGN",        (0,0), (0,-1),  "LEFT"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("FONTNAME",     (0,-1),(-1,-1), "Helvetica-Bold"),
        ("BACKGROUND",   (0,-1),(-1,-1), C_DARK),
        ("TEXTCOLOR",    (0,-1),(-1,-1), C_WHITE),
    ]))
    return t

# ── Documento ────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2.2*cm, bottomMargin=2*cm,
    title="ROI Proyectos IA — La Carolina 2026",
    author="Administrador de Datos — La Carolina De Transporte"
)

story = []

# ── ENCABEZADO ───────────────────────────────────────────────────────────────
logo_img = Image(LOGO, width=3.2*cm, height=3.2*cm)
header_data = [[
    logo_img,
    [
        Paragraph("RETORNO SOBRE LA INVERSIÓN", S_TITLE),
        Paragraph("Proyectos de Inteligencia Artificial en Ejecución", S_SUB),
        Paragraph("La Carolina De Transporte · Mayo 2026 · Para Junta Directiva", S_SMALL),
    ]
]]
header_t = Table(header_data, colWidths=[3.8*cm, W - 4*cm - 3.8*cm])
header_t.setStyle(TableStyle([
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 0),
    ("RIGHTPADDING",(0,0), (-1,-1), 0),
    ("TOPPADDING",  (0,0), (-1,-1), 0),
    ("BOTTOMPADDING",(0,0),(-1,-1),0),
]))
story.append(header_t)
story.append(hr(C_GOLD, 2))

# ── KPIs ─────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.3*cm))
kpi_data = [
    ["$4.5M – $6M", "$114M – $202M", "3x – 5x", "2 – 4 meses"],
    ["Inversión mensual", "Beneficio anual est.", "ROI proyectado", "Recuperación"],
]
story.append(kpi_table(kpi_data))
story.append(Spacer(1, 0.4*cm))

# ── CONTEXTO ─────────────────────────────────────────────────────────────────
story.append(Paragraph("CONTEXTO", S_H2))
story.append(hr(C_LGRAY, 0.5))
story.append(Paragraph(
    "La Carolina tiene <b>5 proyectos de IA activos</b> desde enero 2026, ejecutados por el equipo interno "
    "(Administrador de Datos + Víctor Sandoval) con acompañamiento del consultor Harold Combita. "
    "La plataforma tecnológica es <b>Supabase + Vercel + Claude API</b>. "
    "Los beneficios están basados en datos reales: RRHH Ene–Jul 2025 y consumos de mantenimiento 2023–2026.",
    S_BODY))
story.append(Spacer(1, 0.3*cm))

# ── PROYECTOS ─────────────────────────────────────────────────────────────────
proyectos = [
    {
        "num": "01",
        "titulo": "Dashboard de Gestión de Conductores",
        "estado": "Desarrollo activo · Supabase + Vercel",
        "rows": [
            ["Problema", "Gestión manual de 148–155 conductores sin visibilidad unificada"],
            ["Inversión est.", "$800K COP/mes (herramientas + equipo)"],
            ["Beneficio", "Reducción de 8–10 hrs/semana de reportería manual en RRHH y Gerencia"],
            ["Valor estimado", "~$15M COP/año en tiempo liberado"],
            ["Indicador clave", "Tiempo de respuesta a ausentismo: de 24h a tiempo real"],
        ]
    },
    {
        "num": "02",
        "titulo": "Seguimiento Rotación de Conductores",
        "estado": "Desarrollo activo · Datos base: 154 retiros en 7 meses (2025)",
        "rows": [
            ["Problema", "22% de conductores se retiran en ≤ 30 días — 1 de cada 5 no llega al primer mes"],
            ["Cálculo", "Costo de un ciclo de contratación: ~$1.5M COP/conductor. En 2025 se contrataron 296. "
                        "Reducir 10% rotación temprana = 30 conductores menos/año"],
            ["Inversión est.", "Incluida en Dashboard (sin costo adicional)"],
            ["Valor estimado", "$45M – $75M COP/año"],
            ["Indicador clave", "Tasa rotación temprana: actualmente 22% → objetivo ≤ 15%"],
        ]
    },
    {
        "num": "03",
        "titulo": "Módulo Accidentalidad con Claude API",
        "estado": "En implementación · Supabase Edge Functions + Claude API",
        "rows": [
            ["Problema", "Análisis de accidentalidad manual, sin detección automática de patrones por conductor"],
            ["Referencia", "Un accidente con daños mayores: $8M – $25M COP (reparación + trámites + fuera de servicio)"],
            ["Inversión est.", "$1.2M COP/mes (incluye uso Claude API)"],
            ["Valor estimado", "Prevenir 2 accidentes mayores/año = $16M – $50M COP/año"],
            ["Indicador clave", "Reducción de siniestros reincidentes por conductor"],
        ]
    },
    {
        "num": "04",
        "titulo": "Agente IA Conversacional de Accidentalidad",
        "estado": "En implementación · Claude API + Edge Functions",
        "rows": [
            ["Problema", "Gerencia no puede consultar datos de accidentalidad sin depender del equipo técnico"],
            ["Beneficio", "Gerentes consultan en lenguaje natural: «¿cuántos accidentes tuvo el conductor X en 2026?»"],
            ["Inversión est.", "Incluida en Módulo Accidentalidad"],
            ["Valor estimado", "$8M – $12M COP/año en tiempo de gerencia liberado"],
            ["Indicador clave", "Tiempo de obtención de un reporte: de 2 días a minutos"],
        ]
    },
    {
        "num": "05",
        "titulo": "Registro de Daños de Busetas",
        "estado": "Piloto activo · Supabase + HTML/JS",
        "rows": [
            ["Problema", "Daños no reportados o tardíos generan reparaciones reactivas más costosas"],
            ["Base de datos", "Consumo repuestos 2025: $1.767M COP. Motor + Frenos + Llantas = 50% del total"],
            ["Inversión est.", "$600K COP/mes"],
            ["Valor estimado", "Reducir 5% del gasto correctivo evitable = $30M – $50M COP/año"],
            ["Indicador clave", "% OT reactivas vs. preventivas; daños recurrentes por vehículo"],
        ]
    },
]

for p in proyectos:
    rows_fmt = [[Paragraph(k, S_BOLD), Paragraph(v, S_BODY)] for k, v in p["rows"]]
    block = KeepTogether([
        Paragraph(f"<b>{p['num']}  {p['titulo']}</b>", S_H2),
        Paragraph(p["estado"], S_SMALL),
        Spacer(1, 0.15*cm),
        proj_table(rows_fmt, col_widths=[3.8*cm, W - 4*cm - 3.8*cm]),
        Spacer(1, 0.25*cm),
    ])
    story.append(block)

# ── TABLA CONSOLIDADA ─────────────────────────────────────────────────────────
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("RESUMEN CONSOLIDADO", S_H2))
story.append(hr(C_LGRAY, 0.5))

consol = [
    ["Proyecto", "Inversión/mes", "Beneficio anual est.", "ROI"],
    ["Dashboard + Rotación Conductores", "$800K", "$60M – $90M", "6x – 9x"],
    ["Módulo Accidentalidad + Agente IA", "$1.2M", "$24M – $62M", "2x – 4x"],
    ["Registro Daños Busetas",            "$600K", "$30M – $50M", "4x – 7x"],
    ["TOTAL",                             "~$2.6M/mes", "$114M – $202M", "~4x – 6x"],
]
story.append(main_table(consol))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "* Inversión = costos directos de herramientas (Supabase, Vercel, Claude API). No incluye costo de oportunidad del equipo interno.",
    S_SMALL))

# ── VALOR INTANGIBLE ──────────────────────────────────────────────────────────
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("VALOR ESTRATÉGICO NO CUANTIFICADO", S_H2))
story.append(hr(C_LGRAY, 0.5))
intangibles = [
    ["Trazabilidad", "Por primera vez La Carolina tiene registro digital de daños, accidentes y retiros en tiempo real."],
    ["Auditoría", "Datos disponibles para procesos legales, seguros y RUNT."],
    ["Escalabilidad", "La plataforma Supabase + Vercel crece sin costo proporcional."],
    ["Cultura de datos", "El equipo toma decisiones con datos, no con intuición."],
]
rows_fmt = [[Paragraph(k, S_BOLD), Paragraph(v, S_BODY)] for k, v in intangibles]
story.append(proj_table(rows_fmt, col_widths=[3.2*cm, W - 4*cm - 3.2*cm]))

# ── RECOMENDACION ─────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.35*cm))
story.append(Paragraph("RECOMENDACIÓN A JUNTA DIRECTIVA", S_H2))
story.append(hr(C_LGRAY, 0.5))
rec_box = Table(
    [[Paragraph(
        "Continuar la ejecución de los 5 proyectos. El retorno esperado de <b>$114M – $202M COP/año</b> "
        "frente a una inversión de <b>~$31M COP/año</b> representa un ROI positivo incluso en el escenario "
        "más conservador. El proyecto de mayor impacto inmediato es <b>Seguimiento de Rotación de Conductores</b>, "
        "dado que el costo de contratar un conductor que se retira en 30 días es completamente evitable "
        "con los datos ya disponibles.",
        S_BODY
    )]],
    colWidths=[W - 4*cm]
)
rec_box.setStyle(TableStyle([
    ("BACKGROUND",   (0,0), (-1,-1), colors.HexColor("#FFF9E6")),
    ("LEFTPADDING",  (0,0), (-1,-1), 12),
    ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ("TOPPADDING",   (0,0), (-1,-1), 10),
    ("BOTTOMPADDING",(0,0), (-1,-1), 10),
    ("BOX",          (0,0), (-1,-1), 1.5, C_GOLD),
]))
story.append(rec_box)

# ── FOOTER ────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.6*cm))
story.append(hr(C_GOLD, 1))
story.append(Paragraph(
    "Elaborado por: Administrador de Datos — La Carolina De Transporte  ·  "
    "Fuentes: Procesos de reclutamiento.xlsx (RRHH 2025) · Consumos repuestos 2023-2026 · Reporte Proyectos IA 2026-05-22",
    S_FOOTER))

# ── GENERAR ───────────────────────────────────────────────────────────────────
doc.build(story)
print(f"OK  {OUT}")
