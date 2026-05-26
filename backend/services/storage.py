import aiofiles
import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
    ) -> dict:
        user_dir = self.storage_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        dest_path = user_dir / f"{timestamp}_{safe_filename}"

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(file_content)

        checksum = hashlib.sha256(file_content).hexdigest()

        return {
            "path": str(dest_path),
            "size": len(file_content),
            "checksum": checksum,
            "filename": safe_filename,
        }

    async def download_file(self, file_path: str) -> Optional[bytes]:
        path = Path(file_path)
        if not path.exists():
            return None
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> bool:
        path = Path(file_path)
        if path.exists():
            os.remove(path)
            return True
        return False

    def list_user_files(self, user_id: str) -> list:
        user_dir = self.storage_path / user_id
        if not user_dir.exists():
            return []

        files = []
        for f in user_dir.iterdir():
            if f.is_file():
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return files

    def get_file_info(self, file_path: str) -> Optional[dict]:
        path = Path(file_path)
        if not path.exists():
            return None
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }


storage_service = StorageService()
