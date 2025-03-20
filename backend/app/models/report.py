"""
Report model for the report generation system.
This module defines the data structure for reports in the system.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List


class ReportModel:
    """
    Model representing a generated report in the system.
    """
    
    def __init__(
        self,
        file_id: str,
        content: str,
        report_id: Optional[str] = None,
        model_id: Optional[str] = None,
        prompt: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        status: str = "completed",
        sections: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize a new ReportModel instance.
        
        Args:
            file_id: ID of the file this report is generated from
            content: Content of the report
            report_id: Unique identifier for the report (generated if not provided)
            model_id: ID of the AI model used to generate the report
            prompt: Prompt used to generate the report
            created_at: Time when the report was created
            updated_at: Time when the report was last updated
            status: Status of the report (completed, error, etc.)
            sections: Different sections of the report (summary, key points, etc.)
            metadata: Additional metadata about the report
            version: Version number of the report
            tags: Tags associated with the report
        """
        self.report_id = report_id or str(uuid.uuid4())
        self.file_id = file_id
        self.content = content
        self.model_id = model_id
        self.prompt = prompt
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.status = status
        self.sections = sections or {}
        self.metadata = metadata or {}
        self.version = version
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary for storage or serialization.
        
        Returns:
            Dict containing the model attributes
        """
        return {
            "report_id": self.report_id,
            "file_id": self.file_id,
            "content": self.content,
            "model_id": self.model_id,
            "prompt": self.prompt,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "sections": self.sections,
            "metadata": self.metadata,
            "version": self.version,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportModel':
        """
        Create a ReportModel instance from a dictionary.
        
        Args:
            data: Dictionary containing report attributes
            
        Returns:
            ReportModel instance
        """
        # Convert ISO format strings back to datetime
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
            
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
            
        return cls(
            file_id=data['file_id'],
            content=data['content'],
            report_id=data.get('report_id'),
            model_id=data.get('model_id'),
            prompt=data.get('prompt'),
            created_at=created_at,
            updated_at=updated_at,
            status=data.get('status', 'completed'),
            sections=data.get('sections', {}),
            metadata=data.get('metadata', {}),
            version=data.get('version', 1),
            tags=data.get('tags', [])
        ) 