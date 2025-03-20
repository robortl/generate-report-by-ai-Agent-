"""
File model for the report generation system.
This module defines the data structure for files in the system.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any


class FileModel:
    """
    Model representing a file in the system.
    """
    
    def __init__(
        self,
        original_filename: str,
        category: str = "general",
        file_id: Optional[str] = None,
        s3_key: Optional[str] = None,
        s3_url: Optional[str] = None,
        status: str = "pending",
        upload_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_type: Optional[str] = None,
        file_size: Optional[int] = None
    ):
        """
        Initialize a new FileModel instance.
        
        Args:
            original_filename: Original name of the uploaded file
            category: Category of the file (e.g., meeting, report, etc.)
            file_id: Unique identifier for the file (generated if not provided)
            s3_key: S3 object key where the file is stored
            s3_url: URL to access the file in S3
            status: Processing status of the file (pending, processing, completed, error)
            upload_time: Time when the file was uploaded
            metadata: Additional metadata about the file
            content_type: MIME type of the file
            file_size: Size of the file in bytes
        """
        self.file_id = file_id or str(uuid.uuid4())
        self.original_filename = original_filename
        self.category = category
        self.s3_key = s3_key
        self.s3_url = s3_url
        self.status = status
        self.upload_time = upload_time or datetime.utcnow()
        self.metadata = metadata or {}
        self.content_type = content_type
        self.file_size = file_size
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary for storage or serialization.
        
        Returns:
            Dict containing the model attributes
        """
        return {
            "file_id": self.file_id,
            "original_filename": self.original_filename,
            "category": self.category,
            "s3_key": self.s3_key,
            "s3_url": self.s3_url,
            "status": self.status,
            "upload_time": self.upload_time.isoformat(),
            "metadata": self.metadata,
            "content_type": self.content_type,
            "file_size": self.file_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileModel':
        """
        Create a FileModel instance from a dictionary.
        
        Args:
            data: Dictionary containing file attributes
            
        Returns:
            FileModel instance
        """
        # Convert ISO format string back to datetime
        if isinstance(data.get('upload_time'), str):
            data['upload_time'] = datetime.fromisoformat(data['upload_time'])
            
        return cls(
            original_filename=data['original_filename'],
            category=data.get('category', 'general'),
            file_id=data.get('file_id'),
            s3_key=data.get('s3_key'),
            s3_url=data.get('s3_url'),
            status=data.get('status', 'pending'),
            upload_time=data.get('upload_time'),
            metadata=data.get('metadata', {}),
            content_type=data.get('content_type'),
            file_size=data.get('file_size')
        )