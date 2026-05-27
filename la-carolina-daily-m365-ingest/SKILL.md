---
name: daily-m365-ingest
description: "Ingesta diaria automática de correo y Teams de administradordatos@lacarolina.com.co. Busca contenido nuevo desde la última ingesta, filtra rutinario/sensible, crea notas fuente y actualiza hot.md. Triggers: /daily-m365-ingest, ingestar correo hoy, ingestar teams hoy, procesar correos nuevos."
---

# daily-m365-ingest: Ingesta Diaria M365

Ejecuta la ingesta incremental de correo Outlook y mensajes Teams para `administradordatos@lacarolina.com.co`.

---

## Paso 1 — Leer estado de ingesta

```
Leer: Wiki/meta/m365-ingest-state.md
Extraer: last_email_ingest, last_teams_ingest
Leer: Wiki/hot.md (contexto de negocio actual)
```

Si `Wiki/meta/m365-ingest-state.md` no existe, crearlo con la fecha de hoy y continuar.

---

## Paso 2 — Buscar correos nuevos

```
mcp__claude_ai_Microsoft_365__outlook_email_search
  query: "received:>=YYYY-MM-DD"   ← usar last_email_ingest
  recipient: administradordatos@lacarolina.com.co
  limit: 25
```

Iterar con `offset` hasta `moreResults: false`.

Para correos relevantes (ver reglas de filtrado), leer el cuerpo completo con `read_resource`.

También buscar correos enviados desde ese día:
```
sender: administradordatos@lacarolina.com.co
query: "sent:>=YYYY-MM-DD"
```

---

## Paso 3 — Buscar mensajes Teams nuevos

**Mensajes enviados por Néstor:**
```
mcp__claude_ai_Microsoft_365__chat_message_search
  query: "from:administradordatos@lacarolina.com.co sent>=YYYY-MM-DD"
```

**Mensajes recibidos por Néstor:**
```
mcp__claude_ai_Microsoft_365__chat_message_search
  query: "sent>=YYYY-MM-DD"
  recipient: administradordatos@lacarolina.com.co
```

Para mensajes con contenido de negocio, leer con `read_resource` si la preview no es suficiente.

---

## Paso 4 — Reglas de filtrado

### OMITIR automáticamente
| Señal | Ejemplo |
|---|---|
| Remitente es bot/sistema | `Approvals@teams.microsoft.com`, `fred@fireflies.ai`, SharePoint notifications |
| Asunto contiene | "compartió un archivo", "te invitó a", "reunión cancelada" |
| Contenido es formato fijo diario | Reportes de combustible Petromil, Reporte contratación conductores |
| Mensaje de 1-2 palabras sin contexto | "Liberado", "Ok", "Gracias." (solos) |
| Newsletter / evento externo | Cámara de Comercio, Fenalco, boletines externos |

### PROCESAR
| Señal | Ejemplo |
|---|---|
| Nueva solicitud de acceso a sistema | "crear usuario GEMA", "permisos MGX" |
| Escalación de bug o problema | "ELE-03149", "salida por el 306", "I048 duplicados" |
| Aprobación presupuestal | OC, OPPC, OCPC con monto/descripción |
| Decisión de negocio o proyecto | Nueva herramienta, contrato, piloto |
| Mensaje de proveedor externo | LM Soluciones, MGX Cloud, Jair (hardware) |
| Nuevo canal o interlocutor | Primer mensaje de un DM no registrado |
| Contenido con nombre de persona nueva | "estimado [Nombre]", usuario creado |

### SENSIBLE — registrar existencia, NO contenido
| Tipo | Qué registrar |
|---|---|
| Embargos, situaciones jurídicas personales | "Recibido documento jurídico re: conductor" |
| Datos médicos, CIE-10 | "Recibido BaseRRHH.xlsm (datos ausentismo)" |
| Contraseñas, tokens | No registrar en absoluto |
| Cartas de vinculación / separación | "Recibido documento RRHH individual" |

---

## Paso 5 — Crear / actualizar notas fuente

**Si ya existe nota para ese canal** (buscar en `Wiki/sources/` por nombre del canal):
- Agregar filas nuevas a la tabla de interacciones
- Actualizar `updated:` en frontmatter
- Agregar hechos nuevos a "Datos Clave"

**Si es un canal nuevo:**
Crear `Wiki/sources/[tipo]-[area]-[asunto]-[año].md` con:

```yaml
---
type: source
title: "Teams DM / Correo — Área: Asunto YYYY"
source_type: teams-dm | teams-group-chat | email | email-thread
date: YYYY-MM-DD   ← fecha primer mensaje
status: ingested
tags:
  - teams | email
  - [área]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Cuerpo:
```markdown
# [Título]

Canal/hilo entre **[Persona A]** (`email@`) y **[Persona B]** — propósito del canal.

## Registro de Interacciones

| Fecha | De | Asunto |
|---|---|---|
| DD-mmm | Persona | Descripción concisa |

## Datos Clave
- **Hecho relevante**: descripción

## Relacionado
- [[Entidad relacionada]]
```

---

## Paso 6 — Actualizar entidades

Si se identifica una persona nueva (nombre en mensaje, email, userId Teams):
1. Verificar si existe en `Wiki/entities/`
2. Si no existe: crear entidad con plantilla `_templates/entity.md`
3. Si existe: agregar nueva referencia en sección "Aparece en"

---

## Paso 7 — Actualizar hot.md

En la sección **Key Recent Facts**, prepend (al inicio, no al final) los hechos nuevos más importantes:

```markdown
- **[YYYY-MM-DD] [Área/Tema]**: [hecho conciso en ≤1 línea].
```

Actualizar **Last Updated** con la fecha de hoy y resumen de lo ingested.

---

## Paso 8 — Actualizar estado

En `Wiki/meta/m365-ingest-state.md`:
- Actualizar `last_email_ingest` y `last_teams_ingest` con la fecha de hoy
- Agregar fila al historial: `| YYYY-MM-DD | N emails | N teams msgs | N creadas | N actualizadas |`

---

## Paso 9 — Reporte final

```
═══════════════════════════════════════
  INGESTA M365 — YYYY-MM-DD
═══════════════════════════════════════
  Emails nuevos:   N procesados / M omitidos
  Teams mensajes:  N procesados / M omitidos
  ───────────────────────────────────────
  Notas creadas:   [[Nota1]], [[Nota2]]
  Notas actualizadas: [[Nota3]], [[Nota4]]
  Entidades nuevas: Nombre (email)
  ───────────────────────────────────────
  Hecho más relevante del día:
  [Una oración sobre lo más importante]
═══════════════════════════════════════
```

---

## Notas importantes

- No modificar archivos en `.raw/`
- No registrar contraseñas ni tokens en ningún archivo wiki
- Si hay duda sobre si algo es sensible → omitir contenido, registrar solo metadatos
- Si un canal tiene solo mensajes de formato fijo (sin variación) → registrar una vez en hot.md como "canal rutinario" y omitir en ingestas futuras
