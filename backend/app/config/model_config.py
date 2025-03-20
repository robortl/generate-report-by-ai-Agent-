"""
模型配置文件，用于管理各种模型的参数和默认设置
"""

# 默认模型参数
DEFAULT_TEMPERATURE = 0.2  # 更低的温度使输出更确定性、更少创意性
DEFAULT_MAX_TOKENS = 2000  # 控制生成文本的最大长度

# 默认使用的模型ID（优先使用Titan模型，因为它不需要特殊的推理配置）
DEFAULT_MODEL_ID = "amazon.titan-text-express-v1"

# 模型特定参数配置
MODEL_CONFIGS = {
    # Amazon Titan模型配置
    "amazon.titan-text-express-v1": {
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "provider": "amazon",
        "description": "Amazon的Titan Text Express模型，适合一般文本生成任务",
        "supports_tools": False
    },
    "amazon.titan-text-express-v1:0:8k": {
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "provider": "amazon",
        "description": "Amazon的Titan Text Express 8K上下文模型",
        "supports_tools": False
    },
    "amazon.titan-embed-text-v1": {
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "provider": "amazon",
        "description": "Amazon的Titan嵌入模型，适合向量化文本",
        "supports_tools": False
    },
    "amazon.titan-embed-text-v2:0": {
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "provider": "amazon",
        "description": "Amazon的Titan嵌入模型v2版本",
        "supports_tools": False
    },
    
    # Anthropic模型配置
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "temperature": 0.3,  # Claude模型可以使用略高的温度
        "max_tokens": 4096,  # Claude支持较长的输出
        "anthropic_version": "bedrock-2023-05-31",  # Claude特有参数
        "provider": "anthropic",
        "description": "Anthropic的Claude 3 Sonnet模型，平衡了性能和速度",
        "supports_tools": True
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "temperature": 0.3,
        "max_tokens": 4096,
        "anthropic_version": "bedrock-2023-05-31",
        "provider": "anthropic",
        "description": "Anthropic的Claude 3 Haiku模型，速度快、成本低",
        "supports_tools": True
    },
    
    # Meta模型配置
    "meta.llama3-70b-instruct-v1:0": {
        "temperature": 0.2,
        "max_tokens": 2048,
        "provider": "meta",
        "description": "Meta的Llama 3 70B大型语言模型",
        "supports_tools": False
    }
}

def get_model_config(model_id: str = None) -> dict:
    """
    获取指定模型的配置，如果没有找到则返回默认配置
    
    Args:
        model_id: 模型ID
        
    Returns:
        模型配置字典
    """
    if not model_id:
        model_id = DEFAULT_MODEL_ID
    
    # 返回指定模型的配置，如果没有则返回默认值
    return MODEL_CONFIGS.get(model_id, {
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "provider": "unknown",
        "description": "未知模型",
        "supports_tools": False
    })
