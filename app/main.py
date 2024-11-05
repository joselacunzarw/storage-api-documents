from fastapi import FastAPI, HTTPException
from .routes import health, documents
from .database import verify_db_state
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verificar el estado de la base de datos
if not verify_db_state():
    logger.error("Error en el estado de la base de datos, iniciando reinicialización...")
    from .database import init_database
    init_database()

app = FastAPI(
    title="API Documentos",
    description="API REST para gestión de documentos con soporte para embeddings",
    version="1.0.0"
)

# Incluir los routers
app.include_router(health.router)
app.include_router(documents.router)

@app.on_event("startup")
async def startup_event():
    """Verificaciones de inicio"""
    logger.info("Iniciando API de Documentos...")
    if not verify_db_state():
        logger.error("Estado de la base de datos incorrecto")
        raise HTTPException(
            status_code=500,
            detail="Error en el estado de la base de datos"
        )
    logger.info("Sistema iniciado correctamente")