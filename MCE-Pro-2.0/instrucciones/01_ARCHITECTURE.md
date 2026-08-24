# 01_ARCHITECTURE - Arquitectura Oficial MCE Pro 2.0

> **Estado**: OFICIAL  
> **Versión**: 2.0  
> **Última actualización**: 2025-12-24  
> **Agente responsable**: Qwen Code

---

## 1. Visión General

MCE Pro 2.0 es un sistema de ingeniería de datos que transforma escaneos brutos de múltiples bancos multimedia en un Catálogo Maestro PostgreSQL confiable, utilizando procesamiento local con Wikipedia/Wikidata como primera capa, proveedores especializados como segunda, búsqueda web e IA como último recurso, con validación determinista, publicación transaccional con rollback, y una capa de consumo vía Query Service para Telegram Bot y Mini App.

## 2. Principios Fundamentales

1. **El legacy NUNCA se modifica**. Es solo referencia.
2. **MSL es la fuente de datos brutos**. VALIDATE no inventa datos.
3. **Solo PUBLISHER escribe en mce_master**. Ningún otro módulo.
4. **bank_id NUNCA se pierde**. Está presente en todo el pipeline.
5. **logical_work_id identifica una obra única**. No el filename.
6. **Los contratos son explícitos y versionados**. No se inventan campos.
7. **PUBLISHER siempre ejecuta PREFLIGHT**. Antes de cualquier escritura.
8. **Publicación transaccional**. Lotes con rollback.
9. **Rollback auditable**. Cada publicación se puede revertir.
10. **Cada módulo puede sobrevivir a un apagón**. Checkpointing.
11. **La IA analiza evidencia**. NUNCA inventa. El validador decide.
12. **No gastar APIs si la caché ya resolvió**. Idempotencia.
13. **Buscar una vez por obra lógica**. No una vez por archivo.
14. **Una identificación incorrecta es peor que una obra pendiente**.
15. **Los datos intermedios se persisten**. No se pasan objetos en memoria entre módulos.
16. **Los botones de UI son transiciones controladas**. Cambian estado persistido.
17. **Tests NUNCA tocan bases de datos de producción**. Usar mce_test.
18. **API Keys NUNCA en código ni en Git**. Usar .env.
19. **Preparar no inicia Enriquecer automáticamente**. El usuario decide.
20. **El repositorio es la memoria permanente**. No las conversaciones.

---

## 3. Arquitectura de Datos (PostgreSQL — 4 Bases de Datos)

### 3.1 mce_staging (TEMPORAL)

**Propósito**: Datos del pipeline actual.

**Contenido**: Contratos entre módulos, estados de obras, checkpoints.

**Ciclo de vida**: Se limpia al finalizar un pipeline completo.

**Permite**: Reanudación tras apagones o cierres.

### 3.2 mce_cache (PERMANENTE)

**Propósito**: Datos reutilizables entre bancos y entre ejecuciones.

**Contenido**:
- provider_cache: Respuestas de TMDb, AniList, TVMaze, etc.
- global_work_cache: Obras ya identificadas (metadata universal).
- wikimedia_cache: Respuestas de Wikipedia/Wikidata.
- asset_cache: URLs de posters/backdrops.
- human_corrections: Memoria de correcciones humanas (aliases forzados).

**Ciclo de vida**: Persistente. Nunca se limpia automáticamente.

**Regla**: Si Banco A ya identificó Avatar, Banco B NO vuelve a consultar TMDb.

### 3.3 mce_master (SAGRADO)

**Propósito**: Catálogo Maestro final.

**Contenido**: Obras, alias, metadatos, disponibilidad por banco, assets.

**Acceso de escritura**: SOLO el módulo PUBLISHER.

**Acceso de lectura**: Query Service.

**Regla**: Nunca se borra una obra. Si ya no está disponible, se marca como ARCHIVED.

### 3.4 mce_app (USUARIOS / BOT)

**Propósito**: Datos de usuarios y funcionalidades del Bot/Mini App.

**Contenido**:
- Usuarios de Telegram.
- Wishlists (lista de deseos).
- Historial de visualización.
- Solicitudes (Quiero que suban X obra).
- Notificaciones pendientes.

**Regla**: NUNCA mezclar con mce_master. Son dominios separados.

---

## 4. Los 4 Módulos del Pipeline

### 4.1 VALIDATE

| Aspecto | Detalle |
|---------|---------|
| **Misión** | Validar que el JSON de MSL es estructuralmente correcto |
| **Entrada** | JSON crudo de MSL (importado vía botón en UI) |
| **Salida** | ValidatedScanPackage |
| **UI** | Botón [ IMPORTAR JSON DE MSL ] + Botón [ IMPORTAR CARPETA ] |

**Responsabilidades**:
- Leer y parsear el JSON.
- Validar presencia de bank_id.
- Detectar categoría (Películas, Series, Novelas, Anime, Doramas, Animadas, Concursos).
- Calcular snapshot: nuevos, modificados, sin cambios, ausentes.
- Detectar anomalías (JSON corrupto, estructura inválida).
- Detectar borrados (delta inverso): archivos que estaban antes pero ya no están.

**Lo que NO hace**:
- No modifica datos.
- No agrupa obras.
- No consulta APIs externas.

### 4.2 PREPARE

| Aspecto | Detalle |
|---------|---------|
| **Misión** | Purificar, filtrar, normalizar y agrupar en Obras Lógicas Únicas |
| **Entrada** | ValidatedScanPackage |
| **Salida** | PreparedWorkPackage |
| **Tipo de trabajo** | CPU bound (parsing, agrupación) |

**Responsabilidades**:
- Filtrado: Separar contenido real de ruido (trailers, subs, .nfo, etc.).
- Normalización de títulos: Eliminar ruido técnico (1080p, x264, BluRay, etc.) sin destruir títulos numéricos legítimos (1917, 2001, Blade Runner 2049).
- Agrupación: Detectar que múltiples archivos/carpetas pertenecen a la misma obra lógica.
- Wikimedia (Wikipedia + Wikidata): Consultar para reducir ambigüedad ANTES de gastar APIs comerciales.
- Clasificación: Película, Serie, Novela, Anime, Dorama, Animada, Concurso. Ante duda: CLASSIFICATION_REVIEW.
- Conteo por obras únicas: No por archivos.

**Lo que NO hace**:
- No identifica definitivamente la obra (eso es ENRICH).
- No consulta TMDb, AniList, etc.
- No escribe en mce_master.

### 4.3 ENRICH

| Aspecto | Detalle |
|---------|---------|
| **Misión** | Identificar la obra y completar metadatos con mínimo de llamadas |
| **Entrada** | PreparedWorkPackage |
| **Salida** | EnrichedWorkPackage |
| **Tipo de trabajo** | Network bound (llamadas HTTP) |

**Cadena de Enriquecimiento (por orden)**:
1. mce_cache (global_work_cache) → ¿Ya identificada antes?
2. Wikimedia (Wikipedia + Wikidata) → Gratis, sin rate limit
3. TMDb → Películas, Series, Animadas
4. AniList → Anime
5. TVMaze → Series (fallback)
6. Tavily/Serper/Exa → Búsqueda web para casos ambiguos
7. Groq/Qwen → Análisis de evidencia (último recurso)

**Estados de salida**:
- APPROVED: Obra completamente identificada y enriquecida.
- APPROVED_PARTIAL: Obra identificada pero faltan campos secundarios.
- HUMAN_REVIEW: Ambigüedad. Va a cola de revisión humana.
- NOT_FOUND: No se encontró evidencia suficiente.
- PREPARE_INSUFFICIENT: Datos de entrada demasiado pobres para intentar.

**Lo que NO hace**:
- No escribe en mce_master.
- No inventa metadatos.
- No gasta APIs si la caché ya resolvió.
- No procesa por archivo, procesa por obra lógica.

### 4.4 PUBLISHER

| Aspecto | Detalle |
|---------|---------|
| **Misión** | Único guardián del Catálogo Maestro |
| **Entrada** | EnrichedWorkPackage (solo APPROVED o APPROVED_PARTIAL) |
| **Salida** | PublishCommand → Escritura en mce_master |
| **Tipo de trabajo** | DB bound (transacciones PostgreSQL) |

**Responsabilidades**:
1. Preflight Checks: Validar contrato completo, contenido, conflictos.
2. Deduplicación Final: Buscar por external_ids y original_title + year + category.
3. Publicación Transaccional: Lotes de 100-500 obras con ROLLBACK.
4. Rollback Auditable: Cada publicación genera publish_id.
5. Assets: Verificar poster/backdrop, usar placeholders si necesario.
6. Sync de Borrados: Eliminar bank_id de disponibilidad.
7. Conflictos: Datos dinámicos se actualizan, estables van a PUBLISH_CONFLICT.

**Lo que NO hace**:
- No enriquece.
- No identifica.
- No consulta APIs externas.
- No modifica mce_cache ni mce_staging.

---

## 5. Servicios Transversales

### 5.1 Config Service
- API Keys en .env
- Provider Config en providers.yaml
- Worker Config en workers.yaml
- Feature Flags

### 5.2 Observability
- Structured Logging
- Barras de Progreso en UI
- Panel de Errores en Tiempo Real
- Panel de Llamadas a Proveedores

### 5.3 API Budget Manager
- Límites diarios por proveedor
- Priority Queue (HIGH/MEDIUM/LOW)
- Fallback Chain

### 5.4 Workers
- validate: 2-4 threads (I/O bound)
- prepare: 4-8 threads (CPU bound)
- enrich: 2-3 threads (Network bound)
- publisher: 1-2 threads (DB bound)
- ai_analysis: 1 thread (Secuencial)
- asset_downloader: 2 threads (I/O bound)

### 5.5 Checkpointing
- Save interval: 60 segundos
- Pipeline ID único
- Reanudación automática
- Max 10 checkpoints

### 5.6 Graceful Degradation
- Sin Internet: PREPARE sigue, ENRICH pausa
- Sin Ollama/Qwen: Salta IA
- Sin PostgreSQL: Pausa todo
- Proveedor caído: Circuit breaker + fallback

---

## 6. Capa de Consumo

### 6.1 Query Service
API de lectura que abstrae mce_master y mce_app.

### 6.2 Telegram Bot
Catálogo visual, búsqueda, ficha de obra, wishlist.

### 6.3 Mini App
Interfaz visual tipo Netflix.

---

## 7. Estrategia de Wikipedia/Wikidata

**Objetivo**: Reducir al máximo las obras que necesitan APIs comerciales.

**Meta**: 40% de obras resueltas localmente sin gastar APIs comerciales.

---

## 8. Estrategia Multi-Banco

**Principio**: Obra canónica global + disponibilidad por banco.

---

## 9. UI — MCE Suite

5 Paneles: Validar (Azul), Preparar (Verde), Enriquecer (Púrpura), Publicar (Naranja), Revisión Humana (Rojo).

---

## 10. Contratos entre Módulos

RawScanPackage → ValidatedScanPackage → PreparedWorkPackage → EnrichedWorkPackage → PublishCommand

---

## 11. Estado de Máquina

RAW → VALIDATED → PREPARED → ENRICHED → PUBLISHED

Excepciones: VALIDATION_ERROR, PREPARATION_ERROR, HUMAN_REVIEW, NOT_FOUND, PUBLISH_CONFLICT

---

## 12. Backup y Disaster Recovery

- Daily full backup de mce_master y mce_cache
- WAL archiving
- Publisher Audit Trail

---

## 13. Testing Strategy

Unit tests, Integration tests, Contract tests, E2E tests, Load tests.

---

## 14. Migración del Legacy

Reutilizar: JSON crudos, código funcional, configuración.
NO reutilizar: Datos enriquecidos, BD antigua, arquitectura antigua.

---

## 15. Reglas Inquebrantables (La Constitución)

20 reglas fundamentales del proyecto.

---

## 16. Diseño para el Futuro

Plugin System, Event-Driven Architecture.

---

## 17. Resumen en una Frase

MCE Pro 2.0 es un sistema de ingeniería de datos que transforma escaneos brutos de múltiples bancos multimedia en un Catálogo Maestro PostgreSQL confiable, utilizando procesamiento local con Wikipedia/Wikidata como primera capa, proveedores especializados como segunda, búsqueda web e IA como último recurso, con validación determinista, publicación transaccional con rollback, y una capa de consumo vía Query Service para Telegram Bot y Mini App.
