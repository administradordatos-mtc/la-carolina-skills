#!/usr/bin/env python3
"""
bi_clean.py — Limpieza y análisis de datasets BI La Carolina De Transporte
===========================================================================
Lee un archivo Excel (.xlsx / .xls) o CSV, realiza limpieza automática,
detecta encabezados corporativos, enmascara PII y genera:
  · Reporte JSON  → <salida>.json
  · Preview MD    → <salida>_preview.md  (primeras 10 filas en tabla Markdown)

Uso:
  python bi_clean.py <archivo>                   # detección automática
  python bi_clean.py <archivo> --sheet Hoja1     # hoja específica (Excel)
  python bi_clean.py <archivo> --start-row 5     # forzar inicio de datos
  python bi_clean.py <archivo> --out-dir C:\\tmp  # carpeta de salida
  python bi_clean.py <archivo> --no-pii          # NO enmascarar PII (solo métricas)
  python bi_clean.py <archivo> --preview 20      # N filas en preview
  python bi_clean.py <archivo> --quiet           # sin output a consola

Integración con bi-ingest:
  El script devuelve exit code 0 (ok) o 1 (error).
  El JSON de salida tiene la estructura que bi-ingest espera para
  generar páginas wiki directamente.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

# Forzar UTF-8 en stdout/stderr para Windows (evita error en emojis con cp1252)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Patrones de encabezados corporativos a saltar (fila no es header real)
CORPORATE_HEADER_PATTERNS = [
    r"METROPOLITANA\s+DE\s+TRANSPORTE",
    r"LA\s+CAROLINA",
    r"MOLINA\s+NESTOR",
    r"F\.?\s*Impreso",
    r"NIT\s*:\s*\d",
    r"^\s*$",                          # fila vacía
]

# Columnas PII a enmascarar en el preview
PII_COLUMNS = {
    "IDENTIFICACION", "CC", "CEDULA", "CED", "CED.", "NIT_CONDUCTOR",
    "DOC", "DOCUMENTO", "NUM_DOC_CONDUCTOR", "NIT_EMPLEADO",
    "ID_CONDUCTOR", "IDENTIFICACION_CONDUCTOR",
}

# Columnas de fecha candidatas
DATE_HINTS = ["FECHA", "DATE", "PERIODO", "PERIODO", "MES", "ANO", "AÑO",
              "YEAR", "MONTH", "FEC", "FECHA_DOC", "FECHA_MOV"]

# Columnas de valor monetario candidatas
VALUE_HINTS = ["TOTAL", "SUBTOTAL", "VALOR", "MONTO", "COSTO", "PRECIO",
               "IMPORTE", "NETO", "BRUTO", "IVA", "RECAUDO", "LIQUIDADO",
               "PRE_COS", "TOT_IVA", "TOT_DES", "STOTAL", "PRE_VEN"]

# Columnas de cantidad
QTY_HINTS = ["CANTIDAD", "CANT", "QTY", "COUNT", "VIAJES", "TIMBRADAS",
             "TIM_R", "REGISTROS"]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def is_corporate_header(row: pd.Series) -> bool:
    """Devuelve True si alguna celda de la fila parece encabezado corporativo."""
    for val in row.dropna().astype(str):
        for pat in CORPORATE_HEADER_PATTERNS:
            if re.search(pat, val, re.IGNORECASE):
                return True
    return False


def detect_start_row(path: Path, sheet: str | int | None = None) -> int:
    """
    Detecta la fila real de encabezados en un XLSX.
    Prueba StartRow 1-10, devuelve el primero que no sea corporativo.
    """
    for sr in range(0, 10):
        try:
            kw: dict[str, Any] = {"header": sr, "nrows": 3}
            if sheet is not None:
                kw["sheet_name"] = sheet
            df = pd.read_excel(path, engine="openpyxl", **kw)
            if df.empty:
                continue
            first_row = df.columns.tolist()
            # Columnas con nombres tipo "Unnamed: X" son señal de que aún no
            # llegamos al encabezado real
            unnamed = sum(1 for c in first_row if str(c).startswith("Unnamed"))
            if unnamed / max(len(first_row), 1) > 0.5:
                continue
            # Verificar si la fila de datos debajo del header es corporativa
            sample_series = pd.Series(first_row)
            if is_corporate_header(sample_series):
                continue
            return sr
        except Exception:
            continue
    return 0   # fallback


def detect_csv_encoding(path: Path) -> str:
    """Detecta encoding de un CSV usando chardet."""
    try:
        import chardet
        raw = path.read_bytes()[:50_000]
        result = chardet.detect(raw)
        enc = result.get("encoding") or "utf-8"
        # Normalizar aliases
        if enc.lower() in ("ascii", "windows-1252"):
            enc = "cp1252"
        return enc
    except ImportError:
        return "utf-8"


def detect_csv_separator(path: Path, encoding: str) -> str:
    """Detecta separador del CSV (';' o ',')."""
    try:
        sample = path.read_text(encoding=encoding, errors="replace")[:2000]
        semicolons = sample.count(";")
        commas = sample.count(",")
        return ";" if semicolons >= commas else ","
    except Exception:
        return ";"


def mask_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza valores en columnas PII con '[CC]'."""
    df = df.copy()
    for col in df.columns:
        if col.upper().strip() in PII_COLUMNS:
            df[col] = "[CC]"
    return df


def safe_copy_from_cloud(src: Path) -> Path:
    """
    Si el archivo es cloud-only (OneDrive RecallOnDataAccess),
    lo copia a $TEMP antes de abrirlo.
    En Linux/Mac simplemente devuelve la ruta original.
    """
    if sys.platform != "win32":
        return src
    try:
        attrs = src.stat().st_file_attributes   # type: ignore[attr-defined]
        RECALL_ON_DATA_ACCESS = 0x400000        # 4194304
        if attrs & RECALL_ON_DATA_ACCESS:
            tmp = Path(tempfile.gettempdir()) / f"bi_{src.name}"
            shutil.copy2(src, tmp)
            return tmp
    except AttributeError:
        pass
    # Siempre copiar en Windows para evitar locks de OneDrive
    tmp = Path(tempfile.gettempdir()) / f"bi_{src.name}"
    try:
        shutil.copy2(src, tmp)
        return tmp
    except Exception:
        return src


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

def read_excel(path: Path, sheet: str | int | None, start_row: int | None) -> tuple[pd.DataFrame, str, int, list[str]]:
    """Lee un Excel. Devuelve (df, sheet_name, start_row_used, all_sheets)."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    all_sheets: list[str] = wb.sheetnames
    wb.close()

    target_sheet = sheet if sheet is not None else all_sheets[0]
    sr = start_row if start_row is not None else detect_start_row(path, target_sheet)

    df = pd.read_excel(
        path,
        sheet_name=target_sheet,
        header=sr,
        engine="openpyxl",
        dtype=str,           # leer todo como string para no perder nada
    )
    # Eliminar columnas y filas totalmente vacías
    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df, str(target_sheet), sr, all_sheets


def read_csv(path: Path, encoding: str | None, sep: str | None) -> tuple[pd.DataFrame, str, str]:
    """Lee un CSV. Devuelve (df, encoding_used, sep_used)."""
    enc = encoding or detect_csv_encoding(path)
    separator = sep or detect_csv_separator(path, enc)
    df = pd.read_csv(
        path,
        sep=separator,
        encoding=enc,
        dtype=str,
        on_bad_lines="warn",
        low_memory=False,
    )
    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df, enc, separator


# ---------------------------------------------------------------------------
# Análisis estadístico
# ---------------------------------------------------------------------------

def analyse(df: pd.DataFrame) -> dict[str, Any]:
    """Genera estadísticas completas del DataFrame."""
    stats: dict[str, Any] = {}
    stats["rows"] = len(df)
    stats["cols"] = len(df.columns)
    stats["columns"] = list(df.columns)

    # Nulos
    null_pct = (df.isnull().mean() * 100).round(1).to_dict()
    stats["null_pct"] = null_pct

    # Detección de fechas
    date_cols: list[str] = []
    date_range: dict[str, str] = {}
    for col in df.columns:
        if any(h in col.upper() for h in DATE_HINTS):
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            if parsed.notna().sum() > len(df) * 0.3:
                date_cols.append(col)
                mn = parsed.min()
                mx = parsed.max()
                if pd.notna(mn) and pd.notna(mx):
                    date_range[col] = {
                        "min": mn.strftime("%Y-%m-%d"),
                        "max": mx.strftime("%Y-%m-%d"),
                    }  # type: ignore[assignment]
    stats["date_columns"] = date_cols
    stats["date_range"] = date_range

    # Columnas numéricas — totales
    numeric_totals: dict[str, Any] = {}
    for col in df.columns:
        is_value = any(h in col.upper() for h in VALUE_HINTS + QTY_HINTS)
        if is_value:
            series = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".", regex=False).str.replace(" ", "", regex=False),
                errors="coerce",
            )
            if series.notna().sum() > len(df) * 0.2:
                numeric_totals[col] = {
                    "sum":   round(float(series.sum()), 2),
                    "mean":  round(float(series.mean()), 2),
                    "min":   round(float(series.min()), 2),
                    "max":   round(float(series.max()), 2),
                    "count": int(series.notna().sum()),
                }
    stats["numeric_totals"] = numeric_totals

    # Top 10 por columnas categóricas relevantes
    cat_cols_hints = [
        "CONDUCTOR", "VEHICULO", "PLACA", "COD_COS", "PROVEEDOR",
        "NOM_TER", "ARTICULO", "NOMBRE", "REF_COD", "NOM_REF",
        "RUTA", "NOVEDAD", "CAUSA", "MOTIVO", "TIPO", "NOM_GRU",
        "COD_GRU", "ESTADO", "ORIGEN", "DESTINO",
    ]
    top_n: dict[str, list[dict]] = {}
    for col in df.columns:
        col_up = col.upper()
        if any(h in col_up for h in cat_cols_hints):
            counts = df[col].dropna().value_counts().head(10)
            if len(counts) > 0:
                top_n[col] = [
                    {"value": str(k), "count": int(v)}
                    for k, v in counts.items()
                ]
    stats["top_n"] = top_n

    # Valores únicos en columnas categóricas simples (< 30 únicos)
    unique_vals: dict[str, list[str]] = {}
    for col in df.columns:
        nuniq = df[col].nunique()
        if 2 <= nuniq <= 30:
            unique_vals[col] = sorted(df[col].dropna().unique().tolist())
    stats["unique_values"] = unique_vals

    # Duplicados
    dup_count = int(df.duplicated().sum())
    stats["duplicates"] = dup_count

    return stats


# ---------------------------------------------------------------------------
# Limpieza
# ---------------------------------------------------------------------------

def clean(df: pd.DataFrame, mask_pii_flag: bool) -> tuple[pd.DataFrame, list[str]]:
    """
    Limpia el DataFrame:
      · Normaliza nombres de columnas (strip, upper)
      · Elimina duplicados exactos
      · Enmascara PII si se solicita
    Devuelve (df_limpio, lista_de_cambios).
    """
    changes: list[str] = []

    # Normalizar nombres
    original_cols = list(df.columns)
    df.columns = [str(c).strip().upper() for c in df.columns]
    renamed = [(o, n) for o, n in zip(original_cols, df.columns) if str(o).strip().upper() != n]
    if renamed:
        changes.append(f"Columnas renormalizadas: {len(renamed)}")

    # Quitar filas completamente vacías
    before = len(df)
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)
    if len(df) < before:
        changes.append(f"Filas vacías eliminadas: {before - len(df)}")

    # Quitar duplicados exactos
    before = len(df)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    if len(df) < before:
        changes.append(f"Duplicados eliminados: {before - len(df)}")

    # Enmascarar PII
    if mask_pii_flag:
        pii_found = [c for c in df.columns if c.upper().strip() in PII_COLUMNS]
        if pii_found:
            df = mask_pii(df)
            changes.append(f"Columnas PII enmascaradas: {pii_found}")

    return df, changes


# ---------------------------------------------------------------------------
# Generación de outputs
# ---------------------------------------------------------------------------

def df_to_markdown(df: pd.DataFrame, n: int = 10) -> str:
    """Convierte las primeras N filas a tabla Markdown."""
    sample = df.head(n)
    try:
        return sample.to_markdown(index=False)
    except ImportError:
        # tabulate no disponible — construir manualmente
        cols = list(sample.columns)
        lines = ["| " + " | ".join(cols) + " |"]
        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in sample.iterrows():
            lines.append("| " + " | ".join(str(v) for v in row) + " |")
        return "\n".join(lines)


def build_report(
    file_path: Path,
    df_clean: pd.DataFrame,
    stats: dict,
    changes: list[str],
    meta: dict,
) -> dict:
    """Construye el JSON de reporte completo."""
    return {
        "bi_clean_version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "source": {
            "path": str(file_path),
            "name": file_path.name,
            "size_bytes": file_path.stat().st_size,
            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "extension": file_path.suffix.lower(),
            **meta,
        },
        "cleaning": {
            "rows_original": stats["rows"] + sum(
                int(c.split(": ")[1]) for c in changes
                if "eliminad" in c and c[0].isalpha()
            ) if changes else stats["rows"],
            "rows_clean": stats["rows"],
            "cols": stats["cols"],
            "changes": changes,
        },
        "statistics": stats,
        "wiki_ready": {
            "key_insight": _build_key_insight(stats, file_path.name),
            "column_table": _build_column_table(df_clean),
        },
    }


def _build_key_insight(stats: dict, filename: str) -> str:
    """Genera la línea de key_insight para Obsidian callout."""
    rows = stats["rows"]
    cols = stats["cols"]
    parts = [f"{rows:,} registros · {cols} columnas"]

    # Rango de fechas
    for col, rng in (stats.get("date_range") or {}).items():
        parts.append(f"Período: {rng['min']} → {rng['max']}")
        break

    # Total monetario principal
    for col, nums in (stats.get("numeric_totals") or {}).items():
        if any(h in col.upper() for h in ["TOTAL", "BRUTO", "RECAUDO", "MONTO"]):
            total = nums["sum"]
            if total > 1_000_000:
                parts.append(f"Total {col}: ${total:,.0f}")
            break

    return " · ".join(parts)


def _build_column_table(df: pd.DataFrame) -> str:
    """Genera tabla Markdown de columnas con tipo inferido."""
    lines = ["| Columna | Tipo | Ejemplo |",
             "|---------|------|---------|"]
    for col in df.columns:
        sample = df[col].dropna().head(1)
        example = str(sample.iloc[0])[:40] if len(sample) > 0 else "—"
        # Inferir tipo
        if col.upper() in PII_COLUMNS:
            tipo = "PII 🔒"
            example = "[CC]"
        elif any(h in col.upper() for h in DATE_HINTS):
            tipo = "Fecha"
        elif any(h in col.upper() for h in VALUE_HINTS):
            tipo = "Monetario"
        elif any(h in col.upper() for h in QTY_HINTS):
            tipo = "Cantidad"
        else:
            tipo = "Texto"
        lines.append(f"| `{col}` | {tipo} | {example} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="bi_clean — Limpieza y análisis de datasets BI La Carolina",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file", help="Ruta al archivo .xlsx/.xls/.csv")
    parser.add_argument("--sheet", default=None,
                        help="Nombre o índice de la hoja (Excel). Por defecto: primera hoja.")
    parser.add_argument("--start-row", type=int, default=None,
                        help="Fila de encabezados (0-indexed). Por defecto: autodetección.")
    parser.add_argument("--out-dir", default=None,
                        help="Carpeta de salida para JSON y MD. Por defecto: misma carpeta del archivo.")
    parser.add_argument("--no-pii", action="store_true",
                        help="No enmascarar columnas PII en el preview.")
    parser.add_argument("--preview", type=int, default=10,
                        help="Número de filas en el preview Markdown (default 10).")
    parser.add_argument("--quiet", action="store_true",
                        help="No imprimir resumen en consola.")
    parser.add_argument("--encoding", default=None, help="Encoding del CSV (ej: utf-8, cp1252).")
    parser.add_argument("--sep", default=None, help="Separador del CSV (ej: ; o ,).")

    args = parser.parse_args()

    src = Path(args.file)
    if not src.exists():
        print(f"❌ Archivo no encontrado: {src}", file=sys.stderr)
        return 1

    # Copiar desde OneDrive si es cloud-only
    local = safe_copy_from_cloud(src)

    ext = local.suffix.lower()
    meta: dict[str, Any] = {}

    # ---------- Lectura ----------
    if not args.quiet:
        print(f"📂 Leyendo: {src.name}  [{ext}]")

    try:
        if ext in (".xlsx", ".xls"):
            df_raw, sheet_used, sr_used, all_sheets = read_excel(
                local, args.sheet, args.start_row
            )
            meta = {
                "type": "excel",
                "sheet": sheet_used,
                "all_sheets": all_sheets,
                "start_row": sr_used,
            }
            if not args.quiet:
                print(f"   Hoja: {sheet_used}  |  StartRow: {sr_used}  |  "
                      f"Hojas disponibles: {all_sheets}")
        elif ext == ".csv":
            df_raw, enc_used, sep_used = read_csv(local, args.encoding, args.sep)
            meta = {"type": "csv", "encoding": enc_used, "separator": sep_used}
            if not args.quiet:
                print(f"   Encoding: {enc_used}  |  Separador: '{sep_used}'")
        else:
            print(f"❌ Extensión no soportada: {ext}", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"❌ Error al leer el archivo: {exc}", file=sys.stderr)
        return 1

    if df_raw.empty:
        print("⚠️  El archivo está vacío o no tiene datos legibles.", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"   Dimensiones originales: {df_raw.shape[0]:,} filas × {df_raw.shape[1]} cols")

    # ---------- Limpieza ----------
    df_clean, changes = clean(df_raw, mask_pii_flag=not args.no_pii)
    if not args.quiet and changes:
        for chg in changes:
            print(f"   🧹 {chg}")

    # ---------- Análisis ----------
    stats = analyse(df_clean)

    # ---------- Report JSON ----------
    report = build_report(src, df_clean, stats, changes, meta)

    # ---------- Preview Markdown ----------
    preview_md = df_to_markdown(df_clean, n=args.preview)

    # ---------- Guardar salidas ----------
    stem = src.stem
    out_dir = Path(args.out_dir) if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{stem}_report.json"
    md_path   = out_dir / f"{stem}_preview.md"

    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # Preview Markdown con encabezado
    md_content = f"""---
source: {src.name}
generated: {report['generated_at']}
rows: {stats['rows']}
cols: {stats['cols']}
---

# Preview — {src.name}

> **{stats['rows']:,} filas · {stats['cols']} columnas**

{report['wiki_ready']['key_insight']}

## Primeras {args.preview} filas

{preview_md}

## Columnas detectadas

{report['wiki_ready']['column_table']}
"""
    md_path.write_text(md_content, encoding="utf-8")

    # ---------- Consola ----------
    if not args.quiet:
        print()
        print(f"✅ Análisis completado")
        print(f"   Filas limpias : {stats['rows']:,}")
        print(f"   Columnas      : {stats['cols']}")
        if stats.get("date_range"):
            for col, rng in stats["date_range"].items():
                print(f"   Período ({col}): {rng['min']} → {rng['max']}")
        if stats.get("numeric_totals"):
            for col, nums in stats["numeric_totals"].items():
                print(f"   Σ {col}: ${nums['sum']:,.0f}")
        if stats.get("duplicates", 0) > 0:
            print(f"   ⚠️  Duplicados encontrados: {stats['duplicates']}")
        print()
        print(f"   📄 Reporte JSON  → {json_path}")
        print(f"   📋 Preview MD    → {md_path}")

    # Imprimir JSON a stdout para que PowerShell/bi-ingest pueda capturarlo
    print(json.dumps(report, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
