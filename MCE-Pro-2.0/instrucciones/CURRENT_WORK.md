# 📌 CURRENT WORK — MCE Pro 2.0

> **Última actualización:** 2025
> **Agente activo:** Qwen Code (Web)

---

## Proyecto

**MCE Pro 2.0** — Media Cleaner & Enrichment

## Fase Actual

**FASE 0 — Fundación**

## Estado

🟢 **EN PROGRESO**

---

## Objetivo Actual

Completar la documentación fundacional del proyecto y preparar el repositorio para la implementación de código.

---

## Último Commit

`feat: estructura inicial del proyecto MCE Pro 2.0`

---

## Lo que se ha completado

### Documentación de Instrucciones (100%)

- [x] `instrucciones/00_MASTER_PLAN.md` — Plan maestro con 10 fases (640 líneas) ✅ COMPLETO
- [x] `instrucciones/01_ARCHITECTURE.md` — Arquitectura oficial con 31 mejoras (319 líneas) ✅ COMPLETO
- [x] `instrucciones/02_CONTRACTS.md` — 5 contratos JSON Schema (911 líneas) ✅ COMPLETO
- [x] `instrucciones/03_DATA_MODEL.md` — 4 bases de datos PostgreSQL (976 líneas) ✅ COMPLETO
- [x] `instrucciones/04_PREPARE_SPEC.md` — Especificación de PREPARE (828 líneas) ✅ COMPLETO
- [x] `instrucciones/05_ENRICH_SPEC.md` — Especificación de ENRICH (683 líneas) ✅ COMPLETO
- [x] `instrucciones/06_PUBLISHER_SPEC.md` — Especificación de PUBLISHER (216 líneas) ✅ COMPLETO
- [x] `instrucciones/07_VALIDAR_SPEC.md` — Especificación de VALIDATE (248 líneas) ✅ COMPLETO
- [x] `instrucciones/08_UI_SPEC.md` — Especificación de UI (PySide6, paneles, temas) ✅ COMPLETO
- [x] `instrucciones/09_TESTING.md` — Estrategia de testing (pytest, cobertura, CI/CD) ✅ COMPLETO
- [x] `instrucciones/10_LEGACY_REUSE.md` — Reutilización del legacy (auditoría, clasificación) ✅ COMPLETO

### Configuración del Proyecto

- [x] `pyproject.toml` — Configuración de proyecto
- [x] `config/providers.yaml` — Configuración de proveedores
- [x] `config/workers.yaml` — Configuración de workers
- [x] `.env.example` — Plantilla de variables de entorno
- [x] `.gitignore` — Archivos excluidos de Git
- [x] `.github/workflows/ci.yml` — Pipeline CI/CD
- [x] `QWEN.md` — Instrucciones para Qwen Code
- [x] `README.md` — Documentación del proyecto
- [x] `CURRENT_WORK.md` — Este archivo

### Resumen de Líneas de Documentación

| Documento | Líneas | Estado |
|-----------|--------|--------|
| 00_MASTER_PLAN.md | 640 | ✅ Completo |
| 01_ARCHITECTURE.md | 319 | ✅ Completo |
| 02_CONTRACTS.md | 911 | ✅ Completo |
| 03_DATA_MODEL.md | 976 | ✅ Completo |
| 04_PREPARE_SPEC.md | 828 | ✅ Completo |
| 05_ENRICH_SPEC.md | 683 | ✅ Completo |
| 06_PUBLISHER_SPEC.md | 216 | ✅ Completo |
| 07_VALIDAR_SPEC.md | 248 | ✅ Completo |
| 08_UI_SPEC.md | ~250 | ✅ Completo |
| 09_TESTING.md | ~350 | ✅ Completo |
| 10_LEGACY_REUSE.md | ~550 | ✅ Completo |
| **TOTAL** | **~5,971** | **✅ 100%** |

---

## Lo que falta en FASE 0

- [ ] Subir MCE legacy a `referencia/referencia-1/`
- [ ] Subir MCE Pro de Codex a `referencia/referencia-2/`
- [ ] Subir JSON crudos de MSL a `samples/`
- [ ] Extraer API keys del legacy → `.env`
- [ ] Crear `LEGACY_REUSE_MAP.md` con auditoría inicial
- [ ] Verificar que GitHub Actions funciona
- [ ] Commit final de FASE 0

---

## Próxima Fase

**FASE 1 — Contratos y Shared Kernel**

### Acción del próximo agente

1. Leer `instrucciones/02_CONTRACTS.md`
2. Implementar los 5 JSON Schemas en `contracts/`
   - `raw_scan_package.json`
   - `validated_scan_package.json`
   - `prepared_work_package.json`
   - `enriched_work_package.json`
   - `publish_command.json`
3. Implementar `src/shared/` con:
   - Enums globales
   - Models Pydantic
   - Validators
   - State machine
4. Escribir tests en `tests/contracts/` y `tests/unit/shared/`
5. Ejecutar tests y verificar cobertura ≥ 85%
6. Actualizar este archivo
7. Commit + push

---

## Agente Actual

**Qwen Code (Web)**

## Próximo Agente

**Qwen Code (Web)**

---

## Bloqueado

Nada

---

## No Tocar

- `referencia/` — Solo lectura, no modificar
- `samples/` — Solo lectura, no modificar
- `.env` — No commitear, no mostrar

---

## Notas

- El proyecto usa **solo Qwen Code** como agente de IA. No hay Cursor.
- GitHub Actions se usa para CI/CD y verificación automática.
- El usuario aprueba manualmente cada merge.
- El flujo es: Qwen implementa → GitHub Actions verifica → Usuario aprueba → Qwen continúa.

---

## Historial de Fases

| Fase | Estado | Fecha Inicio | Fecha Fin |
|------|--------|-------------|-----------|
| FASE 0: Fundación | 🟢 En progreso | 2025 | - |
| FASE 1: Contratos | ⏳ Pendiente | - | - |
| FASE 2: VALIDATE | ⏳ Pendiente | - | - |
| FASE 3: PREPARE | ⏳ Pendiente | - | - |
| FASE 4: ENRICH | ⏳ Pendiente | - | - |
| FASE 5: PUBLISHER | ⏳ Pendiente | - | - |
| FASE 6: Pipeline | ⏳ Pendiente | - | - |
| FASE 7: UI | ⏳ Pendiente | - | - |
| FASE 8: Query Service | ⏳ Pendiente | - | - |
| FASE 9: Pulido | ⏳ Pendiente | - | - |

---

## Checklist de Cierre de FASE 0

```text
DOCUMENTACIÓN (100%):
  [x] 00_MASTER_PLAN.md completo
  [x] 01_ARCHITECTURE.md completo
  [x] 02_CONTRACTS.md completo
  [x] 03_DATA_MODEL.md completo
  [x] 04_PREPARE_SPEC.md completo
  [x] 05_ENRICH_SPEC.md completo
  [x] 06_PUBLISHER_SPEC.md completo
  [x] 07_VALIDAR_SPEC.md completo
  [x] 08_UI_SPEC.md completo
  [x] 09_TESTING.md completo
  [x] 10_LEGACY_REUSE.md completo
  [x] CURRENT_WORK.md actualizado

CONFIGURACIÓN:
  [x] pyproject.toml creado
  [x] config/providers.yaml creado
  [x] config/workers.yaml creado
  [x] .env.example creado
  [x] .gitignore configurado
  [x] .github/workflows/ci.yml configurado
  [x] QWEN.md creado
  [x] README.md creado

PENDIENTES:
  [ ] Legacy subido a referencia/
  [ ] JSON crudos subidos a samples/
  [ ] API keys extraídas a .env
  [ ] LEGACY_REUSE_MAP.md creado
  [ ] GitHub Actions verificado
  [ ] Commit final de FASE 0
```

---

> **Este archivo se actualiza al final de cada tarea.**
> **Es la memoria compartida del proyecto.**

---

## Métricas de la FASE 0

| Métrica | Valor |
|---------|-------|
| Documentos creados | 12 |
| Líneas totales de documentación | ~5,971 |
| Tiempo estimado de lectura completa | 4-6 horas |
| Contratos definidos | 5 |
| Bases de datos especificadas | 4 |
| Módulos documentados | 5 (VALIDATE, PREPARE, ENRICH, PUBLISHER, UI) |
| Casos de test críticos identificados | 50+ |
| Reglas inquebrantables definidas | 100+ |

---

## Próximo Hito

**Cierre de FASE 0** → Implementación de Contratos y Shared Kernel (FASE 1)

---

> **Documento mantenido por:** Qwen Code
> **Revisión requerida si:** Cambia el estado de la fase o se completan pendientes.
