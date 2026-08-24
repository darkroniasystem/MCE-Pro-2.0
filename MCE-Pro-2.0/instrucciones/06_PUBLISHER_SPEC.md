# 🚪 MCE Pro 2.0 — Especificación del Módulo PUBLISHER

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Módulo:** PUBLISHER (Fase 4 del Pipeline)

---

## 1. Misión

PUBLISHER es el **único guardián del Catálogo Maestro**.

> **Pregunta que responde PUBLISHER:**
> ¿Esta información puede integrarse con seguridad al Catálogo Maestro sin crear duplicados ni destruir información válida?

> **Pregunta que NO responde PUBLISHER:**
> ¿Qué obra es esta? (Eso ya lo respondió ENRICH)

---

## 2. Posición en el Pipeline

```text
MSL → VALIDATE → PREPARE → ENRICH → [ PUBLISHER ] → MASTER
                                         │
                                         ├── Entrada:  EnrichedWorkPackage (APPROVED / APPROVED_PARTIAL)
                                         ├── Salida:   PublishCommand → Escritura en mce_master
                                         ├── DB:       Lee/Escribe mce_master, escribe mce_staging
                                         ├── Assets:   Descarga/verifica en assets/
                                         └── UI:       Panel naranja con pestañas
```

---

## 3. Entrada y Salida

### 3.1 Entrada

- **Contrato:** `EnrichedWorkPackage` (schema_version: 1)
- **Origen:** `mce_staging.contract_instances`
- **Estados aceptados:** SOLO `READY_FOR_PUBLISH` o `APPROVED_PARTIAL`
- **Estados rechazados:** `HUMAN_REVIEW`, `NOT_FOUND`, `PROVIDER_ERROR`, `PREPARE_INSUFFICIENT`

### 3.2 Salida

- **Contrato:** `PublishCommand` (schema_version: 1)
- **Destino:** Escritura transaccional en `mce_master`
- **Historial:** Registro en `mce_master.publish_history`
- **Estados generados:** `PUBLISHED`, `PUBLISH_CONFLICT`, `PUBLISH_FAILED`, `PENDING_ASSETS`

---

## 4. Principios Fundamentales

1. **El Master es Sagrado** - Solo PUBLISHER escribe en mce_master
2. **Preflight Antes que Todo** - Detectar problemas ANTES de tocar el Master
3. **No Duplicar, No Destruir** - Si ya existe → ADD_AVAILABILITY, no CREATE
4. **Transaccional y Auditable** - Cada publicación tiene publish_id y rollback

---

## 5. Proceso de Publicación (4 Fases)

```text
EnrichedWorkPackage[]
        │
        ▼
┌─ FASE 1: PREFLIGHT ─────────────┐
│  Validar contratos y contenido  │
│  Verificar conflictos           │
└─────────────────────────────────┘
        │
        ▼
┌─ FASE 2: DEDUPLICACIÓN FINAL ───┐
│  Buscar en Master               │
│  ├── Ya existe → ADD_AVAILABILITY
│  └── No existe → CREATE
└─────────────────────────────────┘
        │
        ▼
┌─ FASE 3: TRANSACCIÓN ───────────┐
│  BEGIN TRANSACTION              │
│  Escribir por lotes (batches)   │
│  COMMIT / ROLLBACK              │
└─────────────────────────────────┘
        │
        ▼
┌─ FASE 4: POST-PUBLICACIÓN ──────┐
│  Descargar assets               │
│  Actualizar stats               │
│  Notificar usuario              │
└─────────────────────────────────┘
```

---

## 6. Preflight Checks

Validaciones ANTES de tocar mce_master:

- ✅ schema_version válido
- ✅ status es READY_FOR_PUBLISH o APPROVED_PARTIAL
- ✅ year en rango (1888-2030)
- ✅ external_ids con formato correcto
- ✅ No hay conflicto de datos estables
- ✅ Assets URLs son válidas

---

## 7. Deduplicación

Orden de búsqueda (más fuerte a más débil):

1. External IDs (TMDb, IMDb, Wikidata)
2. Título original + año + categoría
3. Título en español + año
4. Aliases

**Acciones:**
- CREATE → Obra nueva
- ADD_AVAILABILITY → Obra existe, añadir banco
- UPDATE_METADATA → Solo campos dinámicos (rating)

---

## 8. Transacciones y Batches

```text
batch_size: 200 obras (configurable)

POR LOTE:
  BEGIN TRANSACTION
  INSERT INTO works, aliases, metadata, external_ids, availability
  COMMIT

SI ERROR:
  ROLLBACK del lote
  Continuar con siguiente lote
```

---

## 9. Delta Inverso (Sync de Borrados)

Cuando un archivo desaparece del escaneo:

1. REMOVE_AVAILABILITY para ese bank_id
2. NO borrar la obra del Master
3. Si no hay más bancos → ARCHIVED
4. Si reaparece → reactivar disponibilidad

---

## 10. Rollback

Cada publicación puede revertirse:

- Leer publish_history.previous_state
- Ejecutar operaciones inversas
- Marcar status = 'ROLLED_BACK'
- Requiere confirmación del usuario

---

## 11. Assets

- Posters: assets/posters/{work_id}.jpg
- Backdrops: assets/backdrops/{work_id}.jpg
- Placeholders si no hay asset disponible
- Asset Downloader worker (2 threads, asíncrono)

---

## 12. UI de PUBLISHER

6 Pestañas:
1. **Lotes** - Progreso de cada batch
2. **Conflictos** - Resolver conflictos de datos
3. **Disponibilidad** - Obras nuevas/existentes
4. **Assets** - Estado de descarga
5. **Historial** - publish_history
6. **Rollback** - Revertir publicaciones

Botones: [PUBLICAR] [DRY RUN] [CANCELAR]

---

## 13. Casos de Test Críticos

| # | Caso | Criticidad |
|---|------|------------|
| 1 | Obra nueva → CREATE | 🔴 Alta |
| 2 | Obra existente → ADD_AVAILABILITY | 🔴 Alta |
| 3 | Conflicto datos estables | 🔴 Alta |
| 4 | Rollback funciona | 🔴 Alta |
| 5 | Delta inverso | 🔴 Alta |
| 6 | Idempotencia | 🔴 Alta |

---

## 14. Lo que PUBLISHER NUNCA Hace

1. ❌ No enriquece obras
2. ❌ No consulta APIs externas
3. ❌ No modifica mce_cache
4. ❌ No borra obras del Master
5. ❌ No sobrescribe datos estables
6. ❌ No publica sin preflight
7. ❌ No ejecuta rollback automáticamente

---

> **Documento mantenido por:** Qwen Code
> **Próximo documento:** `instrucciones/07_VALIDAR_SPEC.md`
