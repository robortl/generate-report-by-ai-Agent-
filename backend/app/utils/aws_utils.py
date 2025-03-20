"""
AWS utility functions for the report generation system.
This module provides functions for interacting with AWS services like S3 and DynamoDB.
"""

import os
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, BinaryIO, Union

logger = logging.getLogger(__name__)

def get_s3_client():
    """
    Get an S3 client with the configured credentials.
    
    Returns:
        boto3.client: Configured S3 client
    """
    return boto3.client(
        's3',
        region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )

def get_dynamodb_resource():
    """
    Get a DynamoDB resource with the configured credentials.
    
    Returns:
        boto3.resource: Configured DynamoDB resource
    """
    return boto3.resource(
        'dynamodb',
        region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )

def upload_to_s3(
    file_obj: Union[BinaryIO, bytes, str],
    bucket_name: str,
    object_key: str,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload a file to S3.
    
    Args:
        file_obj: File object, bytes, or file path to upload
        bucket_name: Name of the S3 bucket
        object_key: S3 object key (path in the bucket)
        content_type: MIME type of the file
        metadata: Additional metadata to store with the file
        
    Returns:
        Dict containing the upload result with keys:
            - success: Boolean indicating if the upload was successful
            - url: URL of the uploaded file (if successful)
            - error: Error message (if unsuccessful)
    """
    s3_client = get_s3_client()
    extra_args = {}
    
    if content_type:
        extra_args['ContentType'] = content_type
    
    if metadata:
        extra_args['Metadata'] = metadata
    
    try:
        # Handle different input types
        if isinstance(file_obj, str):  # File path
            with open(file_obj, 'rb') as f:
                s3_client.upload_fileobj(f, bucket_name, object_key, ExtraArgs=extra_args)
        elif isinstance(file_obj, bytes):  # Bytes
            s3_client.put_object(Body=file_obj, Bucket=bucket_name, Key=object_key, **extra_args)
        else:  # File-like object
            s3_client.upload_fileobj(file_obj, bucket_name, object_key, ExtraArgs=extra_args)
        
        # Generate the URL
        url = f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'ap-northeast-1')}.amazonaws.com/{object_key}"
        
        return {
            "success": True,
            "url": url,
            "bucket": bucket_name,
            "key": object_key
        }
    
    except ClientError as e:
        logger.error(f"Error uploading file to S3: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def download_from_s3(
    bucket_name: str,
    object_key: str,
    destination: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download a file from S3.
    
    Args:
        bucket_name: Name of the S3 bucket
        object_key: S3 object key (path in the bucket)
        destination: Local file path to save the downloaded file
        
    Returns:
        Dict containing the download result with keys:
            - success: Boolean indicating if the download was successful
            - data: File data (if destination is None and successful)
            - path: Path where the file was saved (if destination is provided and successful)
            - error: Error message (if unsuccessful)
    """
    s3_client = get_s3_client()
    
    try:
        if destination:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            
            # Download to file
            s3_client.download_file(bucket_name, object_key, destination)
            
            return {
                "success": True,
                "path": destination
            }
        else:
            # Download to memory
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            data = response['Body'].read()
            
            return {
                "success": True,
                "data": data,
                "content_type": response.get('ContentType'),
                "metadata": response.get('Metadata', {})
            }
    
    except ClientError as e:
        logger.error(f"Error downloading file from S3: {e}")
        return {
            "success": False,
            "error": str(e)
        }