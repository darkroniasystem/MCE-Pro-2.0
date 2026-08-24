# 🛡️ MCE Pro 2.0 — Especificación del Módulo VALIDATE

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Módulo:** VALIDATE (Fase 1 del Pipeline)

---

## 1. Misión

VALIDATE es la puerta de entrada del pipeline. Su misión es garantizar que el JSON producido por MSL es estructuralmente correcto, coherente y seguro antes de que cualquier otro módulo lo procese.

> **Pregunta que responde VALIDATE:**
> ¿Este escaneo de MSL es válido, está completo y puede procesarse sin riesgos?

> **Pregunta que NO responde VALIDATE:**
> ¿Qué obras contiene este escaneo? (Eso es trabajo de PREPARE)

---

## 2. Posición en el Pipeline

```text
[ MSL ] → VALIDATE → PREPARE → ENRICH → PUBLISHER → MASTER
              │
              ├── Entrada:  JSON crudo de MSL (importado por el usuario)
              ├── Salida:   ValidatedScanPackage
              ├── DB:       Lee/Escribe mce_staging, lee mce_staging.scan_snapshots
              └── UI:       Panel azul con importación y snapshot
```

---

## 3. Entrada y Salida

### 3.1 Entrada

- **Fuente:** JSON crudo generado por MSL
- **Importación:** Manual vía botón en UI
- **Contrato esperado:** `RawScanPackage` (schema_version: 1)

### 3.2 Salida

- **Contrato:** `ValidatedScanPackage` (schema_version: 1)
- **Destino:** `mce_staging.contract_instances`
- **Estados posibles:**
  - `VALIDATED` → Pasa a PREPARE
  - `VALIDATED_WITH_WARNINGS` → Pasa con advertencias
  - `VALIDATION_FAILED` → No pasa. Errores críticos.
  - `ANOMALOUS_SCAN` → No pasa. Requiere revisión.

---

## 4. Proceso de Validación (7 Pasos)

```text
JSON de MSL
      │
      ▼
┌─ PASO 1: LECTURA Y PARSEO ─────┐
│  ¿El archivo es legible?        │
│  ¿El JSON es parseable?         │
└─────────────────────────────────┘
      │
      ▼
┌─ PASO 2: VALIDACIÓN ESTRUCTURAL ─┐
│  ¿Tiene schema_version?          │
│  ¿Tiene bank_id?                 │
│  ¿Tiene records[]?               │
└──────────────────────────────────┘
      │
      ▼
┌─ PASO 3: VALIDACIÓN DE CONTENIDO ─┐
│  ¿bank_id es válido?              │
│  ¿Las rutas son absolutas?        │
│  ¿Las extensiones son reconocidas?│
└───────────────────────────────────┘
      │
      ▼
┌─ PASO 4: DETECCIÓN DE CATEGORÍA ─┐
│  ¿Películas, Series, Anime...?   │
└──────────────────────────────────┘
      │
      ▼
┌─ PASO 5: SNAPSHOT Y DELTA ───────┐
│  Comparar con escaneo anterior    │
│  Calcular: new, modified,         │
│  unchanged, missing               │
└───────────────────────────────────┘
      │
      ▼
┌─ PASO 6: DETECCIÓN DE ANOMALÍAS ─┐
│  Duplicados, archivos sospechosos │
└───────────────────────────────────┘
      │
      ▼
┌─ PASO 7: CLASIFICACIÓN ──────────┐
│  MEDIA, SUBTITLE, METADATA,       │
│  NOISE, UNKNOWN                   │
└───────────────────────────────────┘
      │
      ▼
ValidatedScanPackage
```

---

## 5. Validaciones Principales

### 5.1 Campos Obligatorios

- ✅ schema_version (debe ser 1)
- ✅ bank_id (no vacío, max 50 chars)
- ✅ source (debe ser "MSL")
- ✅ records[] (no vacío)
- ✅ total_records (debe coincidir con len(records))

### 5.2 Por Cada Record

- ✅ record_id (UUID o identificador único)
- ✅ file_path (ruta absoluta)
- ✅ file_name (nombre con extensión)
- ✅ extension (.mkv, .mp4, etc.)
- ✅ size_bytes (≥ 0)

### 5.3 Extensiones Reconocidas

**VIDEO:** .mkv, .mp4, .avi, .mov, .wmv, .flv, .webm, .m4v, .ts, .mpg, .mpeg, .vob, .ifo, .bup

**AUDIO:** .mp3, .flac, .aac, .ogg, .wav, .wma, .m4a, .opus

**SUBTÍTULOS:** .srt, .sub, .ass, .ssa, .vtt, .idx

**METADATOS:** .nfo, .txt, .json, .xml

**IMÁGENES:** .jpg, .jpeg, .png, .webp, .bmp, .gif

---

## 6. Snapshot y Delta

Comparación con el escaneo anterior del mismo banco/sección:

```text
snapshot: {
  total_files:    15420,
  new:            320,     ← Archivos nuevos
  modified:       45,      ← Archivos modificados
  unchanged:      15000,   ← Sin cambios
  missing:        55,      ← Archivos eliminados
  previous_scan_id: "uuid"
}
```

**Delta inverso:** Los archivos "missing" se usarán para REMOVE_AVAILABILITY en PUBLISHER.

---

## 7. Anomalías

| Tipo | Severidad | Descripción |
|------|-----------|-------------|
| CORRUPT_JSON | CRITICAL | JSON no parseable |
| MISSING_BANK_ID | CRITICAL | Falta bank_id |
| EMPTY_RECORDS | CRITICAL | records[] vacío |
| DUPLICATE_FILENAME | WARNING | Mismo filename en múltiples rutas |
| ZERO_SIZE | WARNING | Archivo de 0 bytes |
| UNKNOWN_EXTENSION | INFO | Extensión no reconocida |
| FUTURE_DATE | WARNING | Fecha de modificación futura |

**Escaneo anómalo:** ≥10 warnings → estado ANOMALOUS_SCAN

---

## 8. Clasificación de Registros

```text
PARA CADA RECORD:

  SI extensión es de video → content_type = "MEDIA"
  SI extensión es subtítulos → content_type = "SUBTITLE"
  SI extensión es metadatos → content_type = "METADATA"
  SI filename contiene trailer/teaser/sample → content_type = "NOISE"
  SI es Thumbs.db/.DS_Store → content_type = "NOISE"
  SI extensión no reconocida → content_type = "UNKNOWN"
```

---

## 9. UI de VALIDATE

Panel azul con:

- **[ IMPORTAR JSON DE MSL ]** - Abre file dialog
- **[ IMPORTAR CARPETA ]** - Importa múltiples JSONs
- **Datos del escaneo** - Banco, sección, categoría, archivos, tamaño
- **Snapshot** - Nuevos, modificados, sin cambios, ausentes
- **Anomalías** - Críticas, advertencias, info
- **Clasificación** - MEDIA, SUBTITLE, METADATA, NOISE, UNKNOWN
- **[ ENVIAR A PREPARAR → ]** - Habilitado si VALIDATED

---

## 10. Casos de Test Críticos

| # | Caso | Criticidad |
|---|------|------------|
| 1 | JSON válido → VALIDATED | 🔴 Alta |
| 2 | JSON corrupto → VALIDATION_FAILED | 🔴 Alta |
| 3 | Sin bank_id → VALIDATION_FAILED | 🔴 Alta |
| 4 | Primer escaneo → todos new | 🟡 Media |
| 5 | Archivos eliminados → missing | 🔴 Alta |
| 6 | Duplicados detectados | 🟡 Media |
| 7 | Extensión no reconocida → UNKNOWN | 🟡 Media |
| 8 | Escaneo anómalo (>10 warnings) | 🟡 Media |

---

## 11. Lo que VALIDATE NUNCA Hace

1. ❌ No modifica los datos del JSON
2. ❌ No agrupa archivos en obras (PREPARE)
3. ❌ No limpia títulos (PREPARE)
4. ❌ No consulta APIs externas
5. ❌ No escribe en mce_master
6. ❌ No inicia PREPARE automáticamente
7. ❌ No elimina registros del JSON
8. ❌ No inventa datos faltantes

---

## 12. Dependencias

| Dependencia | Uso |
|-------------|-----|
| `mce_staging.pipeline_runs` | Crear registro de ejecución |
| `mce_staging.contract_instances` | Guardar ValidatedScanPackage |
| `mce_staging.scan_snapshots` | Leer/guardar snapshots |
| `mce_master.banks` | Verificar/crear banco |
| Sistema de archivos | Leer JSON importado |
| ijson | Parseo streaming de JSONs grandes |

---

> **Documento mantenido por:** Qwen Code
> **Próximo documento:** `instrucciones/08_UI_SPEC.md`
