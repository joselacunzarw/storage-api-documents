# Storage API para Documentos

API REST desarrollada con FastAPI para almacenamiento y gestión de documentos, preparada para integración con sistemas de embeddings.

## 📋 Descripción

Esta API proporciona un sistema completo para el almacenamiento y gestión de documentos con las siguientes características:

- Almacenamiento seguro de documentos
- Gestión de metadata
- Sistema de monitoreo de salud
- Preparación para integración con sistemas de embeddings
- Almacenamiento en SQLite con persistencia de datos

### Estructura del Proyecto

```
proyecto/
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuraciones y variables de entorno
│   ├── database.py          # Configuración de la base de datos
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Schemas Pydantic
│   └── routes/
│       ├── __init__.py
│       ├── documents.py     # Endpoints de documentos
│       └── health.py        # Endpoint de monitoreo
├── data/
│   ├── documents/           # Almacenamiento de documentos
│   └── documents.db         # Base de datos SQLite
├── .env                     # Variables de entorno
├── docker-compose.yml       # Configuración de Docker
├── Dockerfile              # Definición de la imagen Docker
└── requirements.txt        # Dependencias Python
```

## 🚀 Instalación

### Prerrequisitos

- Docker
- Docker Compose

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd [NOMBRE_DEL_DIRECTORIO]
```

2. Crear archivo .env:
```env
DATABASE_URL=sqlite:///./data/documents.db
REPOSITORY_PATH=./data/documents
OPENAI_API_KEY=apikey
```

3. Crear directorios necesarios:
```bash
mkdir -p data/documents
```

4. Construir y levantar los contenedores:
```bash
docker-compose build
docker-compose up -d
```

## 🔧 Uso

### Endpoints Disponibles

#### Documentos

- `POST /documents/` - Subir nuevo documento
- `GET /documents/` - Listar documentos
- `GET /documents/{document_id}` - Obtener documento específico
- `GET /documents/{document_id}/download` - Descargar documento
- `DELETE /documents/{document_id}` - Eliminar documento

#### Monitoreo

- `GET /health` - Estado del sistema

### Ejemplos de Uso

#### Subir Documento
```bash
curl -X POST "http://localhost:8000/documents/" \
  -H "accept: application/json" \
  -F "file=@/path/to/your/document.pdf" \
  -F "name=Documento de prueba"
```

#### Listar Documentos
```bash
curl -X GET "http://localhost:8000/documents/" \
  -H "accept: application/json"
```

#### Descargar Documento
```bash
curl -X GET "http://localhost:8000/documents/{id}/download" \
  --output documento.pdf
```

## 🔍 Monitoreo

El endpoint `/health` proporciona información detallada sobre:

- Estado del sistema (CPU, memoria, disco)
- Conexión a la base de datos
- Estado del repositorio de documentos
- Estadísticas de documentos

Ejemplo de respuesta de health:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-05T00:00:00.000Z",
  "checks": {
    "system": {
      "status": "healthy",
      "info": {
        "cpu_percent": 25.5,
        "memory": {
          "total_gb": 16.0,
          "available_gb": 8.5,
          "percent_used": 47.5
        }
      }
    },
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    }
  }
}
```

## 📊 Base de Datos

El sistema utiliza SQLite con las siguientes características:

- Autogestión de esquema
- Verificación de integridad
- Recreación automática si es necesario

### Estructura de la Base de Datos

Tabla `documents`:
- `id` (UUID): Identificador único
- `name`: Nombre descriptivo
- `original_filename`: Nombre original del archivo
- `local_path`: Ruta de almacenamiento
- `status`: Estado del documento (pending, processed, error)
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

## 🛠️ Desarrollo

### Requisitos de Desarrollo

- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic
- Docker

### Configuración del Entorno de Desarrollo

1. Crear entorno virtual:
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
env\Scripts\activate    # Windows
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### Pruebas Locales

1. Ejecutar servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

2. Acceder a la documentación:
```
http://localhost:8000/docs
```

## 📝 Notas Importantes

- Los documentos se almacenan en subdirectorios basados en su ID
- La base de datos se autocrea si no existe
- El sistema verifica y mantiene la integridad del esquema
- Los archivos y la base de datos persisten entre reinicios

## 🔐 Seguridad

- Validación de tipos de archivo
- Manejo seguro de archivos
- Verificación de permisos de escritura
- Limpieza automática en caso de errores

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia [LICENCIA]. Ver el archivo `LICENSE` para más detalles.
