# 🧪 MCE Pro 2.0 — Estrategia de Testing

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Framework:** pytest + pytest-cov + pytest-asyncio

---

## 1. Visión General

MCE Pro 2.0 procesa más de 100,000 obras multimedia. Un error no detectado puede corromper el Catálogo Maestro o gastar miles de llamadas a APIs innecesariamente.

### Pirámide de Tests

```text
                    ╱╲
                   ╱  ╲        E2E Tests (5%)
                  ╱────╲       Pipeline completo con samples reales
                 ╱      ╲
                ╱────────╲     Integration Tests (25%)
               ╱          ╲    Módulos + PostgreSQL + APIs mock
              ╱────────────╲
             ╱              ╲   Unit Tests (70%)
            ╱────────────────╲  Lógica pura, mocks de todo
           ╱──────────────────╲
```

---

## 2. Estructura de Tests

```text
tests/
├── unit/                          ← Tests unitarios (70%)
│   ├── validar/
│   ├── prepare/
│   ├── enrich/
│   ├── publisher/
│   └── shared/
├── integration/                   ← Tests de integración (25%)
│   ├── validar/
│   ├── prepare/
│   ├── enrich/
│   ├── publisher/
│   └── cross_module/
├── e2e/                           ← Tests E2E (5%)
│   ├── test_movie_pipeline.py
│   ├── test_series_pipeline.py
│   └── test_multibank_pipeline.py
├── contracts/                     ← Tests de contratos
├── load/                          ← Tests de carga
├── fixtures/                      ← Datos de prueba
│   ├── samples/
│   ├── json/
│   ├── responses/
│   └── mocks/
├── conftest.py                    ← Fixtures globales
└── pytest.ini                     ← Configuración
```

---

## 3. Reglas Fundamentales

### 3.1 Bases de Datos

```text
REGLA ABSOLUTA:
  Los tests NUNCA tocan bases de datos de producción.

  ✅ USAR: mce_test (base temporal)
  ❌ NUNCA: mce_master, mce_cache, mce_staging, mce_app
```

### 3.2 APIs Externas

```text
REGLA:
  Los tests unitarios NUNCA hacen llamadas reales a APIs.
  Los tests de integración PUEDEN hacer llamadas reales
  pero solo con credenciales de test y rate limiting.

  ✅ Unit tests: Mocks de TMDb, AniList, Tavily, etc.
  ✅ Integration tests: Llamadas reales opcionales (con flag)
```

### 3.3 Idempotencia

```text
REGLA:
  Cada test debe poder ejecutarse múltiples veces
  sin cambiar el resultado.

  ✅ Limpiar estado antes y después
  ✅ No depender del orden
  ✅ No dejar datos residuales
```

---

## 4. Tests Unitarios por Módulo

### VALIDATE

```python
class TestJsonParser:
    def test_valid_json_parses_correctly(self): ...
    def test_corrupt_json_raises_error(self): ...
    def test_missing_bank_id_fails(self): ...

class TestSnapshotDelta:
    def test_first_scan_all_new(self): ...
    def test_same_scan_all_unchanged(self): ...
    def test_missing_file_detected(self): ...
```

### PREPARE

```python
class TestTitleCleaning:
    def test_resolution_removed(self): ...
    def test_year_extracted_separately(self): ...

class TestNumericTitles:
    def test_1917_not_treated_as_year(self): ...
    def test_blade_runner_2049_preserved(self): ...

class TestSeriesGrouping:
    def test_200_episodes_one_work(self): ...
    def test_scattered_seasons_grouped(self): ...
```

### ENRICH

```python
class TestCacheLookup:
    def test_cache_hit_by_external_id(self): ...
    def test_cache_miss_queries_providers(self): ...

class TestProviderChain:
    def test_movie_uses_tmdb_first(self): ...
    def test_anime_uses_anilist_first(self): ...

class TestAiAnalysis:
    def test_qwen_receives_only_evidence(self): ...
    def test_hallucinated_url_rejected(self): ...
```

### PUBLISHER

```python
class TestDeduplication:
    def test_new_work_creates(self): ...
    def test_existing_work_adds_availability(self): ...

class TestRollback:
    def test_rollback_reverses_created_works(self): ...
    def test_rollback_is_idempotent(self): ...

class TestDeletionSync:
    def test_missing_file_removes_availability(self): ...
    def test_work_not_deleted_from_master(self): ...
```

---

## 5. Tests de Integración

### Configuración de DB de Test

```python
# conftest.py

TEST_DB_URL = "postgresql://mce_test:mce_test@localhost:5432/mce_test"

@pytest.fixture(scope="function")
def clean_db(test_engine):
    """Limpia todas las tablas antes de cada test."""
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE work_states CASCADE"))
        conn.commit()
```

### Ejemplo de Test de Integración

```python
class TestValidatePipeline:
    def test_valid_json_produces_validated_package(self, clean_db):
        """JSON válido produce ValidatedScanPackage persistido."""

    def test_snapshot_calculated_and_saved(self, clean_db):
        """Snapshot se calcula y guarda en scan_snapshots."""

class TestFullPipeline:
    def test_movie_from_json_to_master(self, clean_db):
        """Película desde JSON hasta Master Catalog."""

    def test_same_movie_two_banks(self, clean_db):
        """Misma película en dos bancos → 1 obra, 2 disponibilidades."""
```

---

## 6. Tests de Contratos

```python
class TestPreparedWorkSchema:
    def test_valid_package_passes(self, schema): ...
    def test_missing_logical_work_id_fails(self, schema): ...
    def test_invalid_year_fails(self, schema): ...
```

---

## 7. Tests E2E

```python
class TestMoviePipelineE2E:
    def test_avatar_full_pipeline(self):
        """Avatar desde JSON real hasta Master."""

class TestMultibankPipelineE2E:
    def test_same_movie_two_banks(self):
        """Misma película en dos bancos → 1 obra, 2 disponibilidades."""
```

---

## 8. Tests de Carga

```python
class TestLoad10k:
    @pytest.mark.slow
    def test_10k_works_under_2_hours(self):
        """10,000 obras se procesan en < 2 horas."""

    @pytest.mark.slow
    def test_memory_under_4gb(self):
        """Uso de RAM no supera 4 GB."""
```

---

## 9. Configuración de pytest

```ini
# pytest.ini

[pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers
markers =
    unit: Tests unitarios (rápidos, sin DB)
    integration: Tests de integración (con DB de test)
    e2e: Tests end-to-end (pipeline completo)
    load: Tests de carga (lentos)
    slow: Tests que tardan > 10 segundos
    api: Tests que hacen llamadas reales a APIs
```

---

## 10. Cobertura de Código

| Módulo | Cobertura Mínima | Objetivo |
|--------|-----------------|----------|
| VALIDATE | 85% | 95% |
| PREPARE | 85% | 95% |
| ENRICH | 80% | 90% |
| PUBLISHER | 90% | 95% |
| Shared | 90% | 95% |
| Contratos | 100% | 100% |

### Ejecución

```bash
# Cobertura completa
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Verificar umbral mínimo
pytest tests/ --cov=src --cov-fail-under=85
```

---

## 11. CI/CD con GitHub Actions

```yaml
# .github/workflows/tests.yml

name: MCE Pro 2.0 - Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ -v

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_USER: mce_test, POSTGRES_PASSWORD: mce_test }
        ports: [5432:5432]
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -v

  coverage:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/ --cov=src --cov-fail-under=85
```

---

## 12. Ejecución Local

```bash
# Todos los tests
pytest tests/ -v

# Solo unit tests (rápido)
pytest tests/unit/ -v

# Solo un módulo
pytest tests/unit/prepare/ -v

# Solo un test específico
pytest tests/unit/prepare/test_numeric_titles.py::TestNumericTitles::test_1917_not_treated_as_year -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

---

## 13. Casos de Test Críticos

| # | Caso | Módulo | Criticidad |
|---|------|--------|------------|
| 1 | Carpeta vs filename | PREPARE | 🔴 Alta |
| 2 | Títulos numéricos (1917, 2049) | PREPARE | 🔴 Alta |
| 3 | DVD combo con múltiples obras | PREPARE | 🔴 Alta |
| 4 | Series con temporadas dispersas | PREPARE | 🔴 Alta |
| 5 | Cache entre bancos | ENRICH | 🔴 Alta |
| 6 | IA no inventa URLs | ENRICH | 🔴 Alta |
| 7 | Deduplicación por external_id | PUBLISHER | 🔴 Alta |
| 8 | Rollback revierte correctamente | PUBLISHER | 🔴 Alta |
| 9 | Delta inverso (archivos eliminados) | PUBLISHER | 🔴 Alta |
| 10 | Idempotencia del pipeline completo | TODOS | 🔴 Alta |

---

## 14. Lo que los Tests NUNCA Hacen

1. ❌ No tocan `mce_master`, `mce_cache`, `mce_app` de producción
2. ❌ No gastan cuota real de APIs en tests unitarios
3. ❌ No dependen del orden de ejecución
4. ❌ No dejan datos residuales
5. ❌ No requieren intervención manual
6. ❌ No modifican archivos en `referencia/` o `samples/`

---

> **Documento mantenido por:** Qwen Code
> **Próximo documento:** `instrucciones/10_LEGACY_REUSE.md`
