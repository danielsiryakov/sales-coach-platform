import os
import aiofiles
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from datetime import datetime
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.use_s3 = bool(settings.aws_access_key_id and settings.aws_secret_access_key)

        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        else:
            os.makedirs(settings.local_recordings_path, exist_ok=True)

    async def save_audio(self, session_id: str, audio_data: bytes, audio_type: str = "combined") -> str:
        """Save audio recording and return the storage path/URL."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}/{audio_type}_{timestamp}.pcm"

        if self.use_s3:
            return await self._save_to_s3(filename, audio_data)
        else:
            return await self._save_to_local(filename, audio_data)

    async def _save_to_s3(self, filename: str, audio_data: bytes) -> str:
        try:
            self.s3_client.put_object(
                Bucket=settings.s3_recordings_bucket,
                Key=filename,
                Body=audio_data,
                ContentType='audio/pcm'
            )
            return f"s3://{settings.s3_recordings_bucket}/{filename}"
        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {e}")

    async def _save_to_local(self, filename: str, audio_data: bytes) -> str:
        filepath = os.path.join(settings.local_recordings_path, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(audio_data)

        return filepath

    async def get_audio(self, path: str) -> Optional[bytes]:
        """Retrieve audio from storage."""
        if path.startswith("s3://"):
            return await self._get_from_s3(path)
        else:
            return await self._get_from_local(path)

    async def _get_from_s3(self, s3_path: str) -> Optional[bytes]:
        try:
            bucket, key = s3_path.replace("s3://", "").split("/", 1)
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError:
            return None

    async def _get_from_local(self, filepath: str) -> Optional[bytes]:
        try:
            async with aiofiles.open(filepath, 'rb') as f:
                return await f.read()
        except FileNotFoundError:
            return None


storage_service = StorageService()
