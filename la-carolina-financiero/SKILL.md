---
name: financiero
description: >
  Orquestador del agente financiero de La Carolina De Transporte.
  Procesa documentos financieros (facturas, nómina, reportes de pagos, estados de cuenta)
  desde .raw/finanzas/, .raw/Contabilidad/ o .raw/Sistemas/ y los integra al wiki.
  Mantiene páginas por período, categoría de gasto y proveedor/cliente.
  Actualiza Wiki/index.md, Wiki/log.md y Wiki/hot.md al finalizar.
  Triggers: "/financiero", "ingest [archivo financiero]", "procesa esta factura",
  "registra este pago", "ingestar reporte de pagos", "procesar nómina".
allowed-tools: Read Write Edit Glob Grep Agent
---

# financiero: Orquestador de Ingesta Financiera

Eres el orquestador del módulo Financiera. Tu trabajo es recibir un documento financiero, dispatchar el agente especializado, y luego actualizar los archivos maestros del wiki. En Obsidian existe una sola carpeta para este módulo: `Wiki/financiera/`.

## Paso 1 — Identificar el archivo

Si el usuario dio un nombre de archivo, búscalo en este orden:
1. `.raw/finanzas/`
2. `.raw/Contabilidad/`
3. `.raw/Sistemas/`
4. Raíz de `.raw/`

Si no existe, dile al usuario dónde colocarlo y detente.

## Paso 2 — Dispatchar el agente

Llama al agente `financiero` (definido en `agents/financiero.md`) con:
- Ruta absoluta del archivo fuente
- Vault path: `D:\TRANSPORTES LA CAROLINA\Administracion Datos - Documentos\La Carolina De Transporte`
- Instrucción específica del usuario si la hay

El agente procesa el documento y retorna su reporte.

## Paso 3 — Actualizar archivos maestros

Con el reporte del agente:

### Wiki/index.md
Añade o actualiza las entradas correspondientes bajo las secciones `## Financiera` y `## Entidades`.

### Wiki/log.md
Añade al INICIO del archivo:
```markdown
## [YYYY-MM-DD] ingest | [Nombre del documento]
- Fuente: `.raw/[subcarpeta]/[archivo]`
- Período: YYYY-MM
- Tipo: [egreso/ingreso/nómina/estado de cuenta]
- Monto: [valor]
- Páginas creadas: [[Página 1]], [[Página 2]]
- Páginas actualizadas: [[Página 3]]
- Alertas: [ninguna / descripción]
```

### Wiki/hot.md
Reescribe completamente con contexto actualizado (máx 500 palabras).

## Paso 4 — Reportar al usuario

Muestra un resumen claro:
```
✓ Documento procesado: [nombre]
  Período: [mes/año]
  Tipo: [tipo]
  Monto: [valor]
  Páginas creadas: N
  Páginas actualizadas: N
  Alertas: [ninguna o descripción]
```

## Batch (múltiples archivos)

Si el usuario dice "procesa todo" o pasa varios archivos:
1. Lista todos los archivos encontrados y confirma con el usuario.
2. Dispatcha un agente por archivo en paralelo.
3. Consolida todos los reportes.
4. Actualiza index, log y hot una sola vez al final.
5. Reporta totales: N documentos, X páginas creadas, Y páginas actualizadas.
