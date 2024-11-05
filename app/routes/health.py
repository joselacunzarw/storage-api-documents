from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from pathlib import Path
import shutil
import psutil
import os

from ..database import get_db
from ..config import settings
from .. import models

router = APIRouter()

def get_system_info():
    """Obtiene información del sistema"""
    virtual_memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total_gb": round(virtual_memory.total / (1024**3), 2),
            "available_gb": round(virtual_memory.available / (1024**3), 2),
            "percent_used": virtual_memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": disk.percent
        }
    }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Verifica el estado de todos los componentes del sistema:
    - Estado del sistema (CPU, memoria, disco)
    - Conexión a la base de datos
    - Acceso al repositorio de documentos
    - Estado de los documentos
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # 1. Verificar sistema
    try:
        system_info = get_system_info()
        health_status["checks"]["system"] = {
            "status": "healthy",
            "info": system_info
        }

        # Advertencias de recursos
        if system_info["cpu_percent"] > 80:
            health_status["checks"]["system"]["status"] = "warning"
            health_status["checks"]["system"]["message"] = "High CPU usage"
        
        if system_info["memory"]["percent_used"] > 80:
            health_status["checks"]["system"]["status"] = "warning"
            health_status["checks"]["system"]["message"] = "High memory usage"
        
        if system_info["disk"]["percent_used"] > 80:
            health_status["checks"]["system"]["status"] = "warning"
            health_status["checks"]["system"]["message"] = "Low disk space"

    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 2. Verificar base de datos
    try:
        result = db.execute(text("SELECT 1"))
        result.scalar()
        
        # Obtener estadísticas de la base de datos
        total_docs = db.query(models.Document).count()
        stats = {
            "total_documents": total_docs,
            "by_status": {}
        }
        
        # Contar documentos por status
        for status in ["pending", "processed", "error"]:
            count = db.query(models.Document).filter(
                models.Document.status == status
            ).count()
            stats["by_status"][status] = count

        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
            "statistics": stats
        }

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 3. Verificar repositorio de documentos
    try:
        repo_path = Path(settings.REPOSITORY_PATH)
        if not repo_path.exists():
            repo_path.mkdir(parents=True, exist_ok=True)
        
        # Verificar permisos de escritura
        test_file = repo_path / ".test_write"
        test_file.touch()
        test_file.unlink()
        
        # Verificar espacio en disco del repositorio
        disk_usage = shutil.disk_usage(repo_path)
        free_gb = disk_usage.free // (2**30)  # Convertir a GB
        total_gb = disk_usage.total // (2**30)
        used_gb = disk_usage.used // (2**30)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        health_status["checks"]["repository"] = {
            "status": "healthy",
            "path": str(repo_path),
            "permissions": "read-write",
            "storage": {
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "used_percent": round(used_percent, 2)
            }
        }
        
        if used_percent > 80:
            health_status["checks"]["repository"]["status"] = "warning"
            health_status["checks"]["repository"]["message"] = f"Storage usage high: {round(used_percent, 2)}%"
        
        if free_gb < 1:
            health_status["checks"]["repository"]["status"] = "warning"
            health_status["checks"]["repository"]["message"] = f"Low storage: {free_gb}GB remaining"
    
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["repository"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 4. Verificar documentos con errores
    try:
        error_docs = db.query(models.Document).filter(
            models.Document.status == "error"
        ).count()
        
        health_status["checks"]["documents"] = {
            "status": "healthy",
            "error_count": error_docs
        }
        
        if error_docs > 0:
            health_status["checks"]["documents"]["status"] = "warning"
            health_status["checks"]["documents"]["message"] = f"{error_docs} documents in error state"
    
    except Exception as e:
        health_status["checks"]["documents"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Determinar estado general
    if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)
    elif any(check["status"] == "warning" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status