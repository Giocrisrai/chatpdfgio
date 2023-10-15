import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import logging
import os
from typing import Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from the .env file
load_dotenv()


def initialize_s3_client() -> boto3.client:
    """
    Initialize and return an Amazon S3 client using credentials from environment variables.

    **Returns**:
    - An instance of boto3's S3 client.
    """
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )


s3_client = initialize_s3_client()


def upload_pdf(file_bytes: bytes, unique_filename: str) -> Dict[str, Union[str, bool]]:
    """
    Upload a PDF file to Amazon S3.

    **Arguments**:
    - `file_bytes` (bytes): The bytes of the file to be uploaded.
    - `unique_filename` (str): The unique filename to use for the uploaded file.

    **Returns**:
    - A dictionary containing the status, message, and filename of the uploaded file.
    """
    try:
        s3_client.put_object(Body=file_bytes, Bucket=os.environ.get(
            'YOUR_BUCKET_NAME'), Key=unique_filename)
        return {"status": "Success", "message": "File uploaded successfully to S3", "filename": unique_filename}
    except FileNotFoundError:
        return {"status": "Failed", "message": "File not found"}
    except NoCredentialsError:
        return {"status": "Failed", "message": "Credentials not available"}
    except ClientError as e:
        return {"status": "Failed", "message": str(e)}


def s3_object_exists(bucket_name: str, key: str) -> bool:
    """
    Check if an object exists in an Amazon S3 bucket.

    **Arguments**:
    - `bucket_name` (str): The name of the bucket.
    - `key` (str): The key of the object to check.

    **Returns**:
    - A boolean indicating whether the object exists in the bucket.
    """
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise


def check_documents(bucket_name: str) -> bool:
    """
    Check if there are any documents in an Amazon S3 bucket.

    **Arguments**:
    - `bucket_name` (str): The name of the bucket.

    **Returns**:
    - A boolean indicating whether there are any documents in the bucket.
    """
    response = s3_client.list_objects(Bucket=bucket_name)
    return 'Contents' in response
