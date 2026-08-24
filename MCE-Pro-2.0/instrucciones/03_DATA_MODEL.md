# 🗄️ MCE Pro 2.0 — Modelo de Datos

> **Estado:** COMPLETO
> **Versión:** 2.0.0
> **Última actualización:** 2025
> **Agente:** Qwen Code (Web)
> **Motor:** PostgreSQL 15+

---

## 1. Visión General

MCE Pro 2.0 utiliza 4 bases de datos separadas en PostgreSQL, cada una con un propósito claro y reglas de acceso estrictas.

```text
PostgreSQL
│
├── mce_staging     ← TEMPORAL (pipeline actual)
├── mce_cache       ← PERMANENTE (reutilizable entre bancos)
├── mce_master      ← SAGRADO (catálogo final)
└── mce_app         ← USUARIOS (bot/mini app)
```

### Reglas de Acceso

| Base de Datos | VALIDATE | PREPARE | ENRICH | PUBLISHER | QUERY SERVICE |
|---------------|----------|---------|--------|-----------|---------------|
| mce_staging   | ✅ R/W   | ✅ R/W  | ✅ R/W | ✅ R/W    | ❌            |
| mce_cache     | ❌       | ✅ R    | ✅ R/W | ❌        | ❌            |
| mce_master    | ❌       | ❌      | ❌     | ✅ R/W    | ✅ R          |
| mce_app       | ❌       | ❌      | ❌     | ❌        | ✅ R/W        |

---

## 2. mce_staging — Pipeline Temporal

**Propósito:** Almacena datos del pipeline actual. Se limpia al finalizar.

**Ciclo de vida:** Temporal por pipeline.

**Acceso:** Todos los módulos del pipeline.

### 2.1 Tabla: pipeline_runs

Registra cada ejecución del pipeline.

```sql
CREATE TABLE pipeline_runs (
    pipeline_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_id             VARCHAR(50) NOT NULL,
    scan_id             UUID NOT NULL,
    started_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMP WITH TIME ZONE,
    status              VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    current_phase       VARCHAR(30) NOT NULL DEFAULT 'VALIDATE',
    total_works         INTEGER DEFAULT 0,
    processed_works     INTEGER DEFAULT 0,
    failed_works        INTEGER DEFAULT 0,
    error_message       TEXT,
    config_snapshot     JSONB,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_status CHECK (status IN (
        'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED'
    )),
    CONSTRAINT chk_phase CHECK (current_phase IN (
        'VALIDATE', 'PREPARE', 'ENRICH', 'PUBLISH', 'DONE'
    ))
);

CREATE INDEX idx_pipeline_bank ON pipeline_runs(bank_id);
CREATE INDEX idx_pipeline_status ON pipeline_runs(status);
CREATE INDEX idx_pipeline_started ON pipeline_runs(started_at DESC);
```

### 2.2 Tabla: work_states

Estado actual de cada obra lógica dentro del pipeline.

```sql
CREATE TABLE work_states (
    work_state_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         UUID NOT NULL REFERENCES pipeline_runs(pipeline_id),
    scan_id             UUID NOT NULL,
    bank_id             VARCHAR(50) NOT NULL,
    logical_work_id     UUID NOT NULL,
    status              VARCHAR(40) NOT NULL,
    current_module      VARCHAR(20) NOT NULL,
    retry_count         INTEGER DEFAULT 0,
    last_error          TEXT,
    error_type          VARCHAR(30),
    entered_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    priority            VARCHAR(10) DEFAULT 'MEDIUM',

    CONSTRAINT chk_work_status CHECK (status IN (
        'VALIDATED', 'READY_FOR_PREPARE', 'PREPARING', 'PREPARED',
        'READY_FOR_ENRICHMENT', 'ENRICHING', 'APPROVED', 'APPROVED_PARTIAL',
        'HUMAN_REVIEW', 'NOT_FOUND', 'PREPARE_INSUFFICIENT',
        'READY_FOR_PUBLISH', 'PUBLISHING', 'PUBLISHED',
        'PUBLISH_CONFLICT', 'PUBLISH_FAILED', 'PROVIDER_ERROR',
        'CLASSIFICATION_REVIEW', 'PREPARE_REVIEW', 'ANOMALOUS_SCAN',
        'VALIDATION_FAILED', 'DEAD_LETTER'
    )),
    CONSTRAINT chk_module CHECK (current_module IN (
        'VALIDATE', 'PREPARE', 'ENRICH', 'PUBLISHER', 'HUMAN', 'NONE'
    )),
    CONSTRAINT chk_priority CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW'))
);

CREATE INDEX idx_ws_pipeline ON work_states(pipeline_id);
CREATE INDEX idx_ws_status ON work_states(status);
CREATE INDEX idx_ws_logical ON work_states(logical_work_id);
CREATE INDEX idx_ws_bank ON work_states(bank_id);
CREATE INDEX idx_ws_module ON work_states(current_module);
CREATE INDEX idx_ws_priority ON work_states(priority);
```

### 2.3 Tabla: checkpoints

Puntos de guardado para reanudación tras fallos.

```sql
CREATE TABLE checkpoints (
    checkpoint_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         UUID NOT NULL REFERENCES pipeline_runs(pipeline_id),
    phase               VARCHAR(20) NOT NULL,
    checkpoint_data     JSONB NOT NULL,
    works_processed     INTEGER NOT NULL DEFAULT 0,
    last_logical_work_id UUID,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_cp_phase CHECK (phase IN (
        'VALIDATE', 'PREPARE', 'ENRICH', 'PUBLISH'
    ))
);

CREATE INDEX idx_cp_pipeline ON checkpoints(pipeline_id);
CREATE INDEX idx_cp_created ON checkpoints(created_at DESC);
```

### 2.4 Tabla: contract_instances

Instancias persistidas de contratos entre módulos.

```sql
CREATE TABLE contract_instances (
    contract_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         UUID NOT NULL REFERENCES pipeline_runs(pipeline_id),
    scan_id             UUID NOT NULL,
    bank_id             VARCHAR(50) NOT NULL,
    contract_type       VARCHAR(50) NOT NULL,
    schema_version      INTEGER NOT NULL DEFAULT 1,
    status              VARCHAR(40) NOT NULL,
    logical_work_id     UUID,
    payload             JSONB NOT NULL,
    validation_result   VARCHAR(20),
    validation_errors   JSONB,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_contract_type CHECK (contract_type IN (
        'RawScanPackage', 'ValidatedScanPackage', 'PreparedWorkPackage',
        'EnrichedWorkPackage', 'PublishCommand'
    )),
    CONSTRAINT chk_validation CHECK (validation_result IN (
        'PENDING', 'VALID', 'INVALID', 'REJECTED'
    ))
);

CREATE INDEX idx_ci_pipeline ON contract_instances(pipeline_id);
CREATE INDEX idx_ci_type ON contract_instances(contract_type);
CREATE INDEX idx_ci_status ON contract_instances(status);
CREATE INDEX idx_ci_logical ON contract_instances(logical_work_id);
CREATE INDEX idx_ci_bank ON contract_instances(bank_id);
```

### 2.5 Tabla: scan_snapshots

Snapshots de escaneos para calcular deltas.

```sql
CREATE TABLE scan_snapshots (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_id             VARCHAR(50) NOT NULL,
    scan_id             UUID NOT NULL,
    section_name        VARCHAR(100) NOT NULL,
    category            VARCHAR(30) NOT NULL,
    total_files         INTEGER NOT NULL,
    total_size_bytes    BIGINT NOT NULL,
    file_hashes         JSONB NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_snapshot UNIQUE (bank_id, section_name, scan_id)
);

CREATE INDEX idx_ss_bank ON scan_snapshots(bank_id);
CREATE INDEX idx_ss_created ON scan_snapshots(created_at DESC);
```

### 2.6 Tabla: dead_letter_queue

Obras que fallaron tras todos los reintentos.

```sql
CREATE TABLE dead_letter_queue (
    dlq_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         UUID NOT NULL REFERENCES pipeline_runs(pipeline_id),
    logical_work_id     UUID NOT NULL,
    bank_id             VARCHAR(50) NOT NULL,
    failed_phase        VARCHAR(20) NOT NULL,
    error_type          VARCHAR(30) NOT NULL,
    error_message       TEXT NOT NULL,
    retry_count         INTEGER NOT NULL,
    original_payload    JSONB NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved            BOOLEAN DEFAULT FALSE,
    resolved_at         TIMESTAMP WITH TIME ZONE,
    resolution_notes    TEXT
);

CREATE INDEX idx_dlq_pipeline ON dead_letter_queue(pipeline_id);
CREATE INDEX idx_dlq_resolved ON dead_letter_queue(resolved);
CREATE INDEX idx_dlq_bank ON dead_letter_queue(bank_id);
```

---

## 3. mce_cache — Datos Reutilizables

**Propósito:** Caché permanente reutilizable entre bancos y ejecuciones.

**Ciclo de vida:** Persistente. Nunca se limpia automáticamente.

**Acceso:** PREPARE (lectura), ENRICH (lectura/escritura).

### 3.1 Tabla: global_works

Obras ya identificadas. Metadata universal.

```sql
CREATE TABLE global_works (
    global_work_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_title      VARCHAR(500) NOT NULL,
    spanish_title       VARCHAR(500),
    alternative_titles  JSONB DEFAULT '[]',
    year                SMALLINT,
    category            VARCHAR(30) NOT NULL,
    external_ids        JSONB NOT NULL DEFAULT '{}',
    metadata            JSONB DEFAULT '{}',
    identity_confidence FLOAT,
    identified_by       VARCHAR(30),
    identified_at       TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version             INTEGER DEFAULT 1,

    CONSTRAINT chk_gw_year CHECK (year IS NULL OR (year >= 1888 AND year <= 2030)),
    CONSTRAINT chk_gw_category CHECK (category IN (
        'Peliculas', 'Series', 'Novelas', 'Anime', 'Doramas', 'Animadas', 'Concursos'
    ))
);

CREATE INDEX idx_gw_title ON global_works USING GIN (to_tsvector('spanish', original_title));
CREATE INDEX idx_gw_year ON global_works(year);
CREATE INDEX idx_gw_category ON global_works(category);
CREATE INDEX idx_gw_ext_ids ON global_works USING GIN (external_ids);
```

### 3.2 Tabla: provider_responses

Respuestas cacheadas de proveedores externos.

```sql
CREATE TABLE provider_responses (
    response_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider            VARCHAR(30) NOT NULL,
    query_hash          VARCHAR(64) NOT NULL,
    query_text          TEXT NOT NULL,
    response_payload    JSONB NOT NULL,
    http_status         INTEGER,
    duration_ms         INTEGER,
    fetched_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at          TIMESTAMP WITH TIME ZONE,
    is_valid            BOOLEAN DEFAULT TRUE,

    CONSTRAINT uq_provider_query UNIQUE (provider, query_hash),
    CONSTRAINT chk_provider CHECK (provider IN (
        'tmdb', 'anilist', 'tvmaze', 'wikidata', 'wikipedia',
        'tavily', 'serper', 'exa', 'omdb', 'fanart_tv', 'groq', 'qwen'
    ))
);

CREATE INDEX idx_pr_provider ON provider_responses(provider);
CREATE INDEX idx_pr_query ON provider_responses(query_hash);
CREATE INDEX idx_pr_expires ON provider_responses(expires_at);
```

### 3.3 Tabla: wikidata_cache

Caché específica de Wikidata/Wikipedia.

```sql
CREATE TABLE wikidata_cache (
    cache_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source              VARCHAR(20) NOT NULL,
    entity_id           VARCHAR(20),
    search_query        VARCHAR(500) NOT NULL,
    title               VARCHAR(500),
    year                SMALLINT,
    media_type          VARCHAR(50),
    aliases             JSONB DEFAULT '[]',
    external_ids        JSONB DEFAULT '{}',
    description         TEXT,
    confidence          FLOAT,
    fetched_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at          TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_wk_source CHECK (source IN ('wikidata', 'wikipedia'))
);

CREATE INDEX idx_wk_entity ON wikidata_cache(entity_id);
CREATE INDEX idx_wk_query ON wikidata_cache USING GIN (to_tsvector('spanish', search_query));
CREATE INDEX idx_wk_title ON wikidata_cache USING GIN (to_tsvector('spanish', title));
```

### 3.4 Tabla: asset_urls

URLs de assets (posters, backdrops) ya conocidos.

```sql
CREATE TABLE asset_urls (
    asset_url_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    global_work_id      UUID REFERENCES global_works(global_work_id),
    asset_type          VARCHAR(20) NOT NULL,
    url                 TEXT NOT NULL,
    source_provider     VARCHAR(30) NOT NULL,
    width               INTEGER,
    height              INTEGER,
    local_path          VARCHAR(500),
    downloaded          BOOLEAN DEFAULT FALSE,
    downloaded_at       TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_asset_type CHECK (asset_type IN ('poster', 'backdrop', 'logo', 'banner')),
    CONSTRAINT uq_asset_url UNIQUE (global_work_id, asset_type, url)
);

CREATE INDEX idx_au_work ON asset_urls(global_work_id);
CREATE INDEX idx_au_type ON asset_urls(asset_type);
CREATE INDEX idx_au_downloaded ON asset_urls(downloaded);
```

### 3.5 Tabla: human_corrections

Memoria de correcciones humanas. El sistema aprende de ellas.

```sql
CREATE TABLE human_corrections (
    correction_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_input      VARCHAR(500) NOT NULL,
    corrected_title     VARCHAR(500) NOT NULL,
    corrected_year      SMALLINT,
    corrected_category  VARCHAR(30),
    corrected_external_ids JSONB DEFAULT '{}',
    bank_id             VARCHAR(50),
    logical_work_id     UUID,
    correction_type     VARCHAR(30) NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          VARCHAR(50) DEFAULT 'user',

    CONSTRAINT chk_correction_type CHECK (correction_type IN (
        'ALIAS_FORCED', 'IDENTITY_CORRECTED', 'CATEGORY_CORRECTED',
        'YEAR_CORRECTED', 'MERGE_WORKS', 'SPLIT_WORK'
    ))
);

CREATE INDEX idx_hc_input ON human_corrections USING GIN (to_tsvector('spanish', original_input));
CREATE INDEX idx_hc_type ON human_corrections(correction_type);
CREATE INDEX idx_hc_bank ON human_corrections(bank_id);
```

### 3.6 Tabla: enrichment_stats

Estadísticas de uso de APIs y rendimiento.

```sql
CREATE TABLE enrichment_stats (
    stat_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stat_date           DATE NOT NULL,
    provider            VARCHAR(30) NOT NULL,
    total_calls         INTEGER DEFAULT 0,
    successful_calls    INTEGER DEFAULT 0,
    failed_calls        INTEGER DEFAULT 0,
    cache_hits          INTEGER DEFAULT 0,
    cache_misses        INTEGER DEFAULT 0,
    avg_duration_ms     INTEGER,
    rate_limit_hits     INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_stat UNIQUE (stat_date, provider)
);

CREATE INDEX idx_es_date ON enrichment_stats(stat_date DESC);
CREATE INDEX idx_es_provider ON enrichment_stats(provider);
```

---

## 4. mce_master — Catálogo Maestro

**Propósito:** Catálogo final de obras. Fuente única de verdad.

**Ciclo de vida:** Permanente.

**Acceso de escritura:** SOLO PUBLISHER.

**Acceso de lectura:** QUERY SERVICE.

### 4.1 Tabla: works

Obras canónicas del catálogo.

```sql
CREATE TABLE works (
    work_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_title      VARCHAR(500) NOT NULL,
    spanish_title       VARCHAR(500),
    alternative_titles  JSONB DEFAULT '[]',
    year                SMALLINT,
    category            VARCHAR(30) NOT NULL,
    status              VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    identity_confidence FLOAT,
    metadata_completeness FLOAT,
    version             INTEGER DEFAULT 1,
    last_publish_id     UUID,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_work_year CHECK (year IS NULL OR (year >= 1888 AND year <= 2030)),
    CONSTRAINT chk_work_category CHECK (category IN (
        'Peliculas', 'Series', 'Novelas', 'Anime', 'Doramas', 'Animadas', 'Concursos'
    )),
    CONSTRAINT chk_work_status CHECK (status IN (
        'ACTIVE', 'ARCHIVED', 'MERGED', 'DISPUTED'
    ))
);

CREATE INDEX idx_works_title ON works USING GIN (to_tsvector('spanish', original_title));
CREATE INDEX idx_works_year ON works(year);
CREATE INDEX idx_works_category ON works(category);
```

### 4.2 Tabla: aliases

Títulos alternativos de cada obra.

```sql
CREATE TABLE aliases (
    alias_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id             UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    alias_text          VARCHAR(500) NOT NULL,
    language            VARCHAR(10) DEFAULT 'es',
    is_primary          BOOLEAN DEFAULT FALSE,
    source              VARCHAR(30),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_alias UNIQUE (work_id, alias_text)
);

CREATE INDEX idx_aliases_work ON aliases(work_id);
CREATE INDEX idx_aliases_text ON aliases USING GIN (to_tsvector('spanish', alias_text));
```

### 4.3 Tabla: metadata

Metadatos enriquecidos de cada obra.

```sql
CREATE TABLE metadata (
    metadata_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id             UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    genres              JSONB DEFAULT '[]',
    director            JSONB DEFAULT '[]',
    main_cast           JSONB DEFAULT '[]',
    synopsis            TEXT,
    rating              FLOAT,
    runtime_minutes     INTEGER,
    country             JSONB DEFAULT '[]',
    language            VARCHAR(50),
    tags                JSONB DEFAULT '[]',
    is_dynamic_updated  BOOLEAN DEFAULT FALSE,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_md_rating CHECK (rating IS NULL OR (rating >= 0.0 AND rating <= 10.0)),
    CONSTRAINT chk_md_runtime CHECK (runtime_minutes IS NULL OR (runtime_minutes >= 1 AND runtime_minutes <= 600))
);

CREATE INDEX idx_md_work ON metadata(work_id);
CREATE INDEX idx_md_genres ON metadata USING GIN (genres);
CREATE INDEX idx_md_rating ON metadata(rating);
```

### 4.4 Tabla: external_ids

IDs externos de cada obra.

```sql
CREATE TABLE external_ids (
    ext_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id             UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    provider            VARCHAR(30) NOT NULL,
    provider_id         VARCHAR(100) NOT NULL,
    url                 TEXT,
    confidence          FLOAT,
    source              VARCHAR(30),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_ext UNIQUE (work_id, provider),
    CONSTRAINT chk_ext_provider CHECK (provider IN (
        'tmdb', 'imdb', 'wikidata', 'anilist', 'tvmaze', 'omdb', 'fanart_tv'
    ))
);

CREATE INDEX idx_ext_work ON external_ids(work_id);
CREATE INDEX idx_ext_provider ON external_ids(provider, provider_id);
CREATE INDEX idx_ext_lookup ON external_ids(provider_id);
```

### 4.5 Tabla: availability

Disponibilidad de obras por banco.

```sql
CREATE TABLE availability (
    availability_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id             UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    bank_id             VARCHAR(50) NOT NULL,
    is_available        BOOLEAN DEFAULT TRUE,
    first_seen_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scan_count          INTEGER DEFAULT 1,

    CONSTRAINT uq_availability UNIQUE (work_id, bank_id)
);

CREATE INDEX idx_avail_work ON availability(work_id);
CREATE INDEX idx_avail_bank ON availability(bank_id);
CREATE INDEX idx_avail_available ON availability(is_available);
```

### 4.6 Tabla: physical_locations

Ubicaciones físicas de cada obra.

```sql
CREATE TABLE physical_locations (
    location_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id             UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    bank_id             VARCHAR(50) NOT NULL,
    file_path           TEXT NOT NULL,
    folder_path         TEXT,
    drive_letter        VARCHAR(5),
    file_size_bytes     BIGINT,
    file_extension      VARCHAR(20),
    file_hash           VARCHAR(64),
    location_type       VARCHAR(20) DEFAULT 'file',
    is_dvd_structure    BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_loc_type CHECK (location_type IN (
        'file', 'dvd_structure', 'folder', 'network_share'
    ))
);

CREATE INDEX idx_pl_work ON physical_locations(work_id);
CREATE INDEX idx_pl_bank ON physical_locations(bank_id);
CREATE INDEX idx_pl_path ON physical_locations(file_path);
```

### 4.7 Tabla: assets

Assets (posters, backdrops) del catálogo.

```sql
CREATE TABLE assets (
    asset_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id             UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    asset_type          VARCHAR(20) NOT NULL,
    original_url        TEXT,
    local_path          VARCHAR(500) NOT NULL,
    width               INTEGER,
    height              INTEGER,
    file_format         VARCHAR(10),
    file_size_bytes     INTEGER,
    source_provider     VARCHAR(30),
    is_placeholder      BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_asset_type CHECK (asset_type IN ('poster', 'backdrop', 'logo', 'banner')),
    CONSTRAINT uq_asset UNIQUE (work_id, asset_type, is_placeholder)
);

CREATE INDEX idx_assets_work ON assets(work_id);
CREATE INDEX idx_assets_type ON assets(asset_type);
```

### 4.8 Tabla: publish_history

Historial de publicaciones para auditoría y rollback.

```sql
CREATE TABLE publish_history (
    publish_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         UUID NOT NULL,
    bank_id             VARCHAR(50) NOT NULL,
    batch_number        INTEGER NOT NULL,
    total_batches       INTEGER NOT NULL,
    action              VARCHAR(20) NOT NULL,
    works_count         INTEGER NOT NULL,
    works_created       INTEGER DEFAULT 0,
    works_updated       INTEGER DEFAULT 0,
    availability_added  INTEGER DEFAULT 0,
    availability_removed INTEGER DEFAULT 0,
    conflicts           INTEGER DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    previous_state      JSONB,
    error_message       TEXT,
    started_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at        TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_ph_action CHECK (action IN ('PUBLISH', 'ROLLBACK', 'DRY_RUN')),
    CONSTRAINT chk_ph_status CHECK (status IN ('COMPLETED', 'FAILED', 'ROLLED_BACK'))
);

CREATE INDEX idx_ph_pipeline ON publish_history(pipeline_id);
CREATE INDEX idx_ph_bank ON publish_history(bank_id);
CREATE INDEX idx_ph_status ON publish_history(status);
CREATE INDEX idx_ph_started ON publish_history(started_at DESC);
```

### 4.9 Tabla: banks

Registro de bancos conocidos.

```sql
CREATE TABLE banks (
    bank_id             VARCHAR(50) PRIMARY KEY,
    bank_name           VARCHAR(200),
    description         TEXT,
    location_type       VARCHAR(30),
    is_active           BOOLEAN DEFAULT TRUE,
    first_scan_at       TIMESTAMP WITH TIME ZONE,
    last_scan_at        TIMESTAMP WITH TIME ZONE,
    total_works         INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_banks_active ON banks(is_active);
```

---

## 5. mce_app — Usuarios y Bot

**Propósito:** Datos de usuarios, wishlists y funcionalidades del Bot/Mini App.

**Ciclo de vida:** Permanente.

**Acceso:** QUERY SERVICE (lectura/escritura).

### 5.1 Tabla: users

Usuarios del sistema (Telegram).

```sql
CREATE TABLE users (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id         BIGINT UNIQUE,
    username            VARCHAR(100),
    display_name        VARCHAR(200),
    is_admin            BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN DEFAULT TRUE,
    preferred_banks     JSONB DEFAULT '[]',
    language            VARCHAR(10) DEFAULT 'es',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at      TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_telegram ON users(telegram_id);
CREATE INDEX idx_users_active ON users(is_active);
```

### 5.2 Tabla: wishlists

Lista de deseos de cada usuario.

```sql
CREATE TABLE wishlists (
    wishlist_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    work_id             UUID NOT NULL REFERENCES works(work_id),
    status              VARCHAR(20) DEFAULT 'PENDING',
    added_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notified_at         TIMESTAMP WITH TIME ZONE,
    notes               TEXT,

    CONSTRAINT uq_wishlist UNIQUE (user_id, work_id),
    CONSTRAINT chk_wl_status CHECK (status IN (
        'PENDING', 'AVAILABLE', 'WATCHED', 'REMOVED'
    ))
);

CREATE INDEX idx_wl_user ON wishlists(user_id);
CREATE INDEX idx_wl_work ON wishlists(work_id);
CREATE INDEX idx_wl_status ON wishlists(status);
```

### 5.3 Tabla: watch_history

Historial de visualización.

```sql
CREATE TABLE watch_history (
    history_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    work_id             UUID NOT NULL REFERENCES works(work_id),
    watched_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rating_given        SMALLINT,
    notes               TEXT,

    CONSTRAINT chk_wh_rating CHECK (rating_given IS NULL OR (rating_given >= 1 AND rating_given <= 10))
);

CREATE INDEX idx_wh_user ON watch_history(user_id);
CREATE INDEX idx_wh_work ON watch_history(work_id);
CREATE INDEX idx_wh_date ON watch_history(watched_at DESC);
```

### 5.4 Tabla: requests

Solicitudes de obras que los usuarios quieren que se añadan.

```sql
CREATE TABLE requests (
    request_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(user_id),
    title_requested     VARCHAR(500) NOT NULL,
    reason              TEXT,
    status              VARCHAR(20) DEFAULT 'PENDING',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at         TIMESTAMP WITH TIME ZONE,
    resolution_notes    TEXT,

    CONSTRAINT chk_req_status CHECK (status IN (
        'PENDING', 'APPROVED', 'REJECTED', 'FOUND', 'NOT_FOUND'
    ))
);

CREATE INDEX idx_req_user ON requests(user_id);
CREATE INDEX idx_req_status ON requests(status);
CREATE INDEX idx_req_created ON requests(created_at DESC);
```

### 5.5 Tabla: notifications

Notificaciones pendientes para usuarios.

```sql
CREATE TABLE notifications (
    notification_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type   VARCHAR(30) NOT NULL,
    title               VARCHAR(200) NOT NULL,
    message             TEXT NOT NULL,
    work_id             UUID REFERENCES works(work_id),
    is_read             BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at             TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_notif_type CHECK (notification_type IN (
        'WISHLIST_AVAILABLE', 'NEW_WORK', 'REQUEST_RESOLVED', 'SYSTEM'
    ))
);

CREATE INDEX idx_notif_user ON notifications(user_id);
CREATE INDEX idx_notif_read ON notifications(is_read);
CREATE INDEX idx_notif_created ON notifications(created_at DESC);
```

---

## 6. Enums Globales

```sql
-- Categorías de contenido
CREATE TYPE media_category AS ENUM (
    'Peliculas', 'Series', 'Novelas', 'Anime', 'Doramas', 'Animadas', 'Concursos'
);

-- Estados de obra en pipeline
CREATE TYPE work_pipeline_status AS ENUM (
    'VALIDATED', 'READY_FOR_PREPARE', 'PREPARING', 'PREPARED',
    'READY_FOR_ENRICHMENT', 'ENRICHING', 'APPROVED', 'APPROVED_PARTIAL',
    'HUMAN_REVIEW', 'NOT_FOUND', 'PREPARE_INSUFFICIENT',
    'READY_FOR_PUBLISH', 'PUBLISHING', 'PUBLISHED',
    'PUBLISH_CONFLICT', 'PUBLISH_FAILED', 'PROVIDER_ERROR', 'DEAD_LETTER'
);

-- Proveedores
CREATE TYPE provider_name AS ENUM (
    'tmdb', 'anilist', 'tvmaze', 'wikidata', 'wikipedia',
    'tavily', 'serper', 'exa', 'omdb', 'fanart_tv', 'groq', 'qwen'
);

-- Tipos de asset
CREATE TYPE asset_type AS ENUM ('poster', 'backdrop', 'logo', 'banner');

-- Acciones de publicación
CREATE TYPE publish_action AS ENUM (
    'CREATE', 'UPDATE_METADATA', 'ADD_AVAILABILITY',
    'REMOVE_AVAILABILITY', 'ARCHIVE'
);
```

---

## 7. Diagrama de Relaciones

```text
mce_master:

  banks ─────────────┐
                     │
  works ─────────────┼──→ availability ──→ banks
    │                │
    ├──→ aliases     │
    ├──→ metadata    │
    ├──→ external_ids│
    ├──→ assets      │
    └──→ physical_locations ──→ banks

  publish_history (auditoría independiente)


mce_app:

  users
    ├──→ wishlists ──→ works (mce_master)
    ├──→ watch_history ──→ works (mce_master)
    ├──→ requests
    └──→ notifications ──→ works (mce_master)


mce_cache:

  global_works
    └──→ asset_urls

  provider_responses (independiente)
  wikidata_cache (independiente)
  human_corrections (independiente)
  enrichment_stats (independiente)


mce_staging:

  pipeline_runs
    ├──→ work_states
    ├──→ checkpoints
    ├──→ contract_instances
    └──→ dead_letter_queue

  scan_snapshots (independiente)
```

---

## 8. Índices de Búsqueda Full-Text

Para el Query Service y el Bot:

```sql
-- Búsqueda combinada en works + aliases
CREATE OR REPLACE FUNCTION work_search_vector(w works, a aliases)
RETURNS tsvector AS $$
BEGIN
    RETURN
        setweight(to_tsvector('spanish', COALESCE(w.original_title, '')), 'A') ||
        setweight(to_tsvector('spanish', COALESCE(w.spanish_title, '')), 'A') ||
        setweight(to_tsvector('spanish', COALESCE(a.alias_text, '')), 'B');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Índice para búsqueda rápida
CREATE INDEX idx_works_search ON works
    USING GIN (to_tsvector('spanish', original_title || ' ' || COALESCE(spanish_title, '')));
```

---

## 9. Políticas de Retención

| Tabla | Retención | Limpieza |
|-------|-----------|----------|
| mce_staging.* | Hasta fin de pipeline | Automática al completar |
| mce_staging.checkpoints | Últimos 10 | Automática |
| mce_staging.dead_letter_queue | Hasta resolución | Manual |
| mce_cache.provider_responses | 30 días si expiró | Automática |
| mce_cache.global_works | Permanente | Nunca |
| mce_cache.human_corrections | Permanente | Nunca |
| mce_master.* | Permanente | Nunca |
| mce_app.notifications | 90 días si leídas | Automática |
| mce_app.watch_history | Permanente | Nunca |

---

## 10. Backup Strategy

```text
Diario:
  pg_dump mce_master > backup_master_$(date +%Y%m%d).sql
  pg_dump mce_cache > backup_cache_$(date +%Y%m%d).sql
  pg_dump mce_app > backup_app_$(date +%Y%m%d).sql

Semanal:
  Backup completo + verificación de integridad

WAL Archiving:
  Habilitado para mce_master (point-in-time recovery)

Retención:
  Diarios: 7 días
  Semanales: 4 semanas
  Mensuales: 12 meses
```

---

## 11. Reglas de Acceso por Módulo (Resumen)

```text
VALIDATE:
  READ:  mce_staging.scan_snapshots
  WRITE: mce_staging.pipeline_runs, mce_staging.work_states,
         mce_staging.contract_instances, mce_staging.scan_snapshots

PREPARE:
  READ:  mce_staging.contract_instances, mce_cache.global_works,
         mce_cache.human_corrections, mce_cache.wikidata_cache
  WRITE: mce_staging.contract_instances, mce_staging.work_states,
         mce_cache.wikidata_cache

ENRICH:
  READ:  mce_staging.contract_instances, mce_cache.provider_responses,
         mce_cache.global_works, mce_cache.asset_urls
  WRITE: mce_staging.contract_instances, mce_staging.work_states,
         mce_cache.provider_responses, mce_cache.global_works,
         mce_cache.asset_urls, mce_cache.enrichment_stats

PUBLISHER:
  READ:  mce_staging.contract_instances, mce_master.works,
         mce_master.external_ids, mce_master.availability
  WRITE: mce_master.works, mce_master.aliases, mce_master.metadata,
         mce_master.external_ids, mce_master.availability,
         mce_master.physical_locations, mce_master.assets,
         mce_master.publish_history, mce_master.banks,
         mce_staging.work_states

QUERY SERVICE:
  READ:  mce_master.*, mce_app.*
  WRITE: mce_app.users, mce_app.wishlists, mce_app.watch_history,
         mce_app.requests, mce_app.notifications
```
