from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
import uuid
from pathlib import Path
from datetime import datetime

from ..database import get_db
from ..config import settings
from .. import models, schemas

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Documento no encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Documento no encontrado"}
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {"detail": "Error procesando documento"}
                }
            }
        }
    }
)

@router.post(
    "/",
    response_model=schemas.Document,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo documento",
    description="Carga un nuevo documento en el sistema y registra su metadata",
    response_description="Retorna el documento creado con toda su metadata"
)
async def create_document(
    file: UploadFile = File(
        ...,
        description="Archivo a subir (cualquier formato)"
    ),
    name: str = Form(
        ...,
        description="Nombre descriptivo para el documento",
        example="Informe Técnico 2024"
    ),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo documento en el sistema:
    
    - **file**: Archivo a subir (PDF, DOCX, TXT, etc.)
    - **name**: Nombre descriptivo para identificar el documento
    
    El sistema:
    1. Valida y procesa el archivo subido
    2. Genera un ID único para el documento
    3. Guarda el archivo en el sistema de archivos
    4. Registra la metadata en la base de datos
    
    Retorna:
    - La metadata completa del documento creado
    - ID único para futuras referencias
    - Rutas de acceso
    - Timestamps de creación
    """
    try:
        # Generar ID único
        doc_id = str(uuid.uuid4())
        
        # Crear subdirectorio basado en el ID
        sub_dir = Path(settings.REPOSITORY_PATH) / doc_id[:2]
        sub_dir.mkdir(parents=True, exist_ok=True)
        
        # Procesar el archivo
        original_filename = file.filename
        ext = Path(original_filename).suffix or '.txt'
        local_path = sub_dir / f"{doc_id}{ext}"
        
        # Guardar el archivo
        with local_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Crear registro en base de datos
        db_document = models.Document(
            id=doc_id,
            name=name,
            original_filename=original_filename,
            local_path=str(local_path),
            status="pending"
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
        
    except Exception as e:
        if 'local_path' in locals() and Path(local_path).exists():
            Path(local_path).unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando documento: {str(e)}"
        )
    finally:
        await file.close()

@router.get(
    "/",
    response_model=List[schemas.Document],
    summary="Listar documentos",
    description="Obtiene una lista paginada de todos los documentos en el sistema",
    response_description="Lista de documentos con su metadata"
)
def read_documents(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Recupera una lista de documentos del sistema.
    
    Parámetros:
    - **skip**: Número de documentos a saltar (para paginación)
    - **limit**: Número máximo de documentos a retornar
    - **status**: Filtrar por estado del documento (pending, processed, error)
    
    El sistema:
    1. Consulta la base de datos aplicando los filtros
    2. Pagina los resultados según los parámetros
    3. Retorna la lista de documentos encontrados
    
    Retorna:
    Lista de documentos, cada uno con su metadata completa
    """
    query = db.query(models.Document)
    if status:
        query = query.filter(models.Document.status == status)
    return query.offset(skip).limit(limit).all()

@router.get(
    "/{document_id}",
    response_model=schemas.Document,
    summary="Obtener documento específico",
    description="Obtiene la metadata de un documento específico por su ID",
    response_description="Metadata completa del documento"
)
def read_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Recupera la información de un documento específico.
    
    Parámetros:
    - **document_id**: ID único del documento
    
    El sistema:
    1. Busca el documento en la base de datos
    2. Verifica su existencia
    3. Retorna toda su metadata
    
    Retorna:
    Metadata completa del documento solicitado
    """
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    return document

@router.get(
    "/{document_id}/download",
    summary="Descargar documento",
    description="Descarga el archivo original del documento",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"application/octet-stream": {}},
            "description": "El archivo del documento"
        }
    }
)
async def download_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Descarga el archivo original de un documento.
    
    Parámetros:
    - **document_id**: ID único del documento
    
    El sistema:
    1. Verifica la existencia del documento
    2. Localiza el archivo en el sistema de archivos
    3. Prepara el archivo para descarga
    
    Retorna:
    El archivo original para descarga, manteniendo su nombre original
    """
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    file_path = Path(document.local_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el sistema"
        )
    
    return FileResponse(
        file_path,
        filename=document.original_filename,
        media_type="application/octet-stream"
    )

@router.delete(
    "/{document_id}",
    summary="Eliminar documento",
    description="Elimina un documento y su archivo asociado",
    response_description="Confirmación de eliminación"
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Elimina un documento y su archivo asociado del sistema.
    
    Parámetros:
    - **document_id**: ID único del documento a eliminar
    
    El sistema:
    1. Verifica la existencia del documento
    2. Elimina el archivo físico
    3. Elimina el registro de la base de datos
    4. Limpia directorios vacíos si es necesario
    
    Retorna:
    Mensaje de confirmación de la eliminación
    """
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    try:
        # Eliminar archivo físico
        file_path = Path(document.local_path)
        if file_path.exists():
            file_path.unlink()
            # Limpiar directorio si está vacío
            if not any(file_path.parent.iterdir()):
                file_path.parent.rmdir()
        
        # Eliminar registro
        db.delete(document)
        db.commit()
        
        return {
            "message": f"Documento {document_id} eliminado correctamente",
            "name": document.name,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar documento: {str(e)}"
        )