from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

Base = declarative_base()

def check_table_schema(inspector, table_name, expected_columns):
    """Verifica si una tabla tiene las columnas esperadas"""
    if not inspector.has_table(table_name):
        return False
    
    existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
    required_columns = set(expected_columns)
    
    return required_columns.issubset(existing_columns)

def init_database():
    """
    Inicializa o reinicia la base de datos si el esquema no es correcto.
    """
    try:
        # Extraer la ruta del archivo de la URL de conexión
        db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Crear engine
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
        )

        # Importar modelos para tener acceso a las definiciones de tablas
        from . import models

        # Verificar esquema si la base de datos existe
        if db_path.exists():
            inspector = inspect(engine)
            expected_columns = [
                'id', 'name', 'original_filename', 'local_path', 
                'status', 'created_at', 'updated_at'
            ]
            
            if not check_table_schema(inspector, 'documents', expected_columns):
                logger.warning("Esquema incorrecto detectado, recreando base de datos...")
                # Cerrar todas las conexiones
                engine.dispose()
                # Eliminar base de datos existente
                os.remove(db_path)
                # Crear nuevo engine
                engine = create_engine(
                    settings.DATABASE_URL,
                    connect_args={"check_same_thread": False}
                )
                # Crear tablas
                Base.metadata.create_all(bind=engine)
                logger.info("Base de datos recreada con el esquema correcto")
            else:
                logger.info("Esquema de base de datos verificado correctamente")
        else:
            # Crear tablas si es una nueva base de datos
            Base.metadata.create_all(bind=engine)
            logger.info("Nueva base de datos creada con el esquema correcto")

        return engine

    except Exception as e:
        logger.error(f"Error en la inicialización de la base de datos: {str(e)}")
        raise

# Inicializar engine y sesión
engine = init_database()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency para obtener la sesión de DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_db_state():
    """Verifica el estado completo de la base de datos"""
    try:
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result != 1:
                return False
        
        # Verificar esquema
        inspector = inspect(engine)
        expected_columns = [
            'id', 'name', 'original_filename', 'local_path', 
            'status', 'created_at', 'updated_at'
        ]
        
        return check_table_schema(inspector, 'documents', expected_columns)

    except Exception as e:
        logger.error(f"Error verificando estado de la base de datos: {str(e)}")
        return False