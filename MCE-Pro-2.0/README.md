# 🚀 MCE Pro 2.0

**Media Cleaner & Enrichment** - Sistema de normalización, identificación y enriquecimiento multimedia.

## 📖 Descripción

MCE Pro 2.0 transforma escaneos brutos de bancos de contenido multimedia en un Catálogo Maestro confiable, estructurado y deduplicado.

## 🏗️ Arquitectura

El sistema sigue una arquitectura de pipeline con las siguientes etapas:

1. **Validar** - Verifica integridad de escaneos brutos
2. **Prepare** - Normaliza y agrupa datos por obra
3. **Enrich** - Enriquece con metadatos externos (TMDB, AniList, etc.)
4. **Publisher** - Publica al catálogo maestro en PostgreSQL

## 📁 Estructura del Proyecto

```
MCE-Pro-2.0/
├── src/              # Código fuente principal
├── tests/            # Tests unitarios e integración
├── contracts/        # Esquemas JSON de contratos
├── instrucciones/    # Documentación técnica
├── config/           # Configuraciones YAML
├── scripts/          # Scripts utilitarios
└── docs/             # Documentación ADR y diagramas
```

## 🚀 Inicio Rápido

```bash
# Clonar repositorio
git clone <repo-url>
cd MCE-Pro-2.0

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o .\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -e ".[dev]"

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar tests
pytest tests/ -v
```

## 📋 Requisitos

- Python 3.12 - 3.13
- PostgreSQL 15+
- API Keys: TMDB, AniList, Tavily (opcionales)

## 🧪 Testing

```bash
# Todos los tests
pytest tests/ -v

# Solo unitarios
pytest tests/ -v -m "not integration"

# Con coverage
pytest tests/ --cov=src --cov-report=html
```

## 📄 Licencia

MIT License
