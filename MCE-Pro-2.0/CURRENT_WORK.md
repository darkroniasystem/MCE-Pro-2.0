# 📌 CURRENT WORK — MCE Pro 2.0

> **Última actualización:** 2025
> **Agente activo:** Qwen Code (Web)

---

## Proyecto

MCE Pro 2.0 — Media Cleaner & Enrichment

## Fase Actual

**FASE 1 — Contratos y Shared Kernel**

## Estado

🟢 EN PROGRESO

---

## Objetivo Actual

Implementar los 5 JSON Schemas de contratos y el paquete compartido (src/shared/).

---

## Último Commit

`6f3f474` - "feat: FASE 1 completada - 5 JSON Schemas de contratos implementados y validados"

---

## Lo que se ha completado

### FASE 0 — Fundación ✅ COMPLETADA

- [x] Repositorio creado en GitHub: `MCE-Pro-2.0`
- [x] Estructura de carpetas creada
- [x] `instrucciones/00_MASTER_PLAN.md` — Plan maestro con 10 fases
- [x] `instrucciones/01_ARCHITECTURE.md` — Arquitectura oficial
- [x] `instrucciones/02_CONTRACTS.md` — 5 contratos JSON Schema
- [x] `instrucciones/03_DATA_MODEL.md` — 4 bases de datos PostgreSQL
- [x] `instrucciones/04_PREPARE_SPEC.md` — Especificación de PREPARE
- [x] `instrucciones/05_ENRICH_SPEC.md` — Especificación de ENRICH
- [x] `instrucciones/06_PUBLISHER_SPEC.md` — Especificación de PUBLISHER
- [x] `instrucciones/07_VALIDAR_SPEC.md` — Especificación de VALIDATE
- [x] `instrucciones/08_UI_SPEC.md` — Especificación de UI
- [x] `instrucciones/09_TESTING.md` — Estrategia de testing
- [x] `instrucciones/10_LEGACY_REUSE.md` — Reutilización del legacy
- [x] `pyproject.toml` — Configuración de proyecto
- [x] `config/providers.yaml` — Configuración de proveedores
- [x] `config/workers.yaml` — Configuración de workers
- [x] `.env.example` — Plantilla de variables de entorno
- [x] `.gitignore` — Archivos excluidos de Git
- [x] `.github/workflows/ci.yml` — Pipeline CI/CD
- [x] `QWEN.md` — Instrucciones para Qwen Code
- [x] `README.md` — Documentación del proyecto
- [x] `.env` — API keys configuradas (no commiteado)

### FASE 1 — Contratos ✅ EN PROGRESO

- [x] `contracts/raw_scan_package.json` — Contrato MSL → VALIDATE
- [x] `contracts/validated_scan_package.json` — Contrato VALIDATE → PREPARE
- [x] `contracts/prepared_work_package.json` — Contrato PREPARE → ENRICH
- [x] `contracts/enriched_work_package.json` — Contrato ENRICH → PUBLISHER
- [x] `contracts/publish_command.json` — Contrato PUBLISHER → MASTER
- [ ] `src/shared/enums.py` — Enums globales
- [ ] `src/shared/models.py` — Modelos Pydantic
- [ ] `src/shared/validators.py` — Validador de contratos
- [ ] `src/shared/state_machine.py` — State machine
- [ ] `src/shared/config.py` — Config loader
- [ ] `src/shared/errors.py` — Error types
- [ ] `src/shared/logging.py` — Logging structured
- [ ] Tests de contratos (`tests/contracts/`)
- [ ] Tests de shared (`tests/unit/shared/`)

---

## Lo que falta en FASE 1

- [ ] Implementar `src/shared/` completo
- [ ] Escribir tests unitarios para contratos
- [ ] Escribir tests unitarios para shared
- [ ] Verificar cobertura ≥ 90%
- [ ] Ruff limpio
- [ ] MyPy limpio
- [ ] Actualizar este archivo
- [ ] Commit final de FASE 1

---

## Próxima Fase

**FASE 2 — VALIDATE**

### Acción del próximo agente

1. Leer `instrucciones/07_VALIDAR_SPEC.md`
2. Implementar módulo VALIDATE completo
3. Escribir tests en `tests/unit/validar/` y `tests/integration/validar/`
4. Ejecutar tests y verificar cobertura ≥ 85%
5. Actualizar este archivo
6. Commit + push

---

## Agente Actual

Qwen Code (Web)

## Próximo Agente

Qwen Code (Web)

---

## Bloqueado

Nada

---

## No Tocar

- `referencia/` — Solo lectura, no modificar
- `samples/` — Solo lectura, no modificar (los JSONs grandes están en .zip)
- `.env` — No commitear, no mostrar

---

## Notas

- El proyecto usa **solo Qwen Code** como agente de IA.
- GitHub Actions se usa para CI/CD y verificación automática.
- El usuario aprueba manualmente cada merge.
- API keys configuradas en `.env` (no commiteado).

---

## Historial de Fases

| Fase | Estado | Fecha Inicio | Fecha Fin |
|------|--------|-------------|-----------|
| FASE 0: Fundación | ✅ Completada | 2025 | 2025 |
| FASE 1: Contratos | 🟢 En progreso | 2025 | - |
| FASE 2: VALIDATE | ⏳ Pendiente | - | - |
| FASE 3: PREPARE | ⏳ Pendiente | - | - |
| FASE 4: ENRICH | ⏳ Pendiente | - | - |
| FASE 5: PUBLISHER | ⏳ Pendiente | - | - |
| FASE 6: Pipeline | ⏳ Pendiente | - | - |
| FASE 7: UI | ⏳ Pendiente | - | - |
| FASE 8: Query Service | ⏳ Pendiente | - | - |
| FASE 9: Pulido | ⏳ Pendiente | - | - |

---

> **Este archivo se actualiza al final de cada tarea.**
> **Es la memoria compartida del proyecto.**
