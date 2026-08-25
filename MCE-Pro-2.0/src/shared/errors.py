"""
Tipos de error personalizados para MCE Pro 2.0

Jerarquía de errores para manejo consistente en todos los módulos.
"""


class MCEError(Exception):
    """Error base para todas las excepciones de MCE Pro 2.0."""
    
    def __init__(self, message: str, module: str | None = None):
        self.message = message
        self.module = module
        super().__init__(self.message)


# =============================================================================
# Errores de VALIDATE
# =============================================================================

class ValidationError(MCEError):
    """Error durante la validación de un escaneo."""
    
    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message, module="VALIDATE")


class JSONParseError(ValidationError):
    """Error al parsear JSON de MSL."""
    pass


class StructuralValidationError(ValidationError):
    """Error en validación estructural del schema."""
    pass


class ContentValidationError(ValidationError):
    """Error en validación de contenido."""
    pass


class CategoryDetectionError(ValidationError):
    """Error al detectar categoría automáticamente."""
    pass


# =============================================================================
# Errores de PREPARE
# =============================================================================

class PrepareError(MCEError):
    """Error durante la preparación de obras."""
    
    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message, module="PREPARE")


class TitleCleaningError(PrepareError):
    """Error al limpiar títulos."""
    pass


class GroupingError(PrepareError):
    """Error al agrupar archivos en obras lógicas."""
    pass


class WikimediaError(PrepareError):
    """Error en consulta a Wikimedia."""
    pass


class ClassificationError(PrepareError):
    """Error al clasificar obras."""
    pass


# =============================================================================
# Errores de ENRICH
# =============================================================================

class EnrichError(MCEError):
    """Error durante el enriquecimiento de obras."""
    
    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message, module="ENRICH")


class CacheError(EnrichError):
    """Error en operaciones de caché."""
    pass


class ProviderError(EnrichError):
    """Error en proveedor de metadatos."""
    
    def __init__(self, message: str, provider: str, details: dict | None = None):
        self.provider = provider
        self.details = details or {}
        super().__init__(message, details)


class RateLimitError(ProviderError):
    """Proveedor alcanzó límite de rate limiting."""
    pass


class CircuitBreakerError(ProviderError):
    """Circuit breaker activado para el proveedor."""
    pass


class AIAnalysisError(EnrichError):
    """Error en análisis con IA."""
    pass


class HallucinationError(AIAnalysisError):
    """IA inventó datos o URLs."""
    pass


class ValidationError(EnrichError):
    """Validador determinista rechazó resultado."""
    pass


# =============================================================================
# Errores de PUBLISHER
# =============================================================================

class PublisherError(MCEError):
    """Error durante la publicación al catálogo maestro."""
    
    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message, module="PUBLISHER")


class PreflightError(PublisherError):
    """Error en checks preflight."""
    pass


class DeduplicationError(PublisherError):
    """Error en deduplicación de obras."""
    pass


class TransactionError(PublisherError):
    """Error en transacción de base de datos."""
    pass


class RollbackError(PublisherError):
    """Error al revertir publicación."""
    pass


class ConflictError(PublisherError):
    """Conflicto detectado en publicación."""
    
    def __init__(self, message: str, conflict_type: str, details: dict | None = None):
        self.conflict_type = conflict_type
        self.details = details or {}
        super().__init__(message, details)


class AssetError(PublisherError):
    """Error en descarga o validación de assets."""
    pass


# =============================================================================
# Errores de Shared Kernel
# =============================================================================

class ConfigError(MCEError):
    """Error en configuración del sistema."""
    pass


class ContractError(MCEError):
    """Error en validación de contratos."""
    pass


class StateMachineError(MCEError):
    """Error en transición de estados."""
    pass


class DatabaseError(MCEError):
    """Error en operaciones de base de datos."""
    
    def __init__(self, message: str, db_name: str | None = None):
        self.db_name = db_name
        super().__init__(message, module="DATABASE")
