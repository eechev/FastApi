import logging
import tempfile
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from storeapi.libs.b2 import b2_upload_file
from storeapi.models.user import User
from storeapi.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile, current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info(
                f"User is saving uploaded file temporarily to {filename}",
                extra={"email": current_user.email},
            )
            async with aiofiles.open(filename, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)
            file_url = b2_upload_file(
                local_file=filename,
                file_name=file.filename or "",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        )

    return {
        "detail": f"Successfully uploaded file {file.filename}",
        "file_url": file_url,
    }
