# 🧹 MCE Pro 2.0 — Especificación del Módulo PREPARE

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Módulo:** PREPARE (Fase 2 del Pipeline)

---

## 1. Misión

PREPARE transforma registros brutos de VALIDATE en obras lógicas limpias, normalizadas y listas para enriquecimiento.

> **Pregunta que responde PREPARE:**
> ¿Qué obra representa este conjunto de archivos?

> **Pregunta que NO responde PREPARE:**
> ¿Qué metadatos tiene esta obra? (Eso es trabajo de ENRICH)

---

## 2. Posición en el Pipeline

```text
MSL → VALIDATE → [ PREPARE ] → ENRICH → PUBLISHER → MASTER
                       │
                       ├── Entrada:  ValidatedScanPackage
                       ├── Salida:   PreparedWorkPackage[]
                       ├── DB:       Lee/Escribe mce_staging, lee mce_cache
                       └── UI:       Panel verde con 3 pestañas
```

---

## 3. Entrada y Salida

### 3.1 Entrada

- **Contrato:** `ValidatedScanPackage` (schema_version: 1)
- **Origen:** `mce_staging.contract_instances`
- **Estado requerido:** `VALIDATED` o `VALIDATED_WITH_WARNINGS`
- **Contenido relevante:**
  - `records[]` con content_type = MEDIA/SUBTITLE/METADATA
  - `category` detectada por VALIDATE
  - `bank_id`, `scan_id`, `pipeline_id`

### 3.2 Salida

- **Contrato:** `PreparedWorkPackage` (schema_version: 1)
- **Destino:** `mce_staging.contract_instances`
- **Estados generados:**
  - `READY_FOR_ENRICHMENT` → Obra lista para ENRICH
  - `HUMAN_REVIEW` → Requiere decisión humana
  - `PREPARE_INSUFFICIENT` → Sin evidencia suficiente

---

## 4. Principios Fundamentales

### 4.1 Obra Lógica ≠ Archivo

```text
REGLA:
  Una obra lógica es una entidad abstracta (película, serie, etc.)
  que puede estar representada por múltiples archivos físicos.

  EJEMPLOS:
    - Avatar (2009) → 1 obra lógica, 1 archivo .mkv
    - Breaking Bad S01 → 1 obra lógica, 7 archivos .mkv + subs
    - DVD Combo → 1 obra lógica, múltiples VOBs + IFOs
```

### 4.2 Carpeta > Filename

```text
REGLA:
  El nombre de la carpeta contenedora tiene más peso
  que el nombre del archivo para determinar el título.

  PRIORIDAD:
    1. movie.nfo <title> tag
    2. Carpeta contenedora
    3. Filename del archivo principal
```

### 4.3 Títulos Numéricos Protegidos

```text
REGLA:
  Números como 1917, 1984, 2001, 2049, District 9
  SON títulos válidos, NO son años extraíbles.

  PROTECCIÓN EXPLÍCITA:
    - 1917 → título completo
    - 1984 → título completo
    - 2001: A Space Odyssey → "2001" es parte del título
    - Blade Runner 2049 → "2049" es parte del título
    - District 9 → "9" es parte del título
```

### 4.4 No Contar Ruido como Obras

```text
EXCLUIR DEL CONTEO:
  ❌ Subtítulos (.srt, .sub, .ass)
  ❌ Trailers, teasers, samples
  ❌ Thumbs.db, .DS_Store
  ❌ Archivos .nfo (son metadata)
  ❌ Imágenes (posters, fanart)
  ❌ Carpetas VIDEO_TS como obras individuales

CONTAR COMO OBRAS:
  ✅ Videos principales (.mkv, .mp4, .avi)
  ✅ Estructuras DVD completas (como 1 obra)
  ✅ Series completas (como 1 obra lógica)
```

---

## 5. Proceso de Preparación

### 5.1 Vista General

```text
ValidatedScanPackage
        │
        ▼
┌─ FASE 1: FILTRADO DE RUIDO ──────────────────────┐
│  Excluir subtítulos, trailers, system files       │
│  Conservar evidencia (subs, .nfo)                 │
└───────────────────────────────────────────────────┘
        │
        ▼
┌─ FASE 2: LIMPIEZA DE TÍTULOS ────────────────────┐
│  Eliminar tags de releases (1080p, BluRay, etc.)  │
│  Reemplazar puntos/guiones con espacios           │
│  Extraer año posible                              │
│  Proteger títulos numéricos                       │
└───────────────────────────────────────────────────┘
        │
        ▼
┌─ FASE 3: AGRUPACIÓN ─────────────────────────────┐
│  Agrupar por carpeta contenedora                  │
│  Detectar estructuras de series                   │
│  Detectar estructuras DVD                         │
│  Unir evidencias dispersas                        │
└───────────────────────────────────────────────────┘
        │
        ▼
┌─ FASE 4: CONSULTA WIKIMEDIA ─────────────────────┐
│  Buscar en Wikidata/Wikipedia                     │
│  Cachear resultados                               │
│  Extraer aliases y external_ids                   │
└───────────────────────────────────────────────────┘
        │
        ▼
┌─ FASE 5: CLASIFICACIÓN ──────────────────────────┐
│  Asignar categoría (Peliculas, Series, etc.)      │
│  Calcular confianza de clasificación              │
│  Marcar para revisión humana si ambiguo           │
└───────────────────────────────────────────────────┘
        │
        ▼
PreparedWorkPackage[]
```

---

## 6. FASE 1 — Filtrado de Ruido

### 6.1 Qué Excluir del Conteo de Obras

```text
CONTENT_TYPE = NOISE:
  - Thumbs.db, desktop.ini, .DS_Store
  - Archivos ocultos (is_hidden = true)
  - Archivos de 0 bytes
  - carpetas __MACOSX, $RECYCLE.BIN

CONTENT_TYPE = EXTRA_CONTENT:
  - trail*.mp4, teaser*.mp4
  - sample*.mkv, sample*.mp4
  - behind_the_scenes*, deleted_scenes*
  - extras/, bonus/

CONTENT_TYPE = SUBTITLE:
  - .srt, .sub, .ass, .ssa, .vtt, .idx
  → Se conservan como EVIDENCIA pero no cuentan como obra

CONTENT_TYPE = METADATA:
  - .nfo, .txt, .json, .xml
  → Se extrae información pero no cuenta como obra
```

### 6.2 Qué Conservar como Evidencia

```text
EVIDENCIA PRIMARIA:
  ✅ Archivos de video principales (.mkv, .mp4, .avi, .vob)
  ✅ Estructuras DVD completas (VIDEO_TS folder)

EVIDENCIA SECUNDARIA:
  ✅ Subtítulos asociados (para confirmar idioma)
  ✅ Archivos .nfo (para extraer título oficial)
  ✅ Imágenes en carpeta raíz (poster.jpg, fanart.jpg)

EVIDENCIA CONTEXTUAL:
  ✅ Nombre de carpeta contenedora
  ✅ Nombres de carpetas padre
  ✅ Drive letter y ruta completa
```

### 6.3 Resultado del Filtrado

```text
ENTRADA: 15,420 registros (VALIDATE)
FILTRADO:
  - Noise: 890 registros excluidos
  - Subtitles: 2,340 registros → evidencia
  - Metadata: 120 registros → evidencia extraída
  - Extras: 150 registros excluidos

SALIDA: ~12,000 registros válidos para agrupación
CONTEO: ~8,807 obras lógicas estimadas
```

---

## 7. FASE 2 — Limpieza de Títulos

### 7.1 Tags a Eliminar

```text
RESOLUCIÓN:
  1080p, 720p, 2160p, 4K, UHD, HDR, DV, HDR10, Dolby Vision

CODEC:
  x264, x265, h264, h265, hevc, avc, divx, xvid

FORMATO:
  BluRay, BDRip, BRRip, DVDRip, DVDScr, HDCam, WebRip, WEB-DL

GRUPO:
  [YIFY], [YTS], [RARBG], [EVO], [FGT], [MeGusta], etc.

OTROS:
  Dual Audio, Dual Audio Latino, Castellano, VOSE, Subs Spanish
```

### 7.2 Transformaciones

```text
ANTES → DESPUÉS:
  "Avatar.2009.1080p.BluRay.x264.YIFY" → "Avatar 2009"
  "The_Walking_Dead_S01E01" → "The Walking Dead S01E01"
  "Blade.Runner.2049.2017.2160p" → "Blade Runner 2049 2017"
  "1917.2019.1080p" → "1917 2019" (protegido)
  "El.Corredor.The.Runner.2015" → "El Corredor The Runner 2015"
```

### 7.3 Extracción de Año

```text
PATRÓN:
  Buscar número de 4 dígitos entre 1888-2030
  Preferiblemente al final del título limpio

EXCEPCIONES (NO extraer):
  - 1917, 1984, 2001, 2049 → son parte del título
  - District 9 → 9 es parte del título
  - Si hay 2+ años posibles → tomar el más probable

RESULTADO:
  title_clean: "Avatar"
  possible_year: 2009
  year_confidence: 0.95
```

### 7.4 Protección de Títulos Numéricos

```text
LISTA NEGRA DE TÍTULOS NUMÉRICOS:
  1917, 1984, 2001, 2049, District 9, Room 101, etc.

REGLA:
  SI el título limpio es exactamente un número → PROTEGER
  SI el título contiene número + palabras → ANALIZAR contexto

EJEMPLO:
  "1917.2019" → título="1917", año=2019
  "2001.A.Space.Oddyssey" → título="2001 A Space Odyssey", año=null
```

---

## 8. FASE 3 — Agrupación

### 8.1 Agrupación por Carpeta

```text
ALGORITMO:
  1. Identificar carpeta contenedora más alta
  2. Todos los archivos en esa carpeta → misma obra candidata
  3. Subcarpetas (Seasons, Discs) → misma obra lógica

EJEMPLO:
  E:\Series\Breaking Bad\
    ├── Temporada 1\
    │     ├── S01E01.mkv
    │     └── S01E07.mkv
    └── Temporada 2\
          └── S02E01.mkv

  RESULTADO: 1 obra lógica "Breaking Bad"
             3 physical_occurrences
```

### 8.2 Detección de Series

```text
PATRONES DE SERIES:
  - S[0-9]+E[0-9]+ (S01E01, S12E05)
  - Season [0-9]+ / Temporada [0-9]+
  - [0-9]x[0-9]+ (1x01, 12x05)

SEÑALES:
  - Múltiples archivos con patrón episódico
  - Carpetas "Season X" o "Temporada X"
  - Más de 5 archivos de video en estructura jerárquica

ACCIÓN:
  - Agrupar todos los episodios como 1 obra lógica
  - Registrar seasons_seen: [1, 2, 3, ...]
  - category: "Series"
```

### 8.3 Manejo de DVD/VOB

```text
ESTRUCTURA DVD TÍPICA:
  VIDEO_TS/
    ├── VIDEO_TS.IFO
    ├── VIDEO_TS.VOB
    ├── VTS_01_0.IFO
    ├── VTS_01_0.VOB
    ├── VTS_01_1.VOB
    └── VTS_01_2.VOB

TRATAMIENTO:
  - VIDEO_TS folder = 1 obra candidata
  - No contar cada VOB como obra separada
  - Extraer título de carpeta padre o .nfo
  - is_dvd_structure = true
  - location_type = "dvd_structure"
```

### 8.4 Evidencia Dispersa

```text
ESCENARIO:
  - Subtítulos en E:\Subs\Avatar.srt
  - Video en E:\Peliculas\Avatar.mkv
  - .nfo en E:\Metadata\avatar.nfo

ACCIÓN:
  - Usar hash o nombre base para vincular
  - Unir toda la evidencia a la misma obra lógica
  - physical_occurrences incluye todas las ubicaciones
```

---

## 9. FASE 4 — Consulta Wikimedia

### 9.1 Cuándo Consultar

```text
CONSULTAR SI:
  ✅ Título limpio tiene ≥ 2 palabras
  ✅ Título no es genérico ("video", "pelicula", "sin titulo")
  ✅ Hay año posible extraído
  ✅ Categoría es clara (Peliculas, Series, etc.)

NO CONSULTAR SI:
  ❌ Título es demasiado genérico
  ❌ Título está incompleto o corrupto
  ❌ Ya hay match en caché local
```

### 9.2 Qué Consultar

```text
WIKIDATA:
  - Buscar por título + año (si disponible)
  - Extraer: P31 (instancia de), P577 (fecha de publicación)
  - Extraer: alias en español e inglés
  - Extraer: external IDs (Q-ID)

WIKIPEDIA:
  - Buscar artículo por título
  - Extraer: primer párrafo (descripción)
  - Extraer: infobox (año, director, país)
  - Extraer: enlaces externos (IMDb, TMDb si están)
```

### 9.3 Cacheo de Resultados

```text
CACHE LOCAL:
  - Guardar en mce_cache.wikidata_cache
  - Key: search_query + category
  - TTL: 30 días
  - Incluir: title, year, aliases, external_ids, confidence

REUTILIZACIÓN:
  - Antes de consultar, buscar en caché
  - Si hit → usar directamente
  - Si miss → consultar y guardar
```

---

## 10. FASE 5 — Clasificación

### 10.1 Categorías Válidas

| Categoría | Señales | Ejemplos |
|-----------|---------|----------|
| Peliculas | 1 archivo, 90-180 min, estructura plana | Avatar, Inception |
| Series | Múltiples episodios, temporadas, SxxExx | Breaking Bad, TWD |
| Novelas | Episodios diarios, 30-60 min, largo running | La Usurpadora |
| Anime | Estilo japonés, AniList match, subbed/dubbed | Naruto, One Piece |
| Doramas | Drama asiático, 16-24 episodios, coreano/japonés | Goblin, Alice |
| Animadas | Animación occidental, Disney/Pixar/DreamWorks | Toy Story, Shrek |
| Concursos | Reality shows, episodios semanales, TV show | Survivor, MasterChef |

### 10.2 Algoritmo de Clasificación

```text
1. ¿Hay estructura de temporadas/episodios?
   → Sí: ¿Es animación japonesa? → Anime : Series

2. ¿Es un solo archivo de 90-180 minutos?
   → Sí: ¿Es animación? → Animadas : Peliculas

3. ¿Es estructura DVD?
   → Sí: Analizar contenido → Peliculas/Otras

4. ¿Tiene patrón de novela diaria?
   → Sí: Novelas

5. ¿Es reality show/concurso?
   → Sí: Concursos

6. ¿Es drama asiático (coreano/japonés)?
   → Sí: Doramas

SI NO HAY SEÑALES CLARAS:
  → classification_confidence < 0.5
  → status: CLASSIFICATION_REVIEW
  → Marcar para revisión humana
```

### 10.3 Cálculo de Confianza

```text
FACTORES QUE AUMENTAN CONFIANZA:
  +0.3 Coincidencia exacta con Wikidata
  +0.2 Estructura clara (series, DVD)
  +0.2 Múltiples evidencias concuerdan
  +0.1 Año extraído consistentemente
  +0.1 Categoria obvia por estructura

FACTORES QUE DISMINUYEN CONFIANZA:
  -0.3 Título genérico o ambiguo
  -0.2 Sin año identificable
  -0.2 Estructura caótica o incompleta
  -0.1 Múltiples interpretaciones posibles

UMBRALES:
  confidence ≥ 0.7 → READY_FOR_ENRICHMENT
  0.5 ≤ confidence < 0.7 → APPROVED_PARCIAL (enriquecer igual)
  confidence < 0.5 → CLASSIFICATION_REVIEW
```

---

## 11. Generación del PreparedWorkPackage

### 11.1 Estructura de Salida

```json
{
  "schema_version": 1,
  "pipeline_id": "uuid",
  "logical_work_id": "uuid",
  "bank_id": "BANCO_001",
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "status": "READY_FOR_ENRICHMENT",

  "titles": {
    "primary_local": "Avatar",
    "original_filename": "Avatar.2009.1080p.BluRay.x264.YIFY.mkv",
    "folder_name": "Avatar 2009",
    "aliases": ["Avatar 2009"],
    "possible_year": 2009,
    "year_source": "filename",
    "year_confidence": 0.95,
    "is_numeric_title_protected": false
  },

  "classification": {
    "category": "Peliculas",
    "confidence": 0.92,
    "signals": ["single_file", "runtime_162min", "no_seasons"]
  },

  "physical_occurrences": [
    {
      "file_path": "E:\\Peliculas\\Avatar.mkv",
      "folder_path": "E:\\Peliculas",
      "drive_letter": "E:",
      "file_size_bytes": 2199023255552,
      "file_extension": ".mkv",
      "is_main_file": true
    }
  ],

  "evidence": {
    "subtitles": [],
    "metadata_files": [],
    "images": [],
    "wikimedia_results": {
      "wikidata_match": true,
      "wikipedia_match": false,
      "q_id": "Q19995",
      "aliases_found": ["Avatar (2009 film)"]
    }
  },

  "prepare_confidence": 0.92,
  "field_provenance": {
    "primary_local": "folder_name",
    "possible_year": "filename_pattern",
    "category": "structure_analysis"
  },

  "flags": {
    "is_dvd_structure": false,
    "is_series": false,
    "has_multiple_files": false,
    "requires_human_review": false
  }
}
```

### 11.2 Persistencia

```text
GUARDAR EN mce_staging:
  1. contract_instances: el PreparedWorkPackage completo
  2. work_states: actualizar estado a READY_FOR_ENRICHMENT
  3. checkpoints: guardar progreso para reanudación

GENERAR:
  - logical_work_id: UUID único para esta obra lógica
  - prepare_confidence: score 0.0-1.0
```

---

## 12. Workers y Concurrencia

### 12.1 Configuración

```text
PREPARE workers: 4-6 threads (CPU bound)

DISTRIBUCIÓN:
  - Thread 1-2: Filtrado y limpieza de títulos
  - Thread 3-4: Agrupación y clasificación
  - Thread 5-6: Consultas Wikimedia (I/O)

CARACTERÍSTICAS:
  - Trabajo principalmente de CPU (parseo, regex)
  - Consultas Wikimedia son I/O bound
  - Backpressure: máximo 1000 obras en cola
```

### 12.2 Checkpointing

```text
GUARDAR PROGRESO:
  - Cada 500 obras procesadas
  - Al completar cada fase
  - Antes de consultas externas (Wikimedia)

REANUDACIÓN:
  - Leer último checkpoint
  - Saltar obras ya procesadas
  - Continuar desde última obra pendiente
```

---

## 13. Métricas y Logging

### 13.1 Métricas por Lote

```text
Para cada lote de preparación:
  - batch_number
  - records_total
  - records_filtered (noise eliminado)
  - works_created
  - series_grouped
  - dvd_structures_detected
  - wikimedia_queries
  - wikimedia_hits (cache)
  - classification_reviews_needed
  - duration_ms
```

### 13.2 Structured Logging

```json
{
  "timestamp": "2025-01-15T11:00:00Z",
  "module": "PREPARE",
  "pipeline_id": "uuid",
  "batch_number": 3,
  "action": "prepare_batch",
  "records_processed": 2000,
  "works_created": 850,
  "noise_filtered": 450,
  "series_grouped": 12,
  "wikimedia_queries": 600,
  "wikimedia_cache_hits": 180,
  "classification_reviews": 8,
  "duration_ms": 8500,
  "status": "success"
}
```

---

## 14. Casos de Test Críticos

### 14.1 Carpeta vs Filename

```text
ENTRADA:
  Carpeta: "E:\El Corredor\"
  Archivo: "The.Runner.2015.mkv"

ESPERADO:
  primary_local: "El Corredor" (carpeta tiene prioridad)
  original_filename: "The.Runner.2015.mkv" (conservado como evidencia)
  possible_year: 2015
  Ambas se registran en evidence
```

### 14.2 Títulos Numéricos

```text
ENTRADA:
  "1917.2019.1080p.mkv"
  "Blade.Runner.2049.2017.mkv"
  "District.9.2009.mkv"

ESPERADO:
  "1917" → título="1917", año=2019 (protegido)
  "Blade Runner 2049" → título="Blade Runner 2049", año=2017
  "District 9" → título="District 9", año=2009
```

### 14.3 Series con Temporadas Dispersas

```text
ENTRADA:
  E:\Series\TWD\Temporada 1\ (7 episodios)
  F:\Backup\TWD\Temporada 4\ (16 episodios)

ESPERADO:
  1 obra lógica: "The Walking Dead"
  seasons_seen: [1, 4]
  physical_occurrences: 23 archivos en 2 drives
  category: "Series"
  confidence: 0.98
```

### 14.4 DVD Combo

```text
ENTRADA:
  E:\DVD\Matrix_Trilogy\
    ├── Matrix\VIDEO_TS\ (multiple VOBs)
    ├── Matrix Reloaded\VIDEO_TS\
    └── Matrix Revolutions\VIDEO_TS\

ESPERADO:
  3 obras lógicas separadas
  Cada una con is_dvd_structure=true
  No contar VOBs individualmente
  titles desde carpeta padre
```

### 14.5 Subtítulos como Evidencia

```text
ENTRADA:
  E:\Peliculas\Inception.mkv
  E:\Subs\Inception.es.srt
  E:\Subs\Inception.en.srt

ESPERADO:
  1 obra lógica: "Inception"
  evidence.subtitles: 2 archivos registrados
  Subtítulos NO cuentan como obra adicional
  Idiomas detectados: ['es', 'en']
```

### 14.6 Trailer Filtrado

```text
ENTRADA:
  E:\Peliculas\Avatar.mkv
  E:\Peliculas\Avatar_trailer.mp4
  E:\Peliculas\Avatar_sample.mkv

ESPERADO:
  1 obra lógica: "Avatar"
  trailer y sample clasificados como NOISE/EXTRA
  NO contar como obras adicionales
  Conservar como evidencia contextual
```

### 14.7 Wikimedia Cache Hit

```text
ENTRADA:
  Obra: "Breaking Bad"
  Wikidata cache ya tiene Q1079

ESPERADO:
  NO consultar Wikidata API
  Usar caché: title="Breaking Bad", Q-ID="Q1079"
  aliases: ["Breaking Bad (TV series)"]
  category: "Series" (desde caché)
  wikimedia_cache_hit: true
```

### 14.8 Clasificación Ambigua

```text
ENTRADA:
  Carpeta: "E:\Video Sin Nombre\"
  Archivos: "video1.mkv", "video2.mkv"
  Sin .nfo, sin patrón claro

ESPERADO:
  primary_local: "Video Sin Nombre"
  classification_confidence: 0.35
  status: CLASSIFICATION_REVIEW
  flags.requires_human_review: true
```

### 14.9 Multi-Banco Same Work

```text
ESCENARIO:
  Banco A: "Avatar" en E:\Peliculas\
  Banco B: "Avatar" en F:\Movies\

ESPERADO:
  Ambos generan PreparedWorkPackage separado
  Mismo logical_work_id NO asignado aún (eso es ENRICH)
  Cada uno con su bank_id
  ENRICH detectará que es la misma obra vía caché
```

### 14.10 Idempotencia

```text
ESCENARIO:
  Ejecutar PREPARE dos veces con mismo input

ESPERADO:
  Segunda ejecución produce idéntico resultado
  No se crean obras duplicadas
  logical_work_id consistente por hash de evidencia
  Checkpointing permite reanudar sin duplicar
```

---

## 15. Dependencias

| Dependencia | Uso |
|-------------|-----|
| `mce_staging` | Leer ValidatedScanPackage, escribir PreparedWorkPackage |
| `mce_cache.wikidata_cache` | Leer/escribir caché de Wikimedia |
| `mce_cache.human_corrections` | Leer correcciones humanas previas |
| Wikimedia API | Consultas ocasionales (con rate limit) |

---

## 16. Lo que PREPARE NUNCA Hace

1. ❌ No consulta APIs de películas (TMDb, AniList).
2. ❌ No decide identificación final (eso es ENRICH).
3. ❌ No escribe en `mce_master`.
4. ❌ No elimina archivos físicos.
5. ❌ No modifica nombres de archivos.
6. ❌ No asume que filename es correcto (carpeta > filename).
7. ❌ No cuenta subtítulos como obras.
8. ❌ No ignora títulos numéricos (1917, 2049).
9. ❌ No publica sin clasificación clara.
10. ❌ No salta el paso de validación de Wikimedia.

---

> **Documento mantenido por:** Qwen Code
> **Revisión requerida si:** Se modifican reglas de agrupación, clasificación, o limpieza de títulos.
> **Documento anterior:** `instrucciones/03_DATA_MODEL.md`
> **Siguiente documento:** `instrucciones/05_ENRICH_SPEC.md`
