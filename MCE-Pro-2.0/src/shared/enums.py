"""
Enums globales de MCE Pro 2.0

Definiciones centralizadas de categorías, estados y proveedores.
"""

from enum import StrEnum, auto


class Categoria(StrEnum):
    """Categorías de obras multimedia soportadas."""
    PELICULAS = "Peliculas"
    SERIES = "Series"
    NOVELAS = "Novelas"
    ANIME = "Anime"
    DORAMAS = "Doramas"
    ANIMADAS = "Animadas"
    CONCURSOS = "Concursos"


class ContentType(StrEnum):
    """Tipos de contenido para clasificación de archivos."""
    MEDIA = "MEDIA"
    SUBTITLE = "SUBTITLE"
    METADATA = "METADATA"
    EXTRA_CONTENT = "EXTRA_CONTENT"
    NOISE = "NOISE"
    REVIEW = "REVIEW"
    UNKNOWN = "UNKNOWN"


class MediaTypeHint(StrEnum):
    """Pistas del tipo de medio."""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SUBTITLE = "subtitle"
    METADATA = "metadata"
    EXTRA = "extra"
    SYSTEM = "system"
    OTHER = "other"


class ValidateStatus(StrEnum):
    """Estados de validación de escaneos."""
    VALIDATED = "VALIDATED"
    VALIDATED_WITH_WARNINGS = "VALIDATED_WITH_WARNINGS"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    ANOMALOUS_SCAN = "ANOMALOUS_SCAN"


class PrepareStatus(StrEnum):
    """Estados de preparación de obras."""
    READY_FOR_ENRICHMENT = "READY_FOR_ENRICHMENT"
    PREPARE_INSUFFICIENT = "PREPARE_INSUFFICIENT"
    CLASSIFICATION_REVIEW = "CLASSIFICATION_REVIEW"
    PREPARE_REVIEW = "PREPARE_REVIEW"


class EnrichStatus(StrEnum):
    """Estados de enriquecimiento de obras."""
    READY_FOR_PUBLISH = "READY_FOR_PUBLISH"
    APPROVED_PARTIAL = "APPROVED_PARTIAL"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    NOT_FOUND = "NOT_FOUND"
    PREPARE_INSUFFICIENT = "PREPARE_INSUFFICIENT"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class PublishStatus(StrEnum):
    """Estados de publicación de obras."""
    PUBLISHED = "PUBLISHED"
    PUBLISH_CONFLICT = "PUBLISH_CONFLICT"
    PUBLISH_FAILED = "PUBLISH_FAILED"
    PENDING_ASSETS = "PENDING_ASSETS"
    POSSIBLY_MISSING = "POSSIBLY_MISSING"


class PipelineStatus(StrEnum):
    """Estados de ejecución del pipeline."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ProviderType(StrEnum):
    """Tipos de proveedores de metadatos."""
    TMDB = "tmdb"
    ANILIST = "anilist"
    TVMAZE = "tvmaze"
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    TAVILY = "tavily"
    SERPER = "serper"
    EXA = "exa"
    GROQ = "groq"
    OLLAMA = "ollama"
    OMDb = "omdb"


class ConflictType(StrEnum):
    """Tipos de conflictos en publicación."""
    DATA_STABLE_CONFLICT = "DATA_STABLE_CONFLICT"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    AVAILABILITY_CONFLICT = "AVAILABILITY_CONFLICT"


class AnomalySeverity(StrEnum):
    """Severidad de anomalías detectadas."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class ActionType(StrEnum):
    """Tipos de acción en publicación."""
    CREATE = "CREATE"
    ADD_AVAILABILITY = "ADD_AVAILABILITY"
    REMOVE_AVAILABILITY = "REMOVE_AVAILABILITY"
    ARCHIVE = "ARCHIVE"
    UPDATE_METADATA = "UPDATE_METADATA"
