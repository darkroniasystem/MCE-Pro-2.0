# 🔍 MCE Pro 2.0 — Especificación del Módulo ENRICH

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Módulo:** ENRICH (Fase 3 del Pipeline)

---

## 1. Misión

ENRICH identifica la obra real y completa sus metadatos utilizando la menor cantidad razonable de llamadas externas.

> **Pregunta que responde ENRICH:**
> ¿Qué obra real es esta y qué metadatos suficientemente buenos puedo reunir?

> **Pregunta que NO responde ENRICH:**
> ¿Esta obra puede publicarse al Catálogo Maestro? (Eso es trabajo de PUBLISHER)

---

## 2. Posición en el Pipeline

```text
MSL → VALIDATE → PREPARE → [ ENRICH ] → PUBLISHER → MASTER
                                │
                                ├── Entrada:  PreparedWorkPackage
                                ├── Salida:   EnrichedWorkPackage
                                ├── DB:       Lee/Escribe mce_cache, escribe mce_staging
                                ├── Red:      TMDb, AniList, TVMaze, Wikidata, Tavily, etc.
                                ├── IA:       Qwen 2.5 3B local + Groq fallback
                                └── UI:       Panel púrpura con métricas
```

---

## 3. Entrada y Salida

### 3.1 Entrada

- **Contrato:** `PreparedWorkPackage` (schema_version: 1)
- **Origen:** `mce_staging.contract_instances`
- **Estado requerido:** `READY_FOR_ENRICHMENT`
- **Contenido relevante:**
  - `titles`: Candidatos de títulos locales
  - `possible_year`: Año probable
  - `local_evidence[]`: Evidencia de carpetas, filenames, .nfo
  - `wikimedia_evidence[]`: Evidencia preliminar de PREPARE
  - `possible_external_ids`: IDs preliminares de Wikidata
  - `category`: Categoría asignada por PREPARE
  - `prepare_confidence`: Confianza de la preparación

### 3.2 Salida

- **Contrato:** `EnrichedWorkPackage` (schema_version: 1)
- **Destino:** `mce_staging.contract_instances`
- **Estados posibles:**
  - `READY_FOR_PUBLISH` → Pasa a PUBLISHER
  - `APPROVED_PARTIAL` → Pasa a PUBLISHER con advertencias
  - `HUMAN_REVIEW` → Cola de revisión humana
  - `NOT_FOUND` → No se encontró la obra
  - `PREPARE_INSUFFICIENT` → Datos insuficientes
  - `PROVIDER_ERROR` → Todos los proveedores fallaron

---

## 4. Principios Fundamentales

### 4.1 ENRICH Recibe Obras, No Archivos

```text
❌ MAL: Recibir 50,000 episodios de The Walking Dead
✅ BIEN: Recibir 1 obra lógica "The Walking Dead"

PREPARE ya agrupó. ENRICH procesa la obra lógica.
```

### 4.2 Identificar + Enriquecer Simultáneamente

```text
❌ MAL: Dos pipelines separados (uno identifica, otro enriquece)
✅ BIEN: Cada proveedor puede aumentar confianza de identidad Y completar metadata

Ejemplo:
  TMDb responde con:
    - Confirmación de identidad (title + year match) → identifica
    - Reparto, géneros, rating, poster → enriquece
```

### 4.3 Reutilizar Todo lo de PREPARE

```text
ENRICH NO empieza desde cero.

Consume directamente:
  - titles.primary_local → query principal
  - titles.original_candidate → query alternativa
  - possible_year → filtro de búsqueda
  - category → selección de proveedores
  - local_evidence[] → contexto adicional
  - wikimedia_evidence[] → evidencia ya recopilada
  - possible_external_ids → búsqueda directa por ID si existe
```

### 4.4 La IA Analiza, Nunca Inventa

```text
❌ MAL: "Qwen, ¿qué película es 'El Corredor'?"
✅ BIEN: "Qwen, aquí está la evidencia recogida. Analízala y determina si hay match."

La IA recibe:
  - Evidencia local (títulos, año, categoría)
  - Resultados de APIs (snippets, URLs, datos)
  - Resultados de navegador (texto extraído)

La IA NO recibe:
  - Páginas HTML completas
  - Bases de datos enteras
  - Contexto de otras obras

La IA produce:
  - JSON estructurado con status, confidence, matched_sources
  - NUNCA URLs que no estén en la evidencia entregada
```

### 4.5 Ahorro de APIs

```text
REGLA: Si ya tengo suficiente evidencia → STOP.

No consultar 5 proveedores solo porque existen.
No gastar APIs en obras que la cache ya resolvió.
No repetir búsquedas que ya se hicieron.
```

---

## 5. Cadena de Enriquecimiento

### 5.1 Vista General

```text
PreparedWorkPackage
        │
        ▼
┌─ PASO 1: CACHÉ GLOBAL ─────────────────────────┐
│  ¿Ya se identificó esta obra en otro banco?     │
│  ├── SÍ → Reutilizar. STOP.                     │
│  └── NO → Continuar                             │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─ PASO 2: PROVEEDORES ESPECIALIZADOS ────────────┐
│  Por categoría:                                 │
│  ├── Películas/Series → TMDb                    │
│  ├── Anime → AniList                            │
│  ├── Series (fallback) → TVMaze                 │
│  └── Todos → Wikidata/Wikipedia                 │
│                                                 │
│  ¿Resuelto con confianza ≥ 0.7?                 │
│  ├── SÍ → Validar. STOP.                        │
│  └── NO → Continuar                             │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─ PASO 3: BÚSQUEDA WEB ─────────────────────────┐
│  Tavily → Serper → Exa                          │
│  (escala al siguiente si el anterior falla)     │
│                                                 │
│  ¿Evidencia suficiente?                         │
│  ├── SÍ → Analizar con IA. Continuar.           │
│  └── NO → Continuar                             │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─ PASO 4: BROWSER SEARCH ───────────────────────┐
│  Playwright + Chromium                          │
│  Recolectar evidencia de buscadores             │
│                                                 │
│  ¿Evidencia suficiente?                         │
│  ├── SÍ → Analizar con IA. Continuar.           │
│  └── NO → Continuar                             │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─ PASO 5: ANÁLISIS IA ──────────────────────────┐
│  Qwen 2.5 3B local (Ollama)                     │
│  ├── ¿Resuelto? → Validador MCE                 │
│  └── ¿Falló? → Groq (fallback)                  │
│       ├── ¿Resuelto? → Validador MCE            │
│       └── ¿Falló? → HUMAN_REVIEW                │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─ PASO 6: VALIDADOR DETERMINISTA ───────────────┐
│  Verifica:                                      │
│  ├── Schema JSON válido                         │
│  ├── No URLs inventadas                         │
│  ├── Coherencia de datos                        │
│  └── Confianza mínima                           │
│                                                 │
│  Resultado:                                     │
│  ├── ACEPTA → READY_FOR_PUBLISH                 │
│  ├── ACEPTA_PARCIAL → APPROVED_PARTIAL          │
│  └── RECHAZA → HUMAN_REVIEW o NOT_FOUND         │
└─────────────────────────────────────────────────┘
```

---

## 6. PASO 1 — Caché Global

### 6.1 Objetivo

Evitar llamadas externas redundantes. Si una obra ya fue identificada en otro banco, reutilizar.

### 6.2 Estrategia de Búsqueda en Caché

```text
ORDEN DE BÚSQUEDA:
  1. Por external_ids (si PREPARE proporcionó wikidata_id)
  2. Por original_title + year + category
  3. Por aliases

CRITERIO DE MATCH:
  - Si external_id coincide exactamente → MATCH FUERTE (confianza 1.0)
  - Si title + year + category coinciden → MATCH PROBABLE (confianza 0.9)
  - Si solo title coincide → MATCH AMBIGUO (requiere verificación adicional)
```

### 6.3 Qué se Reutiliza de la Caché

```text
SI HAY MATCH EN CACHÉ:
  ✅ Metadata completa (título, año, géneros, reparto, rating)
  ✅ External IDs (TMDb, IMDb, Wikidata)
  ✅ Asset URLs (poster, backdrop)
  ✅ Procedencia de cada campo

  ❌ NO se reutiliza: physical_occurrences (son específicas del banco actual)
  ❌ NO se reutiliza: bank_id availability (se añade nueva)

RESULTADO:
  La obra pasa directamente a READY_FOR_PUBLISH
  sin gastar una sola llamada externa.
```

---

## 7. PASO 2 — Proveedores Especializados

### 7.1 Estrategia por Categoría

| Categoría | Proveedor 1 | Proveedor 2 | Fallback |
|-----------|-------------|-------------|----------|
| Películas | TMDb | Wikidata | Wikipedia |
| Series | TMDb | TVMaze | Wikidata |
| Anime | AniList | TMDb | Wikidata |
| Doramas | TMDb | Wikidata | Wikipedia |
| Novelas | Wikidata | Wikipedia | - |
| Animadas | TMDb | Wikidata | - |
| Concursos | Wikidata | Wikipedia | TMDb |

### 7.2 TMDb

```text
ENDPOINTS:
  GET /search/movie?query={title}&year={year}
  GET /search/tv?query={title}&first_air_date_year={year}

MATCH:
  - Si título coincide (exacto o fuzzy > 0.85) Y año coincide → MATCH
  - Si título coincide pero año difiere por 1 → MATCH PROBABLE
  
CREDENCIALES:
  - API Key desde .env: TMDB_API_KEY
  - Rate limit: 40 requests/10s
```

### 7.3 AniList

```text
ENDPOINT: POST https://graphql.anilist.co

QUERY: search Media by title (romaji, native, english), type: ANIME

CREDENCIALES:
  - Client ID/Secret desde .env
  - Rate limit: 90 requests/min
```

### 7.4 TVMaze

```text
ENDPOINT: GET /search/shows?q={title}

CREDENCIALES:
  - No requiere API key
  - Rate limit: 20 requests/min (conservador)
```

---

## 8. PASO 3 — Búsqueda Web

### 8.1 Cuándo Usar

```text
SOLO cuando:
  - Proveedores especializados NO encontraron la obra
  - O encontraron candidatos ambiguos
  - O la categoría no tiene proveedor especializado

NUNCA como primer recurso.
```

### 8.2 Cadena de Proveedores Web

```text
ORDEN: Tavily → Serper → Exa

ESCALA AL SIGUIENTE CUANDO:
  - Fallo de conexión, Timeout (> 10s), Rate limit
  - Cuota agotada, Circuit breaker activo
  - Resultado vacío, Evidencia insuficiente
```

### 8.3 Tavily

```text
USO: Búsqueda web general como primer fallback.

QUERY: "¿Qué película es '{title}' del año {year}?"

CREDENCIALES:
  - API Key desde .env: TAVILY_API_KEY
```

---

## 9. PASO 4 — BrowserSearchProvider

### 9.1 Cuándo Usar

```text
SOLO cuando:
  - Proveedores especializados fallaron
  - Búsqueda web no dio evidencia suficiente

ES EL ÚLTIMO RECURSO antes de la IA.
```

### 9.2 Tecnología

```text
Playwright + Chromium (headless)

El navegador:
  - NO decide qué obra es
  - SOLO recolecta evidencia
  - Busca en Google/Bing
  - Extrae texto visible de resultados
```

### 9.3 CAPTCHA y Bloqueos

```text
DETECCIÓN:
  - Texto "unusual traffic" o "verify you are not a robot"
  - HTTP 429 (Too Many Requests)

ACCIÓN:
  ❌ NUNCA intentar evadir el CAPTCHA
  ✅ Registrar el evento
  ✅ Aplicar cooldown (5-10 minutos)
  ✅ Cambiar a otro proveedor
  ✅ Si todos fallan → HUMAN_REVIEW
```

---

## 10. PASO 5 — Análisis IA

### 10.1 Qwen 2.5 3B Local (vía Ollama)

```text
ROL: Analizar evidencia recogida. NO es fuente de información.

ENTRADA:
  - Evidencia local (títulos, año, categoría)
  - Resultados de APIs (snippet, URLs, datos)
  - Resultados de navegador (texto extraído)

SALIDA ESPERADA (JSON estricto):
  {
    "status": "matched",
    "canonical_title": "The Runner",
    "year": 2015,
    "media_type": "film",
    "confidence": 0.98,
    "matched_sources": ["tmdb", "tavily"],
    "recommended_action": "accept"
  }
```

### 10.2 Reglas para la IA

```text
1. La IA SOLO analiza evidencia entregada.
2. La IA NUNCA inventa URLs.
3. La IA NUNCA inventa metadatos.
4. La IA NO tiene autoridad final. El validador decide.
```

### 10.3 Protección Contra Fuentes Inventadas

```text
VALIDACIÓN POST-IA:
  1. Extraer todas las URLs del JSON de respuesta
  2. Comparar con URLs presentes en la evidencia
  3. Si hay URL que NO está en evidencia:
     → hallucinated_source = true
     → RECHAZAR resultado
     → Escalar a Groq o HUMAN_REVIEW
```

### 10.4 Groq como Fallback

```text
MODELO: gpt-oss-120b

CUÁNDO USAR GROQ:
  - Ollama no disponible
  - Timeout de Qwen (> 120 segundos)
  - JSON inválido de Qwen
  - Baja confianza (< 0.5)
  - URL alucinada por Qwen

FLUJO:
  Qwen → ¿OK? → Validador
  Qwen → ¿Fallo? → Groq → ¿OK? → Validador
  Groq → ¿Fallo? → HUMAN_REVIEW
```

---

## 11. PASO 6 — Validador Determinista

### 11.1 Autoridad Final

```text
LA IA PROPONE. EL VALIDADOR DECIDE.

Flujo:
  IA produce JSON → Parse JSON → Validar schema → 
  Validar fuentes → Validar coherencia → 
  Validador determinista → accept/partial_accept/escalate/reject
```

### 11.2 Criterios del Validador

```text
ACCEPTA si:
  - JSON válido, Schema correcto, No URLs inventadas
  - confidence ≥ 0.7, Al menos 1 external_id confirmado
  - Título y año coherentes

ACEPTA_PARCIAL si:
  - confidence entre 0.5 y 0.7
  - Faltan campos secundarios (poster, reparto)

ESCALA (a HUMAN_REVIEW) si:
  - confidence < 0.5
  - Múltiples candidatos similares
  - Contradicciones entre fuentes

RECHAZA si:
  - JSON inválido, URLs inventadas
  - Año fuera de rango (1888-2030)
  - Título vacío, Ninguna fuente confirma identidad
```

---

## 12. Enriquecimiento Parcial

### 12.1 Concepto

```text
MCE NO necesita una ficha completa de una sola fuente.

CAMPOS OBLIGATORIOS (para APPROVED):
  ✅ original_title, year, category/type
  ✅ Al menos 1 external_id (TMDb, IMDb, AniList, Wikidata)

CAMPOS DESEADOS:
  ☐ spanish_title, alternative_titles, genres
  ☐ director/creator, main_cast, synopsis
  ☐ rating, runtime_minutes, poster URL

REGLA:
  Si tiene OBLIGATORIOS + 5+ DESEADOS → APPROVED
  Si tiene OBLIGATORIOS + 2-4 DESEADOS → APPROVED_PARTIAL
  Si tiene OBLIGATORIOS + <2 DESEADOS → continuar enriqueciendo
  Si NO tiene OBLIGATORIOS → NO aprobar

NUNCA inventar datos para completar la ficha.
```

---

## 13. Cola de Revisión Humana

### 13.1 Cuándo Va a Revisión

```text
Una obra va a HUMAN_REVIEW cuando:
  - Ningún proveedor la encontró
  - Hay múltiples candidatos con confianza similar
  - La IA no pudo decidir
  - El título es demasiado ambiguo
  - Hay contradicciones entre fuentes
  - El validador rechazó el resultado
```

### 13.2 Decisiones del Usuario

```text
CUANDO EL USUARIO DECIDE:
  1. Se registra en mce_cache.human_corrections
  2. Se genera alias forzado si es necesario
  3. La obra pasa a READY_FOR_PUBLISH
  4. La próxima vez, PREPARE usará esa corrección automáticamente
```

---

## 14. Workers y Concurrencia

### 14.1 Configuración

```text
ENRICH workers: 2-3 threads (Network bound)

BACKPRESSURE:
  - Cola máxima: 50 obras esperando
  - Si cola > 50 → pausar PREPARE
  - Semáforo global: máximo 3 llamadas HTTP simultáneas
```

### 14.2 Rate Limiting

```text
POR PROVEEDOR (configurable):
  TMDb: 40 req/10s | AniList: 90 req/min
  TVMaze: 20 req/min | Wikidata: 100 req/min

SI SE ALCANZA EL LÍMITE:
  1. Pausar ese proveedor
  2. Continuar con el siguiente
  3. Reanudar cuando pase cooldown
```

### 14.3 Checkpointing

```text
GUARDAR PROGRESO:
  - Cada 20 obras enriquecidas
  - Cada 60 segundos
  - Antes de cada llamada a IA

REANUDACIÓN:
  - Leer último checkpoint
  - Saltar obras ya terminadas
  - No repetir llamadas cacheadas
```

---

## 15. UI de ENRICH

```text
┌─────────────────────────────────────────────────────────┐
│  🔍 ENRICH                                  🟣 Púrpura   │
│                                                         │
│  Progreso: ████████░░░░ 78%  (6,870 / 8,807)           │
│                                                         │
│  ┌─ OBRA ACTUAL ─────────────────────────────────┐     │
│  │  "El Corredor" - Consultando TMDb... (2.3s)   │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌─ PROVEEDORES ──────────────────────────────────┐     │
│  │  TMDb:     4,521/5,000  ████████████░  90%    │     │
│  │  AniList:  1,203/2,000  ██████░░░░░░░  60%    │     │
│  │  Tavily:     89/200     ████░░░░░░░░░  44%    │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌─ RESULTADOS ───────────────────────────────────┐     │
│  │  ✅ Aprobadas: 5,420  ⚠️ Parciales: 890        │     │
│  │  👤 Review: 340       ❌ Not Found: 120        │     │
│  │  💾 Cache Hits: 2,100                          │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  [ ENVIAR A PUBLICAR → ]                                │
└─────────────────────────────────────────────────────────┘
```

---

## 16. Métricas y Logging

### 16.1 Métricas por Obra

```text
- logical_work_id, Duración total (ms)
- Proveedores consultados, Llamadas por proveedor
- Cache hits/misses, Estado final
- Confianza de identidad, Completitud de metadatos
```

### 16.2 Métricas Globales

```text
- Total obras procesadas, Llamadas por proveedor
- Cache hit rate global, Tasa de éxito por proveedor
- Tiempo promedio por obra
- Obras resueltas localmente (sin APIs)
- Obras en revisión humana, Errores por tipo
```

---

## 17. Casos de Test Críticos

| # | Caso | Esperado |
|---|------|----------|
| 1 | Cache HIT entre bancos | No consulta APIs, reutiliza metadata |
| 2 | Título ambiguo "Crash" | Va a HUMAN_REVIEW, no elige aleatorio |
| 3 | Provider failure (HTTP 500) | Circuit breaker, fallback, DLQ |
| 4 | IA inventa URL | Validador rechaza, escala a Groq |
| 5 | Enriquecimiento parcial | APPROVED_PARTIAL, no inventa datos |
| 6 | Reanudación tras crash | Lee checkpoint, no repite llamadas |
| 7 | PREPARE_INSUFFICIENT | No gasta APIs, va a review |
| 8 | Idempotencia | Segunda ejecución = cache HIT |

---

## 18. Dependencias

| Dependencia | Uso |
|-------------|-----|
| `mce_staging` | Leer PreparedWorkPackage, escribir EnrichedWorkPackage |
| `mce_cache.*` | Provider responses, global_works, wikidata, assets |
| TMDb API | Películas/series |
| AniList API | Anime |
| TVMaze API | Series (fallback) |
| Wikidata/Wikipedia | Complementario |
| Tavily/Serper/Exa | Búsqueda web (fallback) |
| Ollama (Qwen 2.5 3B) | Análisis IA local |
| Groq API | Análisis IA remoto (fallback) |
| Playwright + Chromium | BrowserSearchProvider |

---

## 19. Lo que ENRICH NUNCA Hace

1. ❌ No escribe en `mce_master`.
2. ❌ No inventa metadatos.
3. ❌ No gasta APIs si la cache ya resolvió.
4. ❌ No procesa por archivo, solo por obra lógica.
5. ❌ No inicia PUBLISHER automáticamente.
6. ❌ No usa búsqueda web como primer recurso.
7. ❌ No permite que la IA tenga autoridad final.
8. ❌ No acepta URLs inventadas por la IA.
9. ❌ No consulta los 3 proveedores web simultáneamente.
10. ❌ No intenta evadir CAPTCHAs.

---

> **Documento mantenido por:** Qwen Code
> **Revisión requerida si:** Se modifican proveedores, cadena de enriquecimiento, o reglas de validación.
> **Siguiente documento:** `instrucciones/06_PUBLISHER_SPEC.md`
