"""
Model definitions for AI models in the report generation system.
This module defines the data structure for AI models available in the system.
"""

from typing import Dict, Any, Optional, List


class ModelInfo:
    """
    Model representing an AI model available in the system.
    """
    
    def __init__(
        self,
        model_id: str,
        provider: str,
        name: str,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        default_parameters: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        is_active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ModelInfo instance.
        
        Args:
            model_id: Unique identifier for the model
            provider: Provider of the model (e.g., "anthropic", "amazon", etc.)
            name: Display name of the model
            description: Description of the model
            capabilities: List of capabilities the model has
            parameters: Parameters that can be configured for the model
            default_parameters: Default parameter values for the model
            max_tokens: Maximum number of tokens the model can process
            is_active: Whether the model is currently active
            metadata: Additional metadata about the model
        """
        self.model_id = model_id
        self.provider = provider
        self.name = name
        self.description = description or ""
        self.capabilities = capabilities or []
        self.parameters = parameters or {}
        self.default_parameters = default_parameters or {}
        self.max_tokens = max_tokens
        self.is_active = is_active
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary for storage or serialization.
        
        Returns:
            Dict containing the model attributes
        """
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "parameters": self.parameters,
            "default_parameters": self.default_parameters,
            "max_tokens": self.max_tokens,
            "is_active": self.is_active,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """
        Create a ModelInfo instance from a dictionary.
        
        Args:
            data: Dictionary containing model attributes
            
        Returns:
            ModelInfo instance
        """
        return cls(
            model_id=data['model_id'],
            provider=data['provider'],
            name=data['name'],
            description=data.get('description'),
            capabilities=data.get('capabilities'),
            parameters=data.get('parameters'),
            default_parameters=data.get('default_parameters'),
            max_tokens=data.get('max_tokens'),
            is_active=data.get('is_active', True),
            metadata=data.get('metadata')
        )


# Predefined models available in the system
AVAILABLE_MODELS = [
    ModelInfo(
        model_id="anthropic.claude-v2",
        provider="anthropic",
        name="Claude 2",
        description="Anthropic's Claude 2 model for text generation and summarization",
        capabilities=["text_generation", "summarization", "question_answering"],
        default_parameters={"temperature": 0.7, "max_tokens_to_sample": 4000}
    ),
    ModelInfo(
        model_id="anthropic.claude-instant-v1",
        provider="anthropic",
        name="Claude Instant",
        description="Faster and more cost-effective version of Claude",
        capabilities=["text_generation", "summarization", "question_answering"],
        default_parameters={"temperature": 0.7, "max_tokens_to_sample": 2000}
    ),
    ModelInfo(
        model_id="amazon.titan-text-express-v1",
        provider="amazon",
        name="Titan Text Express",
        description="Amazon's Titan Text Express model for text generation",
        capabilities=["text_generation", "summarization"],
        default_parameters={"temperature": 0.7, "maxTokenCount": 4000}
    )
] 