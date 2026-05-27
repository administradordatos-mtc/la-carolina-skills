---
name: bi-ingest
description: "Ingesta datasets BI de La Carolina desde rutas SharePoint/OneDrive (Consumos, Compras, Operativo, RRHH y rutas adicionales). Maneja archivos cloud-only copiándolos al temp, soporta CSV y XLSX mediante cuatro métodos en cascada (pandas/Python, ImportExcel, Excel-to-Markdown Table plugin, metadata-only), extrae estadísticas clave y genera páginas wiki estructuradas con delta tracking. Triggers: /bi-ingest, bi ingest, ingestar BI, ingest datasets"
---

# bi-ingest — Ingesta de Datasets BI La Carolina

Ingesta los datasets operativos del repositorio BI desde OneDrive/SharePoint hacia el wiki. Detecta archivos nuevos o modificados, extrae estadísticas y genera páginas wiki con tablas Markdown.

---

## PASO 0 — Pregunta inicial obligatoria

**Siempre que se invoque este skill, mostrar primero:**

```
📂 Rutas BI configuradas:
  1. Consumos         → LA CAROLINA BI - Documentos\Consumos
  2. Compras          → LA CAROLINA BI - Documentos\Compras
  3. Operativo        → LA CAROLINA BI - Documentos\Operativo
  4. Recursos Humanos → LA CAROLINA BI - Documentos\Recursos Humanos

¿Quieres agregar otra ruta al proceso? (sí / no)
Si sí → ingresa la ruta completa o el nombre de la subcarpeta dentro de LA CAROLINA BI - Documentos\
```

Si el usuario responde **sí**: agregar la ruta a `$PATHS` y volver a preguntar.  
Si responde **no** o **listo**: continuar con las rutas acumuladas.

---

## PASO 1 — Configuración de rutas

```powershell
$BI_ROOT  = "C:\Users\administradordatos\TRANSPORTES LA CAROLINA\LA CAROLINA BI - Documentos"
$VAULT    = "C:\Users\administradordatos\TRANSPORTES LA CAROLINA\Administracion Datos - Documentos\La Carolina De Transporte"
$MANIFEST = "$VAULT\.bi-manifest.json"

$PATHS = @(
    "$BI_ROOT\Consumos",
    "$BI_ROOT\Compras",
    "$BI_ROOT\Operativo",
    "$BI_ROOT\Recursos Humanos"
    # + rutas adicionales del PASO 0
)
```

---

## PASO 2 — Delta tracking (manifest)

Cargar el manifest antes de procesar cualquier archivo:

```powershell
if (Test-Path $MANIFEST) {
    $manifest = Get-Content $MANIFEST -Encoding UTF8 | ConvertFrom-Json
} else {
    $manifest = [PSCustomObject]@{ sources = [PSCustomObject]@{} }
}
```

**Estructura del manifest** (`.bi-manifest.json`):
```json
{
  "sources": {
    "C:\\...\\Consumos\\2025_01.xlsx": {
      "size": 45312,
      "last_write": "2026-01-15T10:30:00",
      "ingested_at": "2026-05-27",
      "method": "ImportExcel",
      "wiki_pages": ["Wiki/sources/Consumos-Dataset-2023-2026.md"]
    }
  }
}
```

**Lógica de skip** (por archivo):
```powershell
$key  = $file.FullName
$meta = $manifest.sources.$key
if ($meta -and
    $meta.size       -eq $file.Length -and
    $meta.last_write -eq $file.LastWriteTime.ToString("o")) {
    Write-Host "⏭  SKIP (sin cambios): $($file.Name)"
    continue
}
```

Ignorar manifest si el usuario dice **"force"** o **"re-ingestar"**.

---

## PASO 3 — Listar archivos por ruta

```powershell
$files = Get-ChildItem "$path" -Recurse -File |
    Where-Object { $_.Extension -in @('.csv','.xlsx','.xls') -and $_.Name -ne 'desktop.ini' } |
    Sort-Object FullName
```

Mostrar resumen antes de procesar:
```
📁 Consumos          — 54 xlsx  (+ subcarpetas: Mano De Obra, Iva_calculado, Tipologia, Modelo Vehiculo, Grupo_Inventario)
📁 Compras           — 41 xlsx
📁 Operativo         — 20 csv  + 47 xlsx  (Historico_Despacho · Liquidacion_Gmas · Viajes · Recaudo)
📁 Recursos Humanos  —  1 xlsx
```

---

## PASO 4 — Descarga forzada desde OneDrive

Todos los archivos tienen atributo `RecallOnDataAccess` (cloud-only, valor `4199968`).  
**Regla fija**: copiar al temp antes de cualquier lectura.

```powershell
function Copy-FromCloud {
    param([string]$sourcePath)
    $tmpFile = "$env:TEMP\bi_ingest_$([System.IO.Path]::GetFileName($sourcePath))"
    try {
        Copy-Item $sourcePath $tmpFile -Force -ErrorAction Stop
        return $tmpFile
    } catch {
        Write-Warning "❌ Cloud no disponible: $([System.IO.Path]::GetFileName($sourcePath))"
        return $null
    }
}
```

> **Nunca** `Get-Content` directo sobre la ruta original → falla con *"El proveedor de archivos en la nube se cerró inesperadamente"*.

---

## PASO 5 — Extracción de datos (cuatro métodos en cascada)

Para cada archivo `.xlsx` / `.xls` / `.csv`, intentar los métodos en este orden hasta que uno funcione:

```
Método 0 → Python/pandas + bi_clean.py    : PREFERIDO — limpieza, PII, JSON report, preview MD
Método A → ImportExcel (PowerShell)       : alternativa sin Python
Método B → Excel-to-Markdown Table plugin : lectura interactiva vía portapapeles, semi-manual
Método C → Metadata-only                  : fallback mínimo, solo nombre/tamaño/fecha
```

### Método 0 — Python/pandas `bi_clean.py` (automático, PREFERIDO)

**Cuándo usar**: siempre — es el método más completo. Detecta encoding, encabezados corporativos,
enmascara PII, genera estadísticas y exporta JSON + preview Markdown listo para wiki.

**Dependencias** (ya instaladas):
```
Python 3.14  ·  pandas 3.0.2  ·  openpyxl 3.1.5  ·  chardet 7.4.3  ·  tabulate 0.10.0
```

**Script**: `scripts/bi_clean.py` (en la raíz del vault)

**Uso desde PowerShell**:
```powershell
$VAULT  = "C:\Users\administradordatos\TRANSPORTES LA CAROLINA\Administracion Datos - Documentos\La Carolina De Transporte"
$SCRIPT = "$VAULT\scripts\bi_clean.py"
$env:PYTHONIOENCODING = "utf-8"

# Modo batch — capturar JSON directamente
$json = python $SCRIPT $tmpFile --quiet 2>$null | ConvertFrom-Json

# Modo verbose — mostrar análisis en consola + capturar JSON
python $SCRIPT $tmpFile --preview 5 --out-dir $env:TEMP 2>&1 |
    Where-Object { $_ -notmatch "^\{" }   # filtrar JSON del output

# Variables disponibles tras ejecutar en modo --quiet:
$rowCount  = $json.cleaning.rows_clean
$columns   = $json.statistics.columns
$method    = "pandas"
$startRow  = $json.source.start_row      # solo XLSX
$keyInsight= $json.wiki_ready.key_insight
$colTable  = $json.wiki_ready.column_table
```

**Argumentos útiles**:
```
python bi_clean.py <archivo>              # autodetectar todo
python bi_clean.py <archivo> --sheet N   # hoja específica (Excel)
python bi_clean.py <archivo> --start-row 5   # forzar inicio de datos
python bi_clean.py <archivo> --no-pii    # no enmascarar PII
python bi_clean.py <archivo> --preview 20    # más filas en preview
python bi_clean.py <archivo> --quiet     # solo JSON a stdout
python bi_clean.py <archivo> --out-dir C:\tmp  # carpeta de salida
```

**Estructura del JSON retornado** (clave para bi-ingest):
```json
{
  "bi_clean_version": "1.0.0",
  "generated_at": "2026-05-27T...",
  "source": {
    "path": "C:\\...\\archivo.xlsx",
    "name": "archivo.xlsx",
    "size_bytes": 188996,
    "type": "excel",
    "sheet": "_exportar",
    "all_sheets": ["_exportar"],
    "start_row": 0
  },
  "cleaning": {
    "rows_original": 1433,
    "rows_clean": 1433,
    "cols": 25,
    "changes": ["Columnas PII enmascaradas: ['IDENTIFICACION']"]
  },
  "statistics": {
    "rows": 1433,
    "cols": 25,
    "columns": ["FECHA", "TOTAL", ...],
    "null_pct": {"FECHA": 0.0, ...},
    "date_range": {"FECHA": {"min": "2025-01-01", "max": "2025-12-31"}},
    "numeric_totals": {
      "TOTAL": {"sum": 673956430, "mean": 470103, "min": 0, "max": 5000000, "count": 1433}
    },
    "top_n": {"NOM_TER": [{"value": "AUTOLARTE", "count": 245}, ...]},
    "unique_values": {"TIPO": ["AFILIADO", "PROPIO"]},
    "duplicates": 0
  },
  "wiki_ready": {
    "key_insight": "1,433 registros · 25 columnas · Período: 2025-01-01 → 2025-12-31",
    "column_table": "| Columna | Tipo | Ejemplo |\n|---------|------|---------|..."
  }
}
```

**Flujo completo Método 0 en bi-ingest**:
```powershell
$SCRIPT = "$VAULT\scripts\bi_clean.py"
$env:PYTHONIOENCODING = "utf-8"

$report = python $SCRIPT $tmpFile --quiet 2>$null | ConvertFrom-Json
if ($LASTEXITCODE -eq 0 -and $report) {
    $rowCount   = $report.cleaning.rows_clean
    $columns    = $report.statistics.columns
    $dateRange  = $report.statistics.date_range
    $totals     = $report.statistics.numeric_totals
    $topN       = $report.statistics.top_n
    $keyInsight = $report.wiki_ready.key_insight
    $colTable   = $report.wiki_ready.column_table
    $method     = "pandas"
    Write-Host "✅ Método 0 (pandas): $rowCount filas, $($columns.Count) cols"
} else {
    Write-Warning "⚠️ Método 0 falló — intentando Método A (ImportExcel)"
    # → continuar con Método A
}
```

---

### Método A — ImportExcel (PowerShell, alternativa)

**Cuándo usar**: Python no disponible, o cuando se necesita integración PS pura.

```powershell
$hasImportExcel = Get-Module -ListAvailable -Name ImportExcel -ErrorAction SilentlyContinue
if ($hasImportExcel) {
    Import-Module ImportExcel -ErrorAction SilentlyContinue
    $rows     = Import-Excel $tmpFile -ErrorAction SilentlyContinue
    $columns  = ($rows | Select-Object -First 1).PSObject.Properties.Name
    $rowCount = $rows.Count
    $method   = "ImportExcel"
}
```

Si `$rows` es nulo (archivo protegido o multi-hoja): intentar hoja por hoja:
```powershell
$sheetNames = (New-Object OfficeOpenXml.ExcelPackage($tmpFile)).Workbook.Worksheets.Name
foreach ($sheet in $sheetNames) {
    $rows = Import-Excel $tmpFile -WorksheetName $sheet -ErrorAction SilentlyContinue
    if ($rows) { break }
}
```

### Método B — Excel-to-Markdown Table plugin (interactivo)

**Cuándo usar**: ImportExcel no está instalado, o el archivo tiene protección / múltiples hojas complejas que ImportExcel no lee bien.

**Protocolo**:

1. Claude avisa al usuario:
   ```
   📋 XLSX: [nombre-archivo]
   ImportExcel no disponible. Usar Excel-to-Markdown Table plugin de Obsidian.

   Instrucciones:
     1. Abre el archivo en Excel / Google Sheets
     2. Selecciona toda la hoja (Ctrl+A) o el rango que quieras ingestar
     3. Copia (Ctrl+C)
     4. Abre Obsidian → cualquier nota temporal (ej. "Scratch")
     5. Pega (Ctrl+V) → el plugin convierte automáticamente a tabla Markdown
     6. Copia el Markdown resultante y pégalo aquí en el chat

   ¿Listo? Pega el contenido Markdown cuando quieras.
   ```

2. El usuario pega la tabla Markdown en el chat.

3. Claude parsea la tabla:
   ```
   - Extraer headers de la primera fila (| Col1 | Col2 | ... |)
   - Contar filas de datos
   - Identificar columnas de fecha, valor, categoría
   - Realizar análisis estadístico sobre los datos recibidos
   ```

4. Claude genera las páginas wiki usando los datos parseados del Markdown.

5. Registrar en manifest con `"method": "ExcelToMarkdown"`.

**Ejemplo de tabla Markdown recibida:**
```markdown
| Fecha | Vehiculo | Articulo | Cantidad | Valor |
|-------|----------|----------|----------|-------|
| 01/01/2025 | WGB353 | FILTRO ACEITE | 1 | 45000 |
| 02/01/2025 | TDU375 | LLANTA 11R22.5 | 2 | 890000 |
```

**Notas del plugin**:
- Instalado en: `.obsidian/plugins/obsidian-excel-to-markdown-table/`
- Versión: 0.4.0
- Fuentes compatibles: Excel · Google Sheets · Apple Numbers · LibreOffice Calc
- Activación: automática al pegar desde Excel (no requiere comando especial)
- Si el plugin no convierte al pegar: verificar en Obsidian → Settings → Community plugins → "Excel to Markdown Table" está habilitado

### Método C — Metadata-only (fallback mínimo)

Si ambos métodos A y B fallan o el usuario no puede abrir el archivo:

```powershell
$rows     = $null
$columns  = @("(pendiente — usar Método B)")
$rowCount = 0
$method   = "metadata-only"
```

Crear página wiki mínima con: nombre archivo, tamaño, fecha modificación, ruta, y nota de pendiente.  
Marcar en manifest como `"method": "metadata-only"` para reintentar en la próxima ejecución.

---

### CSV

**Método 0 (preferido)**: `bi_clean.py` detecta encoding y separador automáticamente.

**Método A fallback** (PowerShell nativo):
```powershell
$rows = Import-Csv $tmpFile -Delimiter ";" -Encoding UTF8 -ErrorAction SilentlyContinue
if (-not $rows) { $rows = Import-Csv $tmpFile -Delimiter "," -Encoding UTF8 }
$columns  = ($rows | Select-Object -First 1).PSObject.Properties.Name
$rowCount = $rows.Count
$method   = "ImportCsv"
```

---

## PASO 5b — Uso del plugin para muestras visuales en wiki

Independientemente del método de extracción principal, **siempre que el usuario tenga acceso a Excel**, solicitar una muestra de 5-10 filas representativas usando el plugin para incrustarla directamente en la página wiki de análisis:

```
📋 Muestra para wiki:
   Abre [archivo], copia las primeras 10 filas (con headers) y pégalas aquí.
   Se incluirán como tabla de ejemplo en la página wiki.
```

Esta muestra va en la sección `## Muestra de Datos` de la página wiki análisis.  
Etiquetar con: `> *Muestra de [N] filas. Dataset completo: [X] registros.*`

---

## PASO 6 — Análisis estadístico

Para cada dataset (con datos reales del Método A o B):

| Aspecto | Qué calcular |
|---------|-------------|
| **Dimensiones** | Filas × columnas |
| **Período cubierto** | Rango de fechas (columnas con "Fecha", "Date", "Periodo", "Año", "Mes") |
| **Columnas clave** | Lista completa |
| **Valores únicos** | Columnas categóricas con < 50 valores únicos |
| **Totales/sumas** | Columnas numéricas: Valor, Monto, Total, Cantidad, Costo |
| **Top N** | Top 10-15 de: proveedor, artículo, conductor, vehículo, ruta |
| **Distribución** | Agrupación por año/mes cuando hay columna de fecha |

### Análisis específico por carpeta

#### Consumos (`YYYY_MM.xlsx`)
- Total consumo en pesos por mes
- Top 15 artículos/repuestos más consumidos
- Top 15 vehículos con mayor consumo
- Categorías de inventario (cruzar con `Grupo_Inventario\`)
- Correlación con dataset Despacho: ¿vehículos con más novedades "TALLER" tienen más consumos?

#### Consumos — subcarpetas de referencia
| Subcarpeta | Qué extraer |
|-----------|-------------|
| `Modelo Vehiculo\vstVehiculo_Mstr_Gmas.xlsx` | **Maestro flota**: columnas, total registros, cruzar con [[Flota Vehiculos 2023-2025]] |
| `Tipologia_Utilizacion\` | Catálogo tipos de disposición — listar todos los valores |
| `Grupo_Inventario\` | Catálogo grupos — listar grupos y descripciones |
| `Iva_calculado\` | Tabla IVA aplicado — monto total, períodos |
| `Mano De Obra\Moc_YYYY_MM.xlsx` | Costo MOC mensual — total, top técnicos, top vehículos |

#### Compras (`ComprasYYYYMes.xlsx`)
- Total compras en pesos por mes y acumulado anual
- Top 15 proveedores por valor
- Top 15 artículos más comprados
- Centro de costo / área solicitante si existe
- Comparar con Consumos: ¿lo que se compra se consume en el mismo período?

#### Operativo — subcarpetas XLSX

| Subcarpeta | Análisis clave |
|-----------|----------------|
| `Liquidacion_Detallada_Gmas\` | Total liquidado por conductor/mes, promedio, dispersión |
| `Viajes Reacudados\` | Total recaudado por mes, recaudo promedio por viaje |
| `Viajes_Perdidos\` | Total viajes perdidos por mes, causas principales |
| `Recaudo_Cierres\` | Cierre diario promedio, días con mayor/menor recaudo |

#### Recursos Humanos (`Procesos de reclutamiento.xlsx`)
- Total contrataciones por mes/año
- Total retiros por mes/año
- Motivos de retiro (categorías)
- Cargos más contratados
- Tiempo promedio en el proceso de reclutamiento (si hay columnas de fechas de inicio/fin)

---

## PASO 7 — Generación de páginas wiki

### Por carpeta crear:

1. **`Wiki/sources/[Carpeta]-Dataset-[año-inicio]-[año-fin].md`** — fuente + metadata  
2. **`Wiki/[dominio]/[carpeta-slug]-analisis.md`** — estadísticas + KPIs + muestra visual  
3. Actualizar **`Wiki/[dominio]/_index.md`**

### Mapeo dominio

| Carpeta BI | Dominio | _index.md |
|-----------|---------|-----------|
| Consumos | `Wiki/mantenimiento/` | `Wiki/mantenimiento/_index.md` |
| Compras | `Wiki/operativo/` | `Wiki/operativo/_index.md` |
| Operativo | `Wiki/operativo/` | `Wiki/operativo/_index.md` |
| Recursos Humanos | `Wiki/rrhh/` | `Wiki/rrhh/_index.md` |

### Template — página fuente

```markdown
---
title: "[Carpeta] Dataset [año-inicio]–[año-fin]"
type: source
source_type: dataset_[csv|xlsx]
domain: [dominio]
ingest_method: [ImportExcel|ExcelToMarkdown|ImportCsv|metadata-only]
created: [YYYY-MM-DD]
updated: [YYYY-MM-DD]
tags: [dataset, carpeta-slug]
---

# [Carpeta] — Dataset [año-inicio]–[año-fin]

> [!key-insight] [Resumen en una línea]
> [N] archivos · [X] registros totales · [período]

## Origen
| Campo | Detalle |
|-------|---------|
| Fuente | GMAS / MGX vía SharePoint |
| Ruta   | `LA CAROLINA BI - Documentos\[Carpeta]\` |
| Formato | [CSV;/XLSX] |
| Período | [fecha inicio] – [fecha fin] |
| Método extracción | [Método A/B/C] |

## Archivos
| Archivo | Filas | Tamaño KB | Estado |
|---------|-------|-----------|--------|
| … | … | … | ✅/⏳ |

## Estructura de Columnas
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| … | … | … |

## Páginas Relacionadas
- [[Análisis correspondiente]]
- [[_index del dominio]]
```

### Template — página análisis

```markdown
---
title: "[Carpeta] — Análisis [año-inicio]–[año-fin]"
type: concept
domain: [dominio]
created: [YYYY-MM-DD]
updated: [YYYY-MM-DD]
tags: [analisis, carpeta-slug, kpi]
---

# [Carpeta] — Análisis [año-inicio]–[año-fin]

> [!key-insight] [Hallazgo más importante del dataset]

Fuente primaria: [[Dataset correspondiente]]

## Resumen General
| Indicador | Valor |
|-----------|-------|
| Total registros | … |
| Período | … |
| … | … |

## Volumen por Año
| Año | Registros | Variación |
|-----|-----------|-----------|

## [Sección específica según tipo — Top N, distribución, KPIs]

## Muestra de Datos
> *Muestra de [N] filas pegada desde Excel vía Excel-to-Markdown Table plugin.*

[tabla Markdown pegada desde plugin]

## Conexiones
- [[páginas relacionadas]]
```

---

## PASO 8 — Actualización archivos meta

Al finalizar cada carpeta:

1. **`Wiki/hot.md`** — añadir en `## Key Recent Facts`:
   ```
   - **[YYYY-MM-DD] Dataset [Carpeta] ingestado:** [N] archivos · método: [A/B/C] · [hallazgo clave]. Ver [[Análisis]].
   ```

2. **`Wiki/index.md`** — añadir ⭐ a páginas nuevas en la sección del dominio.

3. **`Wiki/[dominio]/_index.md`** — actualizar "Fuentes" y contadores.

4. **`.bi-manifest.json`** — registrar por archivo:
   ```powershell
   $entry = [PSCustomObject]@{
       size        = $file.Length
       last_write  = $file.LastWriteTime.ToString("o")
       ingested_at = (Get-Date -Format "yyyy-MM-dd")
       method      = $method   # "pandas" | "ImportExcel" | "ExcelToMarkdown" | "ImportCsv" | "metadata-only"
       rows        = $rowCount
       cols        = if ($columns) { $columns.Count } else { 0 }
       wiki_pages  = @($sourcePagePath, $analysisPagePath)
   }
   $manifest.sources | Add-Member -NotePropertyName $file.FullName -NotePropertyValue $entry -Force
   [System.IO.File]::WriteAllText($MANIFEST, ($manifest | ConvertTo-Json -Depth 5), [System.Text.Encoding]::UTF8)
   ```

---

## PASO 9 — Reporte final

```
✅ Ingesta BI completada — [YYYY-MM-DD]

📊 Resumen:
  Rutas procesadas   : [N]
  Archivos revisados : [N total]
  ✅ Ingestados      : [N]  (método A: [N] · método B: [N] · método C: [N])
  ⏭  Skip            : [N]  (sin cambios en manifest)
  ❌ Error           : [N]  (cloud no disponible)

📝 Páginas wiki:
  Creadas     : [lista]
  Actualizadas: [lista]

⚠️  Pendientes (metadata-only — completar con Método B):
  - [archivos que requieren Excel-to-Markdown]

💡 Para completar archivos pendientes:
   Abre cada XLSX, copia con Ctrl+A → Ctrl+C, pega en Obsidian (plugin convierte a tabla).
   Luego ejecuta /bi-ingest --force [nombre-archivo] para reingestar solo ese archivo.
```

---

## Herramientas disponibles para lectura

| Herramienta | Tipo | Estado | Cuándo usar |
|-------------|------|--------|-------------|
| **bi_clean.py** (Python/pandas) | Script Python | ✅ `scripts/bi_clean.py` | **PREFERIDO** — CSV y XLSX · limpieza completa · PII · JSON · preview MD |
| **ImportExcel** (PowerShell) | Módulo PS | ✅ v7.8.10 instalado | Alternativa sin Python · batch PS puro |
| **Excel to Markdown Table** (Obsidian) | Plugin | ✅ v0.4.0 instalado | Muestras visuales interactivas · cuando los dos anteriores fallan |
| **Import-Csv** (PowerShell nativo) | Nativo PS | Sin instalación | Fallback solo CSV · sin dependencias |

### Árbol de decisión de métodos

```
¿Python disponible?  (python --version)
  └─ Sí → Método 0: bi_clean.py (CSV y XLSX)
       ├─ Éxito → usar JSON: rows, cols, date_range, totals, top_n, key_insight
       └─ Fallo → continuar con Método A

¿ImportExcel disponible?  (Get-Module ImportExcel)
  └─ Sí → Método A: Import-Excel
       ├─ Éxito → análisis manual PS
       └─ Fallo → continuar con Método B

¿Usuario puede abrir Excel/GSheets?
  └─ Sí → Método B: Excel-to-Markdown Table plugin (interactivo)
       └─ No → Método C: metadata-only (marcar pendiente en manifest)

¿Muestra visual para wiki?
  └─ Método 0 genera _preview.md automáticamente
     Método B puede complementar con filas seleccionadas
```

### Instalación rápida (si se pierde el entorno)

```powershell
# Python y dependencias
pip install pandas openpyxl chardet tabulate

# ImportExcel (PowerShell)
Install-Module ImportExcel -Scope CurrentUser -Force
```

---

## Tratamiento especial — subcarpetas Consumos

| Subcarpeta | Contenido | Prioridad | Notas |
|-----------|-----------|-----------|-------|
| `Modelo Vehiculo\vstVehiculo_Mstr_Gmas.xlsx` | Maestro flota GMAS | 🔴 Alta | Cruzar con [[Flota Vehiculos 2023-2025]] |
| `Tipologia_Utilizacion\` | Catálogo tipos repuestos | 🟡 Media | Referencia estática |
| `Grupo_Inventario\` | Grupos de inventario | 🟡 Media | Referencia estática |
| `Iva_calculado\` | IVA sobre consumos | 🟢 Normal | Complementa Consumos mensuales |
| `Mano De Obra\` | Costos MOC mensuales | 🔴 Alta | Serie temporal paralela a Consumos |

---

## Restricciones PII

- **Nunca publicar** en wiki: cédulas individuales de conductores o empleados
- **Sí publicar**: totales, promedios, conteos agregados, top N sin cédula
- Campos a enmascarar: `Ced.`, `Cedula`, `CC`, `Identificacion`, `Ced. Conductor`
- En las muestras pegadas vía Método B: reemplazar cédulas por `[CC]` antes de publicar

---

## Notas de contexto

- **Sistemas fuente**: GMAS (LM Soluciones) + MGX (compras/almacén)
- **Cloud-only**: atributo `4199968` en todos los archivos → copiar a `$env:TEMP` siempre
- **Encoding CSV**: UTF-8 · separador `;` (fallback `,`)
- **Período disponible**: generalmente ene-2023 hasta mes actual

---

## Integración con otros skills

| Skill | Relación |
|-------|----------|
| `wiki-ingest` | Complementario — procesa documentos textuales (correos, actas); bi-ingest procesa datasets tabulares |
| `wiki-lint` | Ejecutar después de una ingesta grande para detectar páginas huérfanas |
| `financiero` | Consumos + Compras son insumos del análisis financiero de mantenimiento |
| `daily-m365-ingest` | Independiente — no comparte manifest ni rutas |

---

## Scripts auxiliares

| Script | Ruta | Descripción |
|--------|------|-------------|
| `bi_clean.py` | `scripts/bi_clean.py` | Limpieza, análisis estadístico y preview Markdown de cualquier CSV/XLSX |

### bi_clean.py — referencia rápida

```
python scripts/bi_clean.py <archivo>           → autodetección completa
python scripts/bi_clean.py <archivo> --quiet   → solo JSON a stdout (para PS)
python scripts/bi_clean.py <archivo> --preview 20 --out-dir Wiki/
python scripts/bi_clean.py --help             → ayuda completa
```

**Campos clave del JSON de salida usados por bi-ingest:**

| Campo JSON | Uso en wiki |
|-----------|-------------|
| `cleaning.rows_clean` | `registros` en página fuente |
| `statistics.columns` | tabla `## Columnas` |
| `statistics.date_range` | período en frontmatter y callout |
| `statistics.numeric_totals` | KPIs en `## Resumen` |
| `statistics.top_n` | tabla `## Top N` en análisis |
| `statistics.unique_values` | valores posibles en columnas categóricas |
| `statistics.duplicates` | alerta si > 0 |
| `wiki_ready.key_insight` | texto del callout `> [!key-insight]` |
| `wiki_ready.column_table` | tabla Markdown de columnas lista para pegar |
| `source.start_row` | documenta StartRow en metadata del dataset |
