import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def get_s3_client():
    """Create and return a boto3 S3 client using environment variables."""
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    region_name = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")

    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=region_name,
    )
    return session.client("s3")


def ensure_bucket_exists(bucket: str, region: Optional[str] = None) -> None:
    """Ensure the S3 bucket exists; create it if not present."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except ClientError as e:
        error_code = int(e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0))
        if error_code not in (404, 301):
            # 301 might be wrong region; fall through to create with region
            raise

    # Create the bucket
    create_params = {"Bucket": bucket}
    # us-east-1 must not set LocationConstraint
    if region and region != "us-east-1":
        create_params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    try:
        s3.create_bucket(**create_params)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed to create bucket {bucket}: {e}")


def upload_file_to_s3(
    local_path: str,
    bucket: str,
    key_prefix: str = "",
    content_type: Optional[str] = None,
) -> str:
    """
    Upload a file to S3 and return the public S3 URL.

    The bucket must allow read access for the object or you should
    serve via CloudFront. This returns the object URL form.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    s3 = get_s3_client()
    file_name = os.path.basename(local_path)
    key = f"{key_prefix.rstrip('/')}/{file_name}" if key_prefix else file_name

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    # Optionally auto-create bucket if missing
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    auto_create = (os.getenv("S3_AUTO_CREATE_BUCKET", "false").lower() in ("1", "true", "yes"))
    if auto_create:
        ensure_bucket_exists(bucket=bucket, region=region)

    try:
        s3.upload_file(local_path, bucket, key, ExtraArgs=extra_args)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed to upload {local_path} to s3://{bucket}/{key}: {e}")

    # Construct URL (path-style for us-east-1 is fine; for other regions virtual-hosted style is common)
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    return url


class S3Manager:
    """
    Utility class for common S3 operations, backed by get_s3_client().
    Designed to be test-friendly by relying on the module-level factory.
    """

    def __init__(self, bucket_name: str, region: Optional[str] = None):
        self.bucket_name = bucket_name
        self.region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
        self.s3 = get_s3_client()

    def create_bucket(self) -> None:
        """Create the bucket if it doesn't already exist."""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            return
        except ClientError:
            pass

        params = {"Bucket": self.bucket_name}
        if self.region and self.region != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
        try:
            self.s3.create_bucket(**params)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Error creating bucket '{self.bucket_name}': {e}")

    def upload_file(self, file_path: str, s3_folder: str = "") -> str:
        """Upload a local file to the bucket under the optional folder."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at local path: {file_path}")
        file_name = os.path.basename(file_path)
        key = f"{s3_folder.rstrip('/')}/{file_name}" if s3_folder else file_name
        try:
            self.s3.upload_file(file_path, self.bucket_name, key)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Error uploading file {file_path} to s3://{self.bucket_name}/{key}: {e}")
        return key

    def download_file(self, s3_key: str, local_path: str) -> None:
        """Download an S3 object to a local path."""
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        try:
            self.s3.download_file(self.bucket_name, s3_key, local_path)
        except (BotoCoreError, ClientError) as e:
            # Let callers decide whether to treat as fatal
            raise e

    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a pre-signed URL for an object, or None if generation fails."""
        try:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expires_in,
            )
        except Exception:
            return None


