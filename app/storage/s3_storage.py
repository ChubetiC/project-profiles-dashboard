from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from app.core.config import Settings


class DocumentStorage(Protocol):
    def upload_file(self, storage_key: str, content: bytes, content_type: str) -> None: ...

    def download_file(self, storage_key: str) -> bytes: ...

    def delete_file(self, storage_key: str) -> None: ...


class S3DocumentStorage:
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    def upload_file(self, storage_key: str, content: bytes, content_type: str) -> None:
        self._ensure_bucket_exists()
        self.client.put_object(
            Bucket=self.bucket,
            Key=storage_key,
            Body=content,
            ContentType=content_type,
        )

    def download_file(self, storage_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        body = response["Body"]
        return bytes(body.read())

    def delete_file(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    def _ensure_bucket_exists(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)
