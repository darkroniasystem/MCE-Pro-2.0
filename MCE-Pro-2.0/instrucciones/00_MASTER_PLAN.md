# 📋 MCE Pro 2.0 — Plan Maestro

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Repositorio:** MCE-Pro-2.0 (GitHub)

---

## 1. Visión del Proyecto

**MCE Pro 2.0** es un sistema de ingeniería de datos que transforma escaneos brutos de múltiples bancos multimedia en un Catálogo Maestro PostgreSQL confiable.

### Objetivo Final

```text
ENTRADA:
  Discos, servidores y bancos de contenido con cientos de miles
  de archivos con nombres inconsistentes, estructuras caóticas
  y formatos diversos.

PROCESO:
  MSL escanea → MCE valida → MCE prepara → MCE enriquece → MCE publica

SALIDA:
  Un Catálogo Maestro estructurado, normalizado, deduplicado y
  enriquecido que alimenta:
    - Telegram Bot (catálogo visual + wishlist)
    - Mini App (Trocadero363)
    - API (futuro)
```

### Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| Obras procesadas | > 100,000 sin crash |
| Cache Hit Rate | > 70% |
| Resolución local (sin APIs) | > 40% |
| Llamadas promedio por obra | < 3 |
| Tiempo para 100K obras | < 24 horas |
| RAM máxima | 4 GB |
| Identificaciones incorrectas | 0 (preferimos obras sin identificar) |
| Disponibilidad del sistema | 100% durante procesamiento |

---

## 2. Arquitectura de Referencia

```text
MSL (Media Scanner Local)
         │
         │ JSON crudo
         ▼
┌─────────────────────────────────────────────────────────┐
│                    MCE SUITE                             │
│                                                         │
│  VALIDATE → PREPARE → ENRICH → PUBLISHER               │
│                                                         │
│  Cross-cutting:                                         │
│  Config, Observability, API Budget, Workers,            │
│  Checkpointing, Graceful Degradation, Error Recovery,   │
│  Content Validation, Security, Notifications,           │
│  Disk Management, Asset Management, Human Review Memory │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL                                             │
│  ├── mce_staging  (temporal)                            │
│  ├── mce_cache    (permanente)                          │
│  ├── mce_master   (sagrado)                             │
│  └── mce_app      (usuarios/bot)                        │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  QUERY SERVICE                                          │
│  ├── Telegram Bot (catálogo + wishlist)                 │
│  ├── Mini App (Trocadero363)                            │
│  └── API (futuro)                                       │
└─────────────────────────────────────────────────────────┘
```

**Detalle completo:** Ver `instrucciones/01_ARCHITECTURE.md`

---

## 3. Fases del Proyecto

### Vista General

```text
FASE 0 ──→ FASE 1 ──→ FASE 2 ──→ FASE 3 ──→ FASE 4 ──→ FASE 5
Fundación  Contratos  Módulos    Pipeline   UI/UX     Consumo
```

---

### FASE 0 — Fundación

**Objetivo:** Establecer la base del proyecto. Sin código funcional aún, pero con toda la documentación, estructura y configuración lista.

**Entregables:**

| # | Entregable | Archivo | Estado |
|---|-----------|---------|--------|
| 1 | Estructura de carpetas del repo | Todo el repo | ✅ Completado |
| 2 | Arquitectura oficial | `instrucciones/01_ARCHITECTURE.md` | ✅ Completado |
| 3 | Contratos entre módulos | `instrucciones/02_CONTRACTS.md` | ✅ Completado |
| 4 | Modelo de datos | `instrucciones/03_DATA_MODEL.md` | ✅ Completado |
| 5 | Spec de PREPARE | `instrucciones/04_PREPARE_SPEC.md` | ✅ Completado |
| 6 | Spec de ENRICH | `instrucciones/05_ENRICH_SPEC.md` | ✅ Completado |
| 7 | Spec de PUBLISHER | `instrucciones/06_PUBLISHER_SPEC.md` | ✅ Completado |
| 8 | Spec de VALIDATE | `instrucciones/07_VALIDAR_SPEC.md` | ✅ Completado |
| 9 | Spec de UI | `instrucciones/08_UI_SPEC.md` | ✅ Completado |
| 10 | Estrategia de testing | `instrucciones/09_TESTING.md` | ✅ Completado |
| 11 | Reutilización del legacy | `instrucciones/10_LEGACY_REUSE.md` | ✅ Completado |
| 12 | Plan maestro | `instrucciones/00_MASTER_PLAN.md` | ✅ Completado |
| 13 | Estado actual | `CURRENT_WORK.md` | ✅ Completado |
| 14 | Configuración de proyecto | `pyproject.toml` | ✅ Completado |
| 15 | Configuración de proveedores | `config/providers.yaml` | ✅ Completado |
| 16 | Configuración de workers | `config/workers.yaml` | ✅ Completado |
| 17 | Plantilla de variables de entorno | `.env.example` | ✅ Completado |
| 18 | Gitignore | `.gitignore` | ✅ Completado |
| 19 | CI/CD pipeline | `.github/workflows/ci.yml` | ✅ Completado |
| 20 | Instrucciones para Qwen | `QWEN.md` | ✅ Completado |
| 21 | README del proyecto | `README.md` | ✅ Completado |

**Criterios de Completado:**
- [x] Todos los documentos de `instrucciones/` creados y completos
- [x] Estructura de carpetas creada en GitHub
- [x] Configuración de proyecto definida
- [x] CI/CD pipeline configurado
- [x] QWEN.md con reglas para el agente
- [x] MCE_CONTRACTS.md (reglas inquebrantables) definido

**Duración estimada:** 1-2 días

---

### FASE 1 — Contratos y Shared Kernel

**Objetivo:** Implementar los contratos JSON Schema y el paquete compartido (`src/shared/`). Todo lo que los módulos necesitan para comunicarse.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | JSON Schema: RawScanPackage | `contracts/raw_scan_package.json` |
| 2 | JSON Schema: ValidatedScanPackage | `contracts/validated_scan_package.json` |
| 3 | JSON Schema: PreparedWorkPackage | `contracts/prepared_work_package.json` |
| 4 | JSON Schema: EnrichedWorkPackage | `contracts/enriched_work_package.json` |
| 5 | JSON Schema: PublishCommand | `contracts/publish_command.json` |
| 6 | Enums globales (categorías, estados, proveedores) | `src/shared/enums.py` |
| 7 | Modelos Pydantic de contratos | `src/shared/models.py` |
| 8 | Validador de contratos | `src/shared/validators.py` |
| 9 | State machine | `src/shared/state_machine.py` |
| 10 | Config loader | `src/shared/config.py` |
| 11 | Error types | `src/shared/errors.py` |
| 12 | Logging structured | `src/shared/logging.py` |
| 13 | Tests de contratos | `tests/contracts/` |
| 14 | Tests de shared | `tests/unit/shared/` |

**Criterios de Completado:**
- [ ] 5 JSON Schemas válidos y completos
- [ ] Modelos Pydantic que validan contra los schemas
- [ ] State machine con todas las transiciones
- [ ] 100% de tests de contratos pasando
- [ ] Cobertura de shared ≥ 90%
- [ ] Ruff limpio
- [ ] MyPy limpio

**Duración estimada:** 2-3 días

---

### FASE 2 — VALIDATE

**Objetivo:** Implementar el módulo VALIDATE completo.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | JSON parser (con streaming para archivos grandes) | `src/validar/parser.py` |
| 2 | Validación estructural | `src/validar/structural.py` |
| 3 | Validación de contenido | `src/validar/content.py` |
| 4 | Detección de categoría | `src/validar/category.py` |
| 5 | Snapshot y delta | `src/validar/snapshot.py` |
| 6 | Detección de anomalías | `src/validar/anomalies.py` |
| 7 | Clasificación de registros | `src/validar/classifier.py` |
| 8 | Generación de ValidatedScanPackage | `src/validar/pipeline.py` |
| 9 | Workers de VALIDATE | `src/validar/workers.py` |
| 10 | Tests unitarios | `tests/unit/validar/` |
| 11 | Tests de integración | `tests/integration/validar/` |

**Dependencias:** FASE 1 (contratos y shared)

**Criterios de Completado:**
- [ ] JSON válido produce ValidatedScanPackage correcto
- [ ] JSON corrupto se rechaza con error claro
- [ ] Sin bank_id se rechaza
- [ ] Snapshot se calcula correctamente
- [ ] Delta inverso detecta archivos eliminados
- [ ] Anomalías se detectan y clasifican
- [ ] Registros se clasifican (MEDIA, SUBTITLE, NOISE, etc.)
- [ ] Categoría se detecta correctamente
- [ ] Tests unitarios ≥ 85% cobertura
- [ ] Tests de integración pasando
- [ ] Ruff limpio, MyPy limpio

**Duración estimada:** 3-4 días

---

### FASE 3 — PREPARE

**Objetivo:** Implementar el módulo PREPARE completo.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | Filtrado de ruido | `src/prepare/filter.py` |
| 2 | Limpieza de títulos | `src/prepare/cleaner.py` |
| 3 | Protección de títulos numéricos | `src/prepare/numeric_titles.py` |
| 4 | Regla carpeta > filename | `src/prepare/folder_priority.py` |
| 5 | Agrupación de series | `src/prepare/series_grouper.py` |
| 6 | Manejo de DVD/VOB | `src/prepare/dvd_handler.py` |
| 7 | Integración Wikimedia | `src/prepare/wikimedia.py` |
| 8 | Clasificación | `src/prepare/classifier.py` |
| 9 | Generación de PreparedWorkPackage | `src/prepare/pipeline.py` |
| 10 | Workers de PREPARE | `src/prepare/workers.py` |
| 11 | Tests unitarios | `tests/unit/prepare/` |
| 12 | Tests de integración | `tests/integration/prepare/` |

**Dependencias:** FASE 1, FASE 2

**Criterios de Completado:**
- [ ] Ruido filtrado correctamente (trailers, subs, .nfo, noise)
- [ ] Títulos limpios sin destruir información
- [ ] Títulos numéricos protegidos (1917, 2049, District 9)
- [ ] Carpeta contenedora tiene prioridad sobre filename
- [ ] Series agrupadas correctamente (200 episodios = 1 obra)
- [ ] Temporadas dispersas agrupadas
- [ ] DVD/VOB manejados correctamente
- [ ] Wikimedia consultado y cacheado
- [ ] Clasificación correcta por categoría
- [ ] Conteo por obras únicas, no archivos
- [ ] Tests unitarios ≥ 85% cobertura
- [ ] Tests de integración pasando
- [ ] Ruff limpio, MyPy limpio

**Duración estimada:** 5-7 días

---

### FASE 4 — ENRICH

**Objetivo:** Implementar el módulo ENRICH completo.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | Caché global (lookup y storage) | `src/enrich/cache.py` |
| 2 | Cliente TMDb | `src/enrich/providers/tmdb.py` |
| 3 | Cliente AniList | `src/enrich/providers/anilist.py` |
| 4 | Cliente TVMaze | `src/enrich/providers/tvmaze.py` |
| 5 | Cliente Wikidata/Wikipedia | `src/enrich/providers/wikimedia.py` |
| 6 | Cadena de proveedores por categoría | `src/enrich/provider_chain.py` |
| 7 | Cliente Tavily (web search) | `src/enrich/providers/tavily.py` |
| 8 | Cliente Serper (web search) | `src/enrich/providers/serper.py` |
| 9 | Cliente Exa (web search) | `src/enrich/providers/exa.py` |
| 10 | BrowserSearchProvider (Playwright) | `src/enrich/browser/` |
| 11 | Analizador Qwen (Ollama) | `src/enrich/ai/qwen.py` |
| 12 | Analizador Groq (fallback) | `src/enrich/ai/groq.py` |
| 13 | Validador determinista | `src/enrich/validator.py` |
| 14 | Generación de EnrichedWorkPackage | `src/enrich/pipeline.py` |
| 15 | Workers de ENRICH + backpressure | `src/enrich/workers.py` |
| 16 | Rate limiter | `src/enrich/rate_limiter.py` |
| 17 | Circuit breaker | `src/enrich/circuit_breaker.py` |
| 18 | Tests unitarios | `tests/unit/enrich/` |
| 19 | Tests de integración | `tests/integration/enrich/` |

**Dependencias:** FASE 1, FASE 2, FASE 3

**Criterios de Completado:**
- [ ] Cache global funciona entre bancos
- [ ] TMDb identifica películas correctamente
- [ ] AniList identifica anime correctamente
- [ ] TVMaze funciona como fallback para series
- [ ] Wikimedia complementa identificación
- [ ] Cadena de proveedores respeta prioridades
- [ ] Búsqueda web solo como último recurso
- [ ] BrowserSearchProvider recolecta evidencia
- [ ] Qwen analiza evidencia sin inventar
- [ ] Groq funciona como fallback de Qwen
- [ ] Validador determinista tiene autoridad final
- [ ] URLs inventadas por IA se rechazan
- [ ] Rate limiting funciona
- [ ] Circuit breaker funciona
- [ ] Backpressure funciona
- [ ] Enriquecimiento parcial funciona
- [ ] Procedencia de datos se registra
- [ ] Tests unitarios ≥ 80% cobertura
- [ ] Tests de integración pasando
- [ ] Ruff limpio, MyPy limpio

**Duración estimada:** 7-10 días

---

### FASE 5 — PUBLISHER

**Objetivo:** Implementar el módulo PUBLISHER completo.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | Preflight checks | `src/publisher/preflight.py` |
| 2 | Deduplicación final | `src/publisher/dedup.py` |
| 3 | Publicación transaccional | `src/publisher/transaction.py` |
| 4 | Rollback | `src/publisher/rollback.py` |
| 5 | Sync de borrados (delta inverso) | `src/publisher/deletion_sync.py` |
| 6 | Manejo de conflictos | `src/publisher/conflicts.py` |
| 7 | Asset downloader | `src/publisher/assets.py` |
| 8 | Historial de publicación | `src/publisher/history.py` |
| 9 | Generación de PublishCommand | `src/publisher/pipeline.py` |
| 10 | Workers de PUBLISHER | `src/publisher/workers.py` |
| 11 | Tests unitarios | `tests/unit/publisher/` |
| 12 | Tests de integración | `tests/integration/publisher/` |

**Dependencias:** FASE 1, FASE 2, FASE 3, FASE 4

**Criterios de Completado:**
- [ ] Preflight detecta todos los problemas antes de escribir
- [ ] Deduplicación por external_ids funciona
- [ ] Deduplicación por title+year+category funciona
- [ ] Multi-banco no duplica obras
- [ ] Publicación transaccional con batches
- [ ] Rollback revierte correctamente
- [ ] Delta inverso elimina disponibilidad sin borrar obra
- [ ] Conflictos de datos estables se detectan
- [ ] Assets se descargan y validan
- [ ] Historial se registra
- [ ] Tests unitarios ≥ 90% cobertura
- [ ] Tests de integración pasando
- [ ] Ruff limpio, MyPy limpio

**Duración estimada:** 5-7 días

---

### FASE 6 — Pipeline Completo e Integración

**Objetivo:** Conectar los 4 módulos en un pipeline funcional de extremo a extremo.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | Orquestador del pipeline | `src/pipeline/orchestrator.py` |
| 2 | Checkpointing global | `src/pipeline/checkpointing.py` |
| 3 | Graceful degradation | `src/pipeline/degradation.py` |
| 4 | Error recovery + Dead Letter Queue | `src/pipeline/error_recovery.py` |
| 5 | Observability (logging + métricas) | `src/pipeline/observability.py` |
| 6 | Notification system | `src/pipeline/notifications.py` |
| 7 | Tests E2E | `tests/e2e/` |
| 8 | Tests de carga | `tests/load/` |

**Dependencias:** FASE 2, FASE 3, FASE 4, FASE 5

**Criterios de Completado:**
- [ ] Pipeline completo funciona de MSL a Master
- [ ] Checkpointing permite reanudar tras crash
- [ ] Graceful degradation funciona (sin internet, sin Ollama, etc.)
- [ ] Dead Letter Queue aísla obras fallidas
- [ ] Observability muestra métricas en tiempo real
- [ ] Notificaciones funcionan
- [ ] Tests E2E con samples reales pasando
- [ ] Test de carga con 10,000 obras pasando
- [ ] Idempotencia verificada

**Duración estimada:** 3-5 días

---

### FASE 7 — UI (PySide6)

**Objetivo:** Implementar la interfaz gráfica completa.

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | Ventana principal (Home) | `src/ui/main_window.py` |
| 2 | Panel VALIDATE | `src/ui/panels/validate_panel.py` |
| 3 | Panel PREPARE | `src/ui/panels/prepare_panel.py` |
| 4 | Panel ENRICH | `src/ui/panels/enrich_panel.py` |
| 5 | Panel PUBLISHER | `src/ui/panels/publisher_panel.py` |
| 6 | Panel HUMAN REVIEW | `src/ui/panels/human_review_panel.py` |
| 7 | Dashboard | `src/ui/panels/dashboard.py` |
| 8 | Configuración | `src/ui/panels/settings.py` |
| 9 | Logs viewer | `src/ui/panels/logs.py` |
| 10 | System tray + notificaciones | `src/ui/tray.py` |
| 11 | Temas (oscuro/claro) | `src/ui/themes/` |
| 12 | Tests de UI | `tests/unit/ui/` |

**Dependencias:** FASE 6

**Criterios de Completado:**
- [ ] 5 paneles funcionales con colores correctos
- [ ] Botones de importación funcionan
- [ ] Botones de transición funcionan
- [ ] Barras de progreso en tiempo real
- [ ] Panel de errores en tiempo real
- [ ] Panel de llamadas a proveedores
- [ ] Revisión humana funcional
- [ ] Dashboard con métricas globales
- [ ] Configuración funcional
- [ ] System tray con notificaciones
- [ ] Tema oscuro y claro
- [ ] Atajos de teclado funcionan
- [ ] Diálogos de confirmación para acciones destructivas

**Duración estimada:** 7-10 días

---

### FASE 8 — Query Service y Consumo

**Objetivo:** Implementar la capa de consumo (Bot, Mini App, API).

**Entregables:**

| # | Entregable | Ubicación |
|---|-----------|-----------|
| 1 | Query Service (API de lectura) | `src/query_service/` |
| 2 | Búsqueda full-text | `src/query_service/search.py` |
| 3 | Filtros y paginación | `src/query_service/filters.py` |
| 4 | Integración con Telegram Bot | `src/bot/` |
| 5 | Wishlist | `src/bot/wishlist.py` |
| 6 | Preparación para Mini App | `src/api/` |

**Dependencias:** FASE 5, FASE 6

**Criterios de Completado:**
- [ ] Query Service responde búsquedas correctamente
- [ ] Búsqueda full-text funciona
- [ ] Filtros por género, año, tipo, banco funcionan
- [ ] Paginación funciona
- [ ] Bot responde a búsquedas
- [ ] Wishlist funciona
- [ ] Disponibilidad por banco funciona

**Duración estimada:** 5-7 días

---

### FASE 9 — Pulido y Producción

**Objetivo:** Preparar MCE Pro 2.0 para uso real.

**Entregables:**

| # | Entregable |
|---|-----------|
| 1 | Optimización de rendimiento |
| 2 | Benchmarks finales |
| 3 | Documentación de usuario |
| 4 | Empaquetado con PyInstaller |
| 5 | Backup strategy implementada |
| 6 | Disaster recovery probado |
| 7 | Seguridad auditada |
| 8 | Release 1.0.0 |

**Duración estimada:** 3-5 días

---

## 4. Diagrama de Fases y Dependencias

```text
FASE 0: Fundación
   │
   ▼
FASE 1: Contratos y Shared Kernel
   │
   ├──────────────────────────────────────────┐
   ▼                                          ▼
FASE 2: VALIDATE                    FASE 3: PREPARE
   │                                          │
   └──────────────┬───────────────────────────┘
                  ▼
            FASE 4: ENRICH
                  │
                  ▼
            FASE 5: PUBLISHER
                  │
                  ▼
            FASE 6: Pipeline Completo
                  │
            ┌─────┴─────┐
            ▼           ▼
      FASE 7: UI   FASE 8: Query Service
            │           │
            └─────┬─────┘
                  ▼
            FASE 9: Pulido y Producción
```

---

## 5. Cronograma Estimado

| Fase | Duración | Acumulado |
|------|----------|-----------|
| FASE 0: Fundación | 1-2 días | 1-2 días |
| FASE 1: Contratos | 2-3 días | 3-5 días |
| FASE 2: VALIDATE | 3-4 días | 6-9 días |
| FASE 3: PREPARE | 5-7 días | 11-16 días |
| FASE 4: ENRICH | 7-10 días | 18-26 días |
| FASE 5: PUBLISHER | 5-7 días | 23-33 días |
| FASE 6: Pipeline | 3-5 días | 26-38 días |
| FASE 7: UI | 7-10 días | 33-48 días |
| FASE 8: Query Service | 5-7 días | 38-55 días |
| FASE 9: Pulido | 3-5 días | 41-60 días |

**Total estimado: 6-9 semanas**

---

## 6. Flujo de Trabajo con Qwen

### 6.1 Ciclo por Fase

```text
1. Usuario define objetivo de la fase
2. Qwen lee instrucciones relevantes
3. Qwen implementa código
4. Qwen escribe tests
5. Qwen ejecuta tests
6. Qwen actualiza CURRENT_WORK.md
7. Qwen hace commit + push
8. GitHub Actions verifica (lint, tests, coverage)
9. Usuario revisa en GitHub
10. Usuario aprueba o pide cambios
11. Si hay cambios → Qwen corrige
12. Merge a main
13. Siguiente fase
```

### 6.2 Reglas por Fase

```text
ANTES de cada fase:
  ✅ Leer instrucciones relevantes
  ✅ Leer CURRENT_WORK.md
  ✅ Verificar que la fase anterior está completa
  ✅ Verificar que todos los tests pasan

DURANTE cada fase:
  ✅ Código limpio con type hints
  ✅ Docstrings en todas las funciones públicas
  ✅ Tests escritos junto con el código
  ✅ Commits descriptivos
  ✅ CURRENT_WORK.md actualizado

DESPUÉS de cada fase:
  ✅ Todos los tests pasando
  ✅ Cobertura ≥ umbral mínimo
  ✅ Ruff limpio
  ✅ MyPy limpio
  ✅ CURRENT_WORK.md actualizado
  ✅ Commit final con resumen
```

---

## 7. Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| APIs externas caídas | Media | Alto | Circuit breaker + fallback + graceful degradation |
| PostgreSQL corrupción | Baja | Crítico | Backups diarios + WAL archiving + rollback |
| Memory leak en procesamiento largo | Media | Alto | Checkpointing + monitoreo de RAM + backpressure |
| IA inventa datos | Media | Alto | Validador determinista + verificación de URLs |
| Títulos numéricos se rompen | Media | Medio | Protección explícita + tests específicos |
| DVD/VOB mal manejados | Media | Medio | Tests específicos + reglas explícitas |
| Rate limits de APIs | Alta | Medio | Rate limiter + cache + priority queue |
| Windows update interrumpe | Media | Medio | Checkpointing + reanudación automática |
| Disco lleno | Baja | Alto | Disk management + advertencias + limpieza staging |

---

## 8. Definición de "Done"

Una fase está **DONE** cuando:

```text
✅ Todo el código implementado
✅ Todos los tests pasando
✅ Cobertura ≥ umbral mínimo
✅ Ruff limpio (0 errores)
✅ MyPy limpio (0 errores)
✅ CURRENT_WORK.md actualizado
✅ Commit final con mensaje descriptivo
✅ GitHub Actions pasando
✅ Usuario aprobó el merge
✅ Documentación actualizada si aplica
```

---

## 9. Glosario

| Término | Definición |
|---------|-----------|
| **MSL** | Media Scanner Local. Herramienta que escanea discos y genera JSON |
| **Obra Lógica** | Una obra real (película, serie, etc.) independientemente de cuántos archivos la representen |
| **bank_id** | Identificador externo de un banco de contenido |
| **logical_work_id** | UUID único que identifica una obra lógica en MCE |
| **Pipeline** | Secuencia VALIDATE → PREPARE → ENRICH → PUBLISHER |
| **Contrato** | JSON Schema que define la estructura de datos entre módulos |
| **Preflight** | Validaciones antes de escribir en el Master |
| **Delta inverso** | Detección de archivos que ya no existen en un escaneo |
| **Cache Hit Rate** | Porcentaje de obras resueltas desde cache sin llamar APIs |
| **Dead Letter Queue** | Cola de obras que fallaron tras todos los reintentos |
| **Circuit Breaker** | Mecanismo que pausa un proveedor tras fallos consecutivos |
| **Backpressure** | Control de flujo para no saturar workers |

---

> **Documento mantenido por:** Qwen Code
> **Revisión requerida si:** Se modifican fases, plazos, o criterios de completado.
> **Documento complementario:** `CURRENT_WORK.md`