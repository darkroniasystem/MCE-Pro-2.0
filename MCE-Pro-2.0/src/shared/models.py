"""
Modelos Pydantic para los contratos de MCE Pro 2.0

Validación de datos entre módulos usando Pydantic v2.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from .enums import (
    Categoria,
    ContentType,
    MediaTypeHint,
    ValidateStatus,
    PrepareStatus,
    EnrichStatus,
    PublishStatus,
    AnomalySeverity,
)


# =============================================================================
# Modelos Base
# =============================================================================

class CommonFields(BaseModel):
    """Campos comunes a todos los contratos."""
    
    schema_version: int = Field(ge=1, description="Versión del contrato")
    pipeline_id: str = Field(..., min_length=1, description="ID único de ejecución")
    scan_id: str = Field(..., min_length=1, description="ID único del escaneo")
    bank_id: str = Field(..., min_length=1, max_length=50, description="ID del banco")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    status: str = Field(..., description="Estado actual")

    @field_validator("bank_id")
    @classmethod
    def validate_bank_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("bank_id no puede estar vacío")
        return v.strip()


# =============================================================================
# Contrato 1: RawScanPackage
# =============================================================================

class Record(BaseModel):
    """Registro individual de archivo escaneado."""
    
    record_id: str
    file_path: str
    file_name: str
    folder_path: str
    parent_folders: list[str]
    extension: str
    size_bytes: int = Field(ge=0)
    modified_at: datetime
    created_at: Optional[datetime] = None
    hash_sha256: Optional[str] = None
    fingerprint: Optional[str] = None
    drive_letter: str
    is_symlink: Optional[bool] = False
    is_hidden: Optional[bool] = False

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        if not v.startswith(("C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:", "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:", "Z:", "/")):
            raise ValueError("file_path debe ser ruta absoluta")
        return v

    @field_validator("extension")
    @classmethod
    def validate_extension(cls, v: str) -> str:
        if not v.startswith("."):
            raise ValueError("extension debe incluir el punto (.mkv)")
        return v.lower()


class RawScanPackage(CommonFields):
    """Paquete de escaneo crudo de MSL."""
    
    source: str = "MSL"
    scanner_version: str
    source_folder: str
    section_name: str
    scan_started_at: datetime
    scan_completed_at: datetime
    records: list[Record]
    total_records: int
    total_size_bytes: int = Field(ge=0)

    @field_validator("total_records")
    @classmethod
    def validate_total_records(cls, v: int, info) -> int:
        if v < 1:
            raise ValueError("total_records debe ser >= 1")
        return v

    @field_validator("records")
    @classmethod
    def validate_records(cls, v: list[Record], info) -> list[Record]:
        if len(v) < 1:
            raise ValueError("records no puede estar vacío")
        return v


# =============================================================================
# Contrato 2: ValidatedScanPackage
# =============================================================================

class Snapshot(BaseModel):
    """Snapshot de cambios respecto al escaneo anterior."""
    
    total_files: int
    new: int = Field(ge=0)
    modified: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    missing: int = Field(ge=0)
    previous_scan_id: Optional[str] = None
    previous_scan_date: Optional[datetime] = None


class Anomaly(BaseModel):
    """Anomalía detectada durante validación."""
    
    anomaly_id: str
    type: str
    severity: AnomalySeverity
    description: str
    affected_records: list[str]
    recommendation: str


class ValidatedScanPackage(CommonFields):
    """Paquete de escaneo validado."""
    
    section_name: str
    category: Categoria
    scan_hash: str
    validation_status: ValidateStatus
    validated_at: datetime
    snapshot: Optional[Snapshot] = None
    anomalies: list[Anomaly] = []
    warnings: list[str] = []
    records: list[Record]
    total_records: int
    valid_records: int
    invalid_records: int = 0


# =============================================================================
# Contrato 3: PreparedWorkPackage
# =============================================================================

class Titles(BaseModel):
    """Candidatos de títulos para una obra."""
    
    primary_local: str
    original_candidate: Optional[str] = None
    alternatives: list[str] = []


class PhysicalOccurrence(BaseModel):
    """Ocurrencia física de una obra."""
    
    file_path: str
    file_name: str
    folder_path: str
    parent_folders: list[str]
    size_bytes: int
    extension: str
    content_type: ContentType
    media_type_hint: MediaTypeHint
    is_primary: bool = True


class LocalEvidence(BaseModel):
    """Evidencia local recopilada."""
    
    source: str  # folder, filename, nfo
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class WikimediaEvidence(BaseModel):
    """Evidencia de Wikimedia."""
    
    source: str  # wikidata, wikipedia
    url: str
    title: str
    year: Optional[int] = None
    type: Optional[str] = None
    external_ids: dict[str, str] = {}
    aliases: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)


class StructureInfo(BaseModel):
    """Información sobre estructura especial."""
    
    is_dvd: bool = False
    seasons_seen: list[int] = []
    has_video_ts: bool = False
    loose_files: int = 0


class PreparedWorkPackage(CommonFields):
    """Paquete de obra preparada para enriquecimiento."""
    
    logical_work_id: str
    titles: Titles
    possible_year: Optional[int] = Field(None, ge=1888, le=2030)
    category: Categoria
    local_evidence: list[LocalEvidence] = []
    wikimedia_evidence: list[WikimediaEvidence] = []
    possible_external_ids: dict[str, str] = {}
    physical_occurrences: list[PhysicalOccurrence] = []
    structure: Optional[StructureInfo] = None
    prepare_confidence: float = Field(ge=0.0, le=1.0)
    status: PrepareStatus = PrepareStatus.READY_FOR_ENRICHMENT


# =============================================================================
# Contrato 4: EnrichedWorkPackage
# =============================================================================

class Identity(BaseModel):
    """Identidad confirmada de la obra."""
    
    original_title: str
    spanish_title: Optional[str] = None
    year: int = Field(ge=1888, le=2030)
    category: Categoria
    media_type: str  # movie, tv, anime, etc.
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    anilist_id: Optional[int] = None
    wikidata_id: Optional[str] = None


class Metadata(BaseModel):
    """Metadatos enriquecidos."""
    
    synopsis: Optional[str] = None
    genres: list[str] = []
    director: Optional[str] = None
    cast: list[str] = []
    rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    runtime: Optional[int] = Field(None, ge=1, le=600)
    country: Optional[str] = None
    language: Optional[str] = None
    seasons: Optional[int] = Field(None, ge=1)
    episodes: Optional[int] = Field(None, ge=1)


class AssetCandidate(BaseModel):
    """Candidato a asset (poster/backdrop)."""
    
    asset_type: str  # poster, backdrop
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    provider: str


class FieldProvenance(BaseModel):
    """Procedencia de un campo."""
    
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    fetched_at: datetime


class EnrichedWorkPackage(CommonFields):
    """Paquete de obra enriquecida."""
    
    logical_work_id: str
    identity: Identity
    metadata: Metadata
    external_ids: dict[str, str]
    physical_occurrences: list[PhysicalOccurrence]
    asset_candidates: list[AssetCandidate] = []
    field_provenance: dict[str, FieldProvenance] = {}
    identity_confidence: float = Field(ge=0.0, le=1.0)
    metadata_completeness: float = Field(ge=0.0, le=1.0)
    enrichment_notes: list[str] = []
    status: EnrichStatus


# =============================================================================
# Contrato 5: PublishCommand
# =============================================================================

class PublishAction(BaseModel):
    """Acción a ejecutar en publicación."""
    
    action_type: str  # CREATE, ADD_AVAILABILITY, etc.
    logical_work_id: str
    work_data: Optional[dict] = None
    availability_data: Optional[dict] = None
    reason: str


class Conflict(BaseModel):
    """Conflicto detectado en publicación."""
    
    conflict_type: str
    field: str
    existing_value: str
    new_value: str
    recommendation: str


class PublishCommand(CommonFields):
    """Comando de publicación al Master."""
    
    actions: list[PublishAction]
    conflicts: list[Conflict] = []
    preflight_passed: bool = True
    batch_number: Optional[int] = None
    total_batches: Optional[int] = None
    status: PublishStatus
