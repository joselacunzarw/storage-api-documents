from pathlib import Path
import shutil
import uuid
import aiohttp
from fastapi import HTTPException
import asyncio
import os

class DocumentHandler:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def download_and_save(self, url: str, name: str) -> tuple[str, str]:
        """
        Descarga un documento y lo guarda en el repositorio.
        Retorna: (id, ruta_local)
        """
        doc_id = str(uuid.uuid4())
        # Crear subdirectorio usando los primeros caracteres del ID
        sub_dir = self.base_path / doc_id[:2]
        sub_dir.mkdir(exist_ok=True)
        
        # Determinar extensión del archivo original
        ext = os.path.splitext(url)[1] or '.txt'
        if not ext.startswith('.'):
            ext = '.' + ext
            
        local_path = sub_dir / f"{doc_id}{ext}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"No se pudo descargar el documento. Status: {response.status}"
                        )
                    
                    content = await response.read()
                    with open(local_path, 'wb') as f:
                        f.write(content)

            return doc_id, str(local_path)
        except Exception as e:
            if local_path.exists():
                local_path.unlink()
            raise HTTPException(
                status_code=500, 
                detail=f"Error procesando documento: {str(e)}"
            )

    def delete_document(self, local_path: str):
        """Elimina un documento del repositorio"""
        try:
            path = Path(local_path)
            if path.exists():
                path.unlink()
                # Eliminar directorio si está vacío
                if not any(path.parent.iterdir()):
                    path.parent.rmdir()
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error eliminando documento: {str(e)}"
            )

    def get_document_size(self, local_path: str) -> int:
        """Retorna el tamaño del documento en bytes"""
        try:
            return Path(local_path).stat().st_size
        except Exception:
            return 0