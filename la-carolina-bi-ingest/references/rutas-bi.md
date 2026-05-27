# Referencia — Rutas BI y Mapeo de Dominios

## Rutas base configuradas

| # | Ruta relativa | Contenido | Dominio Wiki | Archivos |
|---|--------------|-----------|-------------|---------|
| 1 | `Consumos\` | Consumos repuestos/inventario por mes | `Wiki/mantenimiento/` | XLSX mensual (2023→actual) |
| 2 | `Consumos\Mano De Obra\` | Costos mano de obra mensual | `Wiki/mantenimiento/` | XLSX: Moc_YYYY_MM |
| 3 | `Consumos\Modelo Vehiculo\` | Maestro vehículos GMAS | `Wiki/operativo/` | `vstVehiculo_Mstr_Gmas.xlsx` |
| 4 | `Consumos\Tipologia_Utilizacion\` | Catálogo tipología repuestos | `Wiki/mantenimiento/` | 2 XLSX |
| 5 | `Consumos\Grupo_Inventario\` | Catálogo grupos de inventario | `Wiki/mantenimiento/` | 1 XLSX |
| 6 | `Consumos\Iva_calculado\` | IVA calculado sobre consumos | `Wiki/mantenimiento/` | 1 XLSX |
| 7 | `Compras\` | Órdenes de compra / facturas por mes | `Wiki/operativo/` | XLSX mensual (2023→actual) |
| 8 | `Operativo\Historico_Despacho\` | ✅ YA INGESTADO | `Wiki/operativo/` | CSV trimestral/mensual |
| 9 | `Operativo\Liquidacion_Detallada_Gmas\` | Liquidaciones GMAS por conductor | `Wiki/operativo/` | XLSX mensual (2024→actual) |
| 10 | `Operativo\Viajes Reacudados\` | Recaudo por viaje | `Wiki/operativo/` | XLSX mensual (2024→actual) |
| 11 | `Operativo\Viajes_Perdidos\` | Viajes perdidos por mes | `Wiki/operativo/` | XLSX mensual (2025→actual) |
| 12 | `Operativo\Recaudo_Cierres\` | Cierres diarios consolidados | `Wiki/operativo/` | XLSX mensual (2025→actual) |
| 13 | `Recursos Humanos\` | Procesos reclutamiento/retiros | `Wiki/rrhh/` | 1 XLSX |

## Raíz BI

```
C:\Users\administradordatos\TRANSPORTES LA CAROLINA\LA CAROLINA BI - Documentos\
```

## Vault destino

```
C:\Users\administradordatos\TRANSPORTES LA CAROLINA\Administracion Datos - Documentos\La Carolina De Transporte\
```

## Manifest delta tracking

```
[VAULT]\.bi-manifest.json
```

## Páginas wiki ya existentes (no crear duplicados)

| Dataset | Página wiki existente |
|---------|----------------------|
| Historico_Despacho 2023-2025 | [[Historico Despacho 2023-2025]] |
| Análisis despacho | [[Despacho Historico Analisis 2023-2025]] |
| Flota vehículos | [[Flota Vehiculos 2023-2025]] |
| Rutas | [[Rutas Operativas]] |
| Consumos repuestos | [[Consumos Repuestos Mantenimiento 2023-2026]] |

## Restricciones PII

- **No publicar** cédulas individuales de conductores
- **No publicar** cédulas de empleados
- **Sí** publicar totales, promedios y conteos agregados
- Los campos PII: `Ced. Conductor`, `Cedula`, `CC`, `Identificacion`
