# 📜 MCE Pro 2.0 — Contratos entre Módulos

**Estado:** COMPLETO  
**Versión:** 2.0.0  
**Última actualización:** 2025  
**Agente:** Qwen Code (Web)

---

## 1. Visión General

Los contratos definen exactamente qué datos se pasan entre módulos. Son la ley de comunicación del sistema.

### Principios

- **Versionados:** Todo contrato tiene `schema_version`. Cambios rompen versión.
- **Estrictos:** Si un campo requerido falta, el contrato se rechaza. No se procesa.
- **Inmutables en tránsito:** Un módulo no modifica el contrato que recibe. Genera uno nuevo.
- **Persistidos:** Los contratos se guardan en `mce_staging`. No se pasan en memoria.
- **Validados:** Cada transición valida el contrato contra su JSON Schema antes de aceptar.

### Los 5 Contratos

| # | Contrato | De → A | Archivo Schema |
|---|----------|--------|----------------|
| 1 | RawScanPackage | MSL → VALIDATE | `contracts/raw_scan_package.json` |
| 2 | ValidatedScanPackage | VALIDATE → PREPARE | `contracts/validated_scan_package.json` |
| 3 | PreparedWorkPackage | PREPARE → ENRICH | `contracts/prepared_work_package.json` |
| 4 | EnrichedWorkPackage | ENRICH → PUBLISHER | `contracts/enriched_work_package.json` |
| 5 | PublishCommand | PUBLISHER → MASTER | `contracts/publish_command.json` |

### Campos Comunes (presentes en TODOS los contratos)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `schema_version` | integer | ✅ | Versión del contrato. Actual: 1 |
| `pipeline_id` | string (UUID) | ✅ | ID único de la ejecución del pipeline |
| `scan_id` | string (UUID) | ✅ | ID único del escaneo actual |
| `bank_id` | string | ✅ | Identificador externo del banco. NUNCA se pierde |
| `created_at` | string (ISO 8601) | ✅ | Cuándo se creó este contrato |
| `updated_at` | string (ISO 8601) | ✅ | Última modificación |
| `status` | string (enum) | ✅ | Estado actual del paquete |

---

## 2. Contrato 1: RawScanPackage

**Dirección:** MSL → VALIDATE  
**Archivo:** `contracts/raw_scan_package.json`  
**Descripción:** JSON crudo generado por Media Scanner Local. Es la entrada bruta del sistema.

### Estructura

```json
{
  "schema_version": 1,
  "pipeline_id": "uuid-v4",
  "scan_id": "uuid-v4",
  "bank_id": "BANCO_001",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "status": "RAW",

  "source": "MSL",
  "scanner_version": "1.2.0",
  "source_folder": "E:\\Peliculas",
  "section_name": "Peliculas",
  "scan_started_at": "2025-01-15T10:00:00Z",
  "scan_completed_at": "2025-01-15T10:28:00Z",

  "records": [
    {
      "record_id": "uuid-v4",
      "file_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.2009.1080p.BluRay.mkv",
      "file_name": "Avatar.2009.1080p.BluRay.mkv",
      "folder_path": "E:\\Peliculas\\Avatar (2009)",
      "parent_folders": ["Peliculas", "Avatar (2009)"],
      "extension": ".mkv",
      "size_bytes": 8500000000,
      "modified_at": "2024-06-15T14:22:00Z",
      "created_at": "2024-01-10T08:00:00Z",
      "hash_sha256": "abc123...",
      "fingerprint": "fp_001",
      "drive_letter": "E:",
      "is_symlink": false,
      "is_hidden": false
    }
  ],

  "total_records": 15420,
  "total_size_bytes": 45000000000000
}
```

### Campos Específicos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `source` | string | ✅ | Siempre "MSL" |
| `scanner_version` | string | ✅ | Versión del scanner que generó el JSON |
| `source_folder` | string | ✅ | Ruta raíz escaneada |
| `section_name` | string | ✅ | Nombre de la sección (Peliculas, Series, etc.) |
| `scan_started_at` | string | ✅ | Inicio del escaneo |
| `scan_completed_at` | string | ✅ | Fin del escaneo |
| `records` | array | ✅ | Lista de archivos encontrados |
| `records[].record_id` | string | ✅ | ID único del registro |
| `records[].file_path` | string | ✅ | Ruta completa del archivo |
| `records[].file_name` | string | ✅ | Nombre del archivo con extensión |
| `records[].folder_path` | string | ✅ | Carpeta inmediata del archivo |
| `records[].parent_folders` | array[string] | ✅ | Jerarquía de carpetas desde la raíz |
| `records[].extension` | string | ✅ | Extensión del archivo (.mkv, .mp4, .avi, .vob, .srt, etc.) |
| `records[].size_bytes` | integer | ✅ | Tamaño en bytes |
| `records[].modified_at` | string | ✅ | Última modificación del archivo |
| `records[].created_at` | string | ❌ | Fecha de creación del archivo |
| `records[].hash_sha256` | string | ❌ | Hash SHA256 si MSL lo calculó |
| `records[].fingerprint` | string | ❌ | Identificador único del archivo |
| `records[].drive_letter` | string | ✅ | Unidad de disco (E:, F:, etc.) |
| `records[].is_symlink` | boolean | ❌ | Si es enlace simbólico |
| `records[].is_hidden` | boolean | ❌ | Si es archivo oculto |
| `total_records` | integer | ✅ | Total de registros |
| `total_size_bytes` | integer | ✅ | Tamaño total del escaneo |

### Reglas de Validación

1. `bank_id` debe estar presente y no vacío.
2. `records` no puede ser array vacío (si no hay archivos, MSL no debería generar JSON).
3. `records[].file_path` debe ser ruta absoluta.
4. `records[].extension` debe incluir el punto (.mkv, no mkv).
5. `total_records` debe coincidir con `len(records)`.
6. `scan_completed_at` debe ser posterior a `scan_started_at`.

### Estado Inicial

`status`: "RAW"

---

## 3. Contrato 2: ValidatedScanPackage

**Dirección:** VALIDATE → PREPARE  
**Archivo:** `contracts/validated_scan_package.json`  
**Descripción:** El escaneo validado con metadata adicional. VALIDATE confirma que los datos son correctos y añade información de contexto.

### Estructura

```json
{
  "schema_version": 1,
  "pipeline_id": "uuid-v4",
  "scan_id": "uuid-v4",
  "bank_id": "BANCO_001",
  "created_at": "2025-01-15T10:35:00Z",
  "updated_at": "2025-01-15T10:35:00Z",
  "status": "VALIDATED",

  "section_name": "Peliculas",
  "category": "Peliculas",
  "scan_hash": "sha256_of_entire_scan",
  "validation_status": "VALID",
  "validated_at": "2025-01-15T10:34:00Z",

  "snapshot": {
    "total_files": 15420,
    "new": 320,
    "modified": 45,
    "unchanged": 15000,
    "missing": 55,
    "previous_scan_id": "uuid-v4-anterior",
    "previous_scan_date": "2025-01-01T08:00:00Z"
  },

  "anomalies": [
    {
      "anomaly_id": "uuid-v4",
      "type": "DUPLICATE_FILENAME",
      "severity": "WARNING",
      "description": "Archivo 'pelicula.mkv' aparece en 2 carpetas diferentes",
      "affected_records": ["record_id_1", "record_id_2"],
      "recommendation": "REVIEW"
    }
  ],

  "warnings": [
    "55 archivos del escaneo anterior ya no existen",
    "3 archivos tienen extensión no reconocida"
  ],

  "records": [
    {
      "record_id": "uuid-v4",
      "file_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.2009.1080p.BluRay.mkv",
      "file_name": "Avatar.2009.1080p.BluRay.mkv",
      "folder_path": "E:\\Peliculas\\Avatar (2009)",
      "parent_folders": ["Peliculas", "Avatar (2009)"],
      "extension": ".mkv",
      "size_bytes": 8500000000,
      "modified_at": "2024-06-15T14:22:00Z",
      "drive_letter": "E:",
      "content_type": "MEDIA",
      "media_type_hint": "video",
      "is_valid": true,
      "validation_notes": ""
    }
  ],

  "total_records": 15420,
  "valid_records": 15380,
  "invalid_records": 40
}
```

### Campos Específicos (además de los comunes)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `section_name` | string | ✅ | Nombre original de la sección |
| `category` | string (enum) | ✅ | Categoría detectada: Peliculas, Series, Novelas, Anime, Doramas, Animadas, Concursos |
| `scan_hash` | string | ✅ | Hash del escaneo completo para idempotencia |
| `validation_status` | string (enum) | ✅ | VALID, VALID_WITH_WARNINGS, ANOMALOUS |
| `validated_at` | string | ✅ | Cuándo se completó la validación |
| `snapshot` | object | ✅ | Comparación con escaneo anterior |
| `snapshot.total_files` | integer | ✅ | Total de archivos en este escaneo |
| `snapshot.new` | integer | ✅ | Archivos nuevos |
| `snapshot.modified` | integer | ✅ | Archivos modificados |
| `snapshot.unchanged` | integer | ✅ | Archivos sin cambios |
| `snapshot.missing` | integer | ✅ | Archivos que ya no existen (delta inverso) |
| `snapshot.previous_scan_id` | string | ❌ | ID del escaneo anterior (null si es el primero) |
| `anomalies` | array | ❌ | Lista de anomalías detectadas |
| `anomalies[].type` | string | ✅ | Tipo: DUPLICATE_FILENAME, CORRUPT_JSON, INVALID_STRUCTURE, etc. |
| `anomalies[].severity` | string | ✅ | CRITICAL, WARNING, INFO |
| `warnings` | array[string] | ❌ | Advertencias legibles para el usuario |
| `records[].content_type` | string | ✅ | MEDIA, SUBTITLE, METADATA, NOISE, UNKNOWN |
| `records[].media_type_hint` | string | ❌ | video, audio, image, subtitle, other |
| `records[].is_valid` | boolean | ✅ | Si el registro pasó validación |
| `valid_records` | integer | ✅ | Total de registros válidos |
| `invalid_records` | integer | ✅ | Total de registros inválidos |

### Reglas de Validación

1. `category` debe ser uno de los valores permitidos.
2. `validation_status` no puede ser VALID si hay anomalías con severity CRITICAL.
3. `snapshot.new` + `snapshot.modified` + `snapshot.unchanged` debe ser ≤ `total_files`.
4. Si `snapshot.missing` > 0, debe existir al menos un warning explicativo.
5. Todos los records con `is_valid: false` deben tener `validation_notes` no vacío.

### Transición de Estado

- RAW → VALIDATED (si `validation_status` es VALID o VALID_WITH_WARNINGS)
- RAW → VALIDATION_FAILED (si hay anomalías CRITICAL)
- RAW → ANOMALOUS_SCAN (si hay demasiadas anomalías WARNING)

---

## 4. Contrato 3: PreparedWorkPackage

**Dirección:** PREPARE → ENRICH  
**Archivo:** `contracts/prepared_work_package.json`  
**Descripción:** Una obra lógica única, agrupada y clasificada. Este contrato se genera UNA VEZ POR OBRA LÓGICA, no por archivo.

### Estructura

```json
{
  "schema_version": 1,
  "pipeline_id": "uuid-v4",
  "scan_id": "uuid-v4",
  "bank_id": "BANCO_001",
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "status": "READY_FOR_ENRICHMENT",

  "logical_work_id": "uuid-v4",
  "category": "Peliculas",

  "titles": {
    "primary_local": "Avatar",
    "filename_reference": "Avatar.2009.1080p.BluRay",
    "original_candidate": null,
    "spanish_candidate": null,
    "alternatives": []
  },

  "possible_year": 2009,

  "local_evidence": [
    {
      "evidence_id": "uuid-v4",
      "type": "FOLDER_NAME",
      "value": "Avatar (2009)",
      "source_path": "E:\\Peliculas\\Avatar (2009)",
      "confidence": 0.95
    },
    {
      "evidence_id": "uuid-v4",
      "type": "FILENAME",
      "value": "Avatar.2009.1080p.BluRay.mkv",
      "source_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.2009.1080p.BluRay.mkv",
      "confidence": 0.85
    }
  ],

  "wikimedia_evidence": [
    {
      "evidence_id": "uuid-v4",
      "source": "wikidata",
      "wikidata_id": "Q248713",
      "title": "Avatar",
      "year": 2009,
      "media_type": "film",
      "aliases": ["Avatar de James Cameron"],
      "confidence": 0.92,
      "fetched_at": "2025-01-15T11:00:00Z"
    }
  ],

  "possible_external_ids": {
    "wikidata": "Q248713",
    "tmdb": null,
    "imdb": null,
    "anilist": null
  },

  "physical_occurrences": [
    {
      "occurrence_id": "uuid-v4",
      "type": "file",
      "file_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.2009.1080p.BluRay.mkv",
      "folder_path": "E:\\Peliculas\\Avatar (2009)",
      "drive_letter": "E:",
      "size_bytes": 8500000000,
      "extension": ".mkv"
    }
  ],

  "structure": {
    "is_dvd": false,
    "is_series": false,
    "seasons_seen": [],
    "files_count": 1,
    "total_size_bytes": 8500000000
  },

  "prepare_confidence": 0.95,
  "classification_confidence": 0.98,

  "noise_filtered": [
    {
      "original_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.srt",
      "filter_reason": "SUBTITLE",
      "kept_as_evidence": true
    },
    {
      "original_path": "E:\\Peliculas\\Avatar (2009)\\trailer.mp4",
      "filter_reason": "EXTRA_CONTENT",
      "kept_as_evidence": false
    }
  ]
}
```

### Campos Específicos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `logical_work_id` | string (UUID) | ✅ | ID único de la obra lógica. Generado por PREPARE |
| `category` | string (enum) | ✅ | Peliculas, Series, Novelas, Anime, Doramas, Animadas, Concursos |
| `titles.primary_local` | string | ✅ | Mejor título local determinado (normalmente la carpeta) |
| `titles.filename_reference` | string | ❌ | Título extraído del filename (si difiere de carpeta) |
| `titles.original_candidate` | string | ❌ | Candidato a título original (si Wikimedia lo sugirió) |
| `titles.spanish_candidate` | string | ❌ | Candidato a título en español |
| `titles.alternatives` | array[string] | ❌ | Otros títulos posibles |
| `possible_year` | integer | ❌ | Año probable extraído localmente. Null si no se encontró |
| `local_evidence` | array | ✅ | Evidencia local (carpeta, filename, estructura). Mínimo 1 |
| `wikimedia_evidence` | array | ❌ | Evidencia de Wikipedia/Wikidata si se consultó |
| `possible_external_ids` | object | ❌ | IDs externos preliminares (solo de Wikimedia) |
| `physical_occurrences` | array | ✅ | Ubicaciones físicas de la obra. Mínimo 1 |
| `structure.is_dvd` | boolean | ✅ | Si es estructura DVD/VOB |
| `structure.is_series` | boolean | ✅ | Si es serie con temporadas |
| `structure.seasons_seen` | array[integer] | ❌ | Temporadas detectadas (solo si is_series) |
| `structure.files_count` | integer | ✅ | Número de archivos que componen esta obra |
| `structure.total_size_bytes` | integer | ✅ | Tamaño total |
| `prepare_confidence` | float | ✅ | Confianza de la preparación (0.0 - 1.0) |
| `classification_confidence` | float | ✅ | Confianza de la clasificación (0.0 - 1.0) |
| `noise_filtered` | array | ❌ | Archivos filtrados como ruido (subs, trailers, .nfo) |

### Reglas de Validación

1. `logical_work_id` debe ser UUID válido y único dentro del pipeline.
2. `titles.primary_local` no puede estar vacío.
3. `local_evidence` debe tener al menos 1 elemento.
4. `physical_occurrences` debe tener al menos 1 elemento.
5. Si `structure.is_dvd` es true, `physical_occurrences[].type` debe ser "dvd_structure".
6. Si `structure.is_series` es true, `structure.seasons_seen` no puede estar vacío.
7. `possible_year` si existe: 1888 ≤ year ≤ 2030.
8. `prepare_confidence` y `classification_confidence`: 0.0 ≤ valor ≤ 1.0.

### Transición de Estado

- PREPARED → READY_FOR_ENRICHMENT (si todo es correcto)
- PREPARED → PREPARE_INSUFFICIENT (si `titles.primary_local` es demasiado ambiguo)
- PREPARED → CLASSIFICATION_REVIEW (si `classification_confidence` < 0.5)

---

## 5. Contrato 4: EnrichedWorkPackage

**Dirección:** ENRICH → PUBLISHER  
**Archivo:** `contracts/enriched_work_package.json`  
**Descripción:** La obra enriquecida con metadatos externos. Solo las obras con estado APPROVED o APPROVED_PARTIAL llegan a PUBLISHER.

### Estructura

```json
{
  "schema_version": 1,
  "pipeline_id": "uuid-v4",
  "scan_id": "uuid-v4",
  "bank_id": "BANCO_001",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z",
  "status": "READY_FOR_PUBLISH",

  "logical_work_id": "uuid-v4",

  "identity": {
    "original_title": "Avatar",
    "spanish_title": "Avatar",
    "alternative_titles": ["Avatar de James Cameron"],
    "year": 2009,
    "category": "Peliculas"
  },

  "metadata": {
    "genres": ["Ciencia ficción", "Aventura", "Acción"],
    "director": ["James Cameron"],
    "main_cast": [
      {"name": "Sam Worthington", "role": "Jake Sully"},
      {"name": "Zoe Saldaña", "role": "Neytiri"}
    ],
    "synopsis": "Un marine parapléjico es enviado a Pandora...",
    "rating": 7.9,
    "runtime_minutes": 162,
    "country": ["Estados Unidos"],
    "language": "English"
  },

  "external_ids": {
    "tmdb": "19995",
    "imdb": "tt0499549",
    "wikidata": "Q248713",
    "anilist": null,
    "tvmaze": null
  },

  "field_provenance": {
    "original_title": {"source": "tmdb", "confidence": 0.99, "fetched_at": "2025-01-15T12:00:00Z"},
    "year": {"source": "tmdb", "confidence": 0.99, "fetched_at": "2025-01-15T12:00:00Z"},
    "rating": {"source": "tmdb", "confidence": 0.95, "fetched_at": "2025-01-15T12:00:00Z"},
    "poster": {"source": "tmdb", "confidence": 0.99, "fetched_at": "2025-01-15T12:00:00Z"},
    "synopsis": {"source": "wikidata", "confidence": 0.90, "fetched_at": "2025-01-15T11:58:00Z"}
  },

  "physical_occurrences": [
    {
      "occurrence_id": "uuid-v4",
      "type": "file",
      "file_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.2009.1080p.BluRay.mkv",
      "folder_path": "E:\\Peliculas\\Avatar (2009)",
      "drive_letter": "E:",
      "size_bytes": 8500000000,
      "extension": ".mkv"
    }
  ],

  "asset_candidates": {
    "poster": [
      {
        "url": "https://image.tmdb.org/t/p/original/avatar_poster.jpg",
        "source": "tmdb",
        "width": 2000,
        "height": 3000
      }
    ],
    "backdrop": [
      {
        "url": "https://image.tmdb.org/t/p/original/avatar_backdrop.jpg",
        "source": "tmdb",
        "width": 3840,
        "height": 2160
      }
    ]
  },

  "identity_confidence": 0.99,
  "metadata_completeness": 0.92,

  "warnings": [],

  "enrichment_path": [
    {"step": 1, "provider": "cache", "result": "MISS"},
    {"step": 2, "provider": "tmdb", "result": "MATCH", "duration_ms": 342},
    {"step": 3, "provider": "validator", "result": "ACCEPTED"}
  ]
}
```

### Campos Específicos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `identity.original_title` | string | ✅ | Título original confirmado |
| `identity.spanish_title` | string | ❌ | Título en español (si existe) |
| `identity.alternative_titles` | array[string] | ❌ | Títulos alternativos |
| `identity.year` | integer | ✅ | Año confirmado |
| `identity.category` | string | ✅ | Categoría confirmada |
| `metadata.genres` | array[string] | ❌ | Géneros |
| `metadata.director` | array[string] | ❌ | Director(es) o creador(es) |
| `metadata.main_cast` | array[object] | ❌ | Reparto principal |
| `metadata.synopsis` | string | ❌ | Sinopsis |
| `metadata.rating` | float | ❌ | Valoración (0.0 - 10.0) |
| `metadata.runtime_minutes` | integer | ❌ | Duración en minutos |
| `metadata.country` | array[string] | ❌ | País(es) de producción |
| `external_ids` | object | ✅ | Al menos UN ID externo debe existir |
| `field_provenance` | object | ✅ | Procedencia de cada campo importante |
| `asset_candidates.poster` | array | ❌ | URLs de posters candidatos |
| `asset_candidates.backdrop` | array | ❌ | URLs de backdrops candidatos |
| `identity_confidence` | float | ✅ | Confianza de la identificación (0.0 - 1.0) |
| `metadata_completeness` | float | ✅ | Completitud de metadatos (0.0 - 1.0) |
| `warnings` | array[string] | ❌ | Advertencias del proceso |
| `enrichment_path` | array | ✅ | Trazabilidad: qué proveedores se usaron y en qué orden |

### Reglas de Validación

1. `status` debe ser READY_FOR_PUBLISH para que PUBLISHER lo acepte.
2. `identity.original_title` no puede estar vacío.
3. `identity.year`: 1888 ≤ year ≤ 2030.
4. `external_ids` debe tener al menos un ID no nulo.
5. `identity_confidence` debe ser ≥ 0.7 para APPROVED.
6. `identity_confidence` puede ser ≥ 0.5 para APPROVED_PARTIAL.
7. `field_provenance` debe incluir procedencia para `original_title` y `year`.
8. `enrichment_path` debe tener al menos 1 paso.
9. Si `metadata.rating` existe: 0.0 ≤ rating ≤ 10.0.
10. Si `metadata.runtime_minutes` existe: 1 ≤ runtime ≤ 600.

### Estados de Salida de ENRICH

| Estado | Significado | ¿Llega a PUBLISHER? |
|--------|-------------|---------------------|
| READY_FOR_PUBLISH | Obra aprobada completamente | ✅ Sí |
| APPROVED_PARTIAL | Obra aprobada con campos faltantes | ✅ Sí |
| HUMAN_REVIEW | Ambigüedad, necesita revisión | ❌ No |
| NOT_FOUND | No se encontró evidencia suficiente | ❌ No |
| PREPARE_INSUFFICIENT | Datos de entrada insuficientes | ❌ No |
| PROVIDER_ERROR | Error de proveedor tras todos los reintentos | ❌ No |

### Transición de Estado

- ENRICHING → READY_FOR_PUBLISH (si `identity_confidence` ≥ 0.7)
- ENRICHING → APPROVED_PARTIAL (si `identity_confidence` ≥ 0.5 pero faltan campos)
- ENRICHING → HUMAN_REVIEW (si hay ambigüedad)
- ENRICHING → NOT_FOUND (si ningún proveedor encontró la obra)
- ENRICHING → PROVIDER_ERROR (si todos los proveedores fallaron)

---

## 6. Contrato 5: PublishCommand

**Dirección:** PUBLISHER → MASTER CATALOG  
**Archivo:** `contracts/publish_command.json`  
**Descripción:** La orden de publicación que PUBLISHER ejecuta contra `mce_master`. Este es el ÚNICO contrato que toca la base de datos sagrada.

### Estructura

```json
{
  "schema_version": 1,
  "pipeline_id": "uuid-v4",
  "scan_id": "uuid-v4",
  "bank_id": "BANCO_001",
  "created_at": "2025-01-15T13:00:00Z",
  "updated_at": "2025-01-15T13:00:00Z",
  "status": "PUBLISHING",

  "publish_id": "uuid-v4",
  "batch_number": 3,
  "total_batches": 10,
  "action": "PUBLISH",

  "works": [
    {
      "logical_work_id": "uuid-v4",
      "action": "CREATE",
      "identity": {
        "original_title": "Avatar",
        "spanish_title": "Avatar",
        "alternative_titles": [],
        "year": 2009,
        "category": "Peliculas"
      },
      "metadata": {
        "genres": ["Ciencia ficción", "Aventura"],
        "director": ["James Cameron"],
        "rating": 7.9,
        "runtime_minutes": 162
      },
      "external_ids": {
        "tmdb": "19995",
        "imdb": "tt0499549",
        "wikidata": "Q248713"
      },
      "asset_paths": {
        "poster": "assets/posters/uuid-v4.jpg",
        "backdrop": "assets/backdrops/uuid-v4.jpg"
      },
      "physical_occurrences": [
        {
          "file_path": "E:\\Peliculas\\Avatar (2009)\\Avatar.2009.1080p.BluRay.mkv",
          "drive_letter": "E:",
          "size_bytes": 8500000000
        }
      ]
    },
    {
      "logical_work_id": "uuid-v4-existente",
      "action": "ADD_AVAILABILITY",
      "bank_id": "BANCO_002",
      "physical_occurrences": [
        {
          "file_path": "F:\\Cine\\Avatar.mkv",
          "drive_letter": "F:",
          "size_bytes": 7200000000
        }
      ]
    },
    {
      "logical_work_id": "uuid-v4-borrado",
      "action": "REMOVE_AVAILABILITY",
      "bank_id": "BANCO_001"
    }
  ],

  "rollback_metadata": {
    "can_rollback": true,
    "previous_state_snapshot": "path/to/snapshot.json",
    "created_at": "2025-01-15T13:00:00Z"
  },

  "preflight_results": {
    "total_works_checked": 200,
    "passed": 198,
    "failed": 2,
    "failures": [
      {
        "logical_work_id": "uuid-v4",
        "reason": "YEAR_OUT_OF_RANGE",
        "details": "Year 2050 exceeds maximum 2030"
      }
    ]
  }
}
```

### Acciones Posibles (`works[].action`)

| Acción | Descripción | Cuándo se usa |
|--------|-------------|---------------|
| CREATE | Crear obra nueva en Master | Primera vez que se publica esta obra |
| UPDATE_METADATA | Actualizar metadatos de obra existente | Rating cambió, se añadió reparto |
| ADD_AVAILABILITY | Añadir banco a obra existente | Otro banco tiene la misma obra |
| REMOVE_AVAILABILITY | Quitar banco de obra existente | Delta inverso: archivo eliminado |
| ARCHIVE | Archivar obra sin bancos disponibles | Ya ningún banco la tiene |

### Campos Específicos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `publish_id` | string (UUID) | ✅ | ID único de esta publicación |
| `batch_number` | integer | ✅ | Número de lote actual |
| `total_batches` | integer | ✅ | Total de lotes en esta publicación |
| `action` | string (enum) | ✅ | PUBLISH, ROLLBACK, DRY_RUN |
| `works` | array | ✅ | Lista de obras a publicar. Máximo 500 |
| `works[].action` | string (enum) | ✅ | Acción específica por obra |
| `works[].identity` | object | Condicional | Requerido para CREATE |
| `works[].metadata` | object | Condicional | Requerido para CREATE y UPDATE_METADATA |
| `works[].external_ids` | object | Condicional | Requerido para CREATE |
| `works[].asset_paths` | object | ❌ | Rutas locales de assets descargados |
| `works[].physical_occurrences` | array | Condicional | Requerido para CREATE y ADD_AVAILABILITY |
| `rollback_metadata` | object | ✅ | Información para poder revertir |
| `rollback_metadata.can_rollback` | boolean | ✅ | Si se puede revertir esta publicación |
| `preflight_results` | object | ✅ | Resultados del preflight check |

### Reglas de Validación

1. `publish_id` debe ser UUID único.
2. `works` no puede estar vacío.
3. `works` máximo 500 elementos por lote.
4. Si `action` es CREATE: `works[].identity` y `works[].external_ids` son obligatorios.
5. Si `action` es ADD_AVAILABILITY: `works[].bank_id` es obligatorio.
6. Si `action` es REMOVE_AVAILABILITY: `works[].bank_id` es obligatorio.
7. `preflight_results.failed` debe ser 0 para proceder con la publicación.
8. `rollback_metadata.can_rollback` debe ser true para publicaciones reales.
9. `batch_number` debe ser ≤ `total_batches`.

### Transición de Estado

- READY_FOR_PUBLISH → PUBLISHING (cuando Publisher empieza)
- PUBLISHING → PUBLISHED (si todas las obras del lote se publican)
- PUBLISHING → PUBLISH_FAILED (si el lote falla → ROLLBACK)
- PUBLISHING → PUBLISH_CONFLICT (si hay conflictos no resolubles)

---

## 7. Reglas Globales de Contratos

### 7.1 Validación en Cada Transición

```
Módulo A genera contrato
      ↓
Validar contra JSON Schema
      ↓
  ¿Válido?
  ├── SÍ → Persistir en mce_staging → Módulo B lo consume
  └── NO → Rechazar + Loggear + No procesar
```

### 7.2 Versionado

- Versión actual: `schema_version: 1`.
- Si se añade un campo opcional: sigue siendo versión 1.
- Si se añade un campo requerido: subir a versión 2.
- Si se elimina un campo: subir a versión 2.
- Si se cambia un tipo: subir a versión 2.
- Módulos deben verificar `schema_version` antes de procesar.

### 7.3 Inmutabilidad

- Un módulo NUNCA modifica el contrato que recibe.
- Si necesita añadir información, genera un NUEVO contrato.
- El contrato original queda como evidencia en `mce_staging`.

### 7.4 Persistencia

- Todos los contratos se guardan en `mce_staging.contract_instances`.
- Cada contrato tiene un `contract_id` (UUID) para trazabilidad.
- Los contratos NO se pasan en memoria entre módulos.
- Los botones de UI ([ ENVIAR A ENRIQUECIMIENTO ]) cambian el estado persistido.

### 7.5 bank_id Siempre Presente

- `bank_id` aparece en TODOS los contratos.
- Nunca se elimina ni se transforma.
- Es la clave para la disponibilidad multi-banco.

### 7.6 logical_work_id vs file_path

- `logical_work_id` es la identidad interna de la obra.
- `file_path` es solo una referencia física.
- NUNCA usar `file_path` como identificador de obra.
- NUNCA usar el título como identificador de obra.

---

## 8. Flujo Completo de Contratos

```
MSL genera JSON
      │
      ▼
RawScanPackage (schema_version: 1, status: "RAW")
      │
      │ [VALIDATE importa y valida]
      ▼
ValidatedScanPackage (schema_version: 1, status: "VALIDATED")
      │
      │ [PREPARE agrupa en obras lógicas]
      ▼
PreparedWorkPackage × N (uno por obra lógica)
      │  (schema_version: 1, status: "READY_FOR_ENRICHMENT")
      │
      │ [ENRICH identifica y enriquece]
      ▼
EnrichedWorkPackage × N
      │  (schema_version: 1, status: "READY_FOR_PUBLISH")
      │
      │ [PUBLISHER ejecuta preflight + publicación]
      ▼
PublishCommand (schema_version: 1, status: "PUBLISHING")
      │
      │ [Escritura transaccional en mce_master]
      ▼
PUBLISHED ✅
```

---

## 9. Ejemplo: Ciclo de Vida de una Obra

**Escenario:** "Avatar" existe en Banco A y Banco B

**PASO 1:** MSL escanea Banco A
```
→ RawScanPackage: bank_id="BANCO_A", records=[Avatar.mkv]
```

**PASO 2:** VALIDATE
```
→ ValidatedScanPackage: category="Peliculas", status="VALIDATED"
```

**PASO 3:** PREPARE
```
→ PreparedWorkPackage: logical_work_id="uuid-001", titles.primary_local="Avatar"
```

**PASO 4:** ENRICH
```
→ Cache: MISS
→ TMDb: MATCH (id: 19995)
→ EnrichedWorkPackage: status="READY_FOR_PUBLISH"
```

**PASO 5:** PUBLISHER
```
→ Preflight: PASS
→ PublishCommand: action="CREATE"
→ mce_master: obra creada + disponibilidad BANCO_A
```

--- Tiempo después ---

**PASO 6:** MSL escanea Banco B
```
→ RawScanPackage: bank_id="BANCO_B", records=[Avatar.mkv]
```

**PASO 7:** VALIDATE + PREPARE
```
→ PreparedWorkPackage: logical_work_id="uuid-002", titles.primary_local="Avatar"
```

**PASO 8:** ENRICH
```
→ Cache: HIT (ya existe obra con TMDb: 19995)
→ NO se consultan APIs. Se reutiliza metadata.
→ EnrichedWorkPackage: status="READY_FOR_PUBLISH"
```

**PASO 9:** PUBLISHER
```
→ Preflight: PASS
→ Deduplicación: obra YA existe (TMDb: 19995)
→ PublishCommand: action="ADD_AVAILABILITY", bank_id="BANCO_B"
→ mce_master: solo se añade disponibilidad BANCO_B
```

---

## 10. Implementación en Código

### Ubicación de Schemas

```
contracts/
├── raw_scan_package.json          ← JSON Schema Draft 07
├── validated_scan_package.json    ← JSON Schema Draft 07
├── prepared_work_package.json     ← JSON Schema Draft 07
├── enriched_work_package.json     ← JSON Schema Draft 07
└── publish_command.json           ← JSON Schema Draft 07
```

### Validación en Python

```python
import json
import jsonschema

def validate_contract(data: dict, contract_type: str) -> bool:
    """Valida un contrato contra su JSON Schema."""
    schema_path = f"contracts/{contract_type}.json"
    with open(schema_path) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        log_error(f"Contrato inválido: {e.message}")
        return False
```

### Persistencia en mce_staging

```sql
CREATE TABLE contract_instances (
    contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL,
    scan_id UUID NOT NULL,
    bank_id VARCHAR(50) NOT NULL,
    contract_type VARCHAR(50) NOT NULL,
    schema_version INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    logical_work_id UUID,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contract_pipeline ON contract_instances(pipeline_id);
CREATE INDEX idx_contract_status ON contract_instances(status);
CREATE INDEX idx_contract_bank ON contract_instances(bank_id);
```
