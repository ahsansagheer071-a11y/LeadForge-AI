import os
import asyncio
from typing import Dict, Any
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ServiceUnavailableException

# Configure cloudinary using settings if available
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

class CloudinaryService:
    async def upload_image(self, file_path: str, folder: str = "leadforge_screenshots") -> Dict[str, Any]:
        """
        Uploads an image to Cloudinary asynchronously, with 1 retry on failure.
        Deletes the local file upon successful upload.
        """
        if not settings.CLOUDINARY_CLOUD_NAME:
            logger.warning("Cloudinary is not configured. Skipping upload.")
            return {}

        if not os.path.exists(file_path):
            logger.error(f"File not found for upload: {file_path}")
            return {}

        max_retries = 1
        attempt = 0
        
        while attempt <= max_retries:
            try:
                # cloudinary.uploader.upload is synchronous, so we run it in a thread
                result = await asyncio.to_thread(
                    cloudinary.uploader.upload,
                    file_path,
                    folder=folder
                )
                
                logger.info("Successfully uploaded %s to Cloudinary. Public ID: %s", file_path, result.get("public_id"))
                
                # Delete local file after successful upload
                try:
                    os.remove(file_path)
                    logger.info("Deleted local file: %s", file_path)
                except Exception as e:
                    logger.warning("Failed to delete local file %s: %s", file_path, e)
                
                return {
                    "secure_url": result.get("secure_url"),
                    "public_id": result.get("public_id")
                }
            except Exception as e:
                attempt += 1
                logger.error("Cloudinary upload failed for %s. Attempt %d of %d. Error: %s", file_path, attempt, max_retries + 1, e)
                if attempt > max_retries:
                    raise ServiceUnavailableException(f"Failed to upload image to Cloudinary: {e}")
                await asyncio.sleep(2)
        
        return {}

cloudinary_service = CloudinaryService()
