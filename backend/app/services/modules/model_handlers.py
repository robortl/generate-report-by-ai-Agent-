"""
模型处理模块 - 处理不同模型的初始化和使用
"""

import logging
import os
import boto3
from typing import Optional, Dict, Any, Union
from langchain_community.llms import Bedrock as CommunityBedrock
from langchain_community.chat_models import BedrockChat
from langchain_community.llms.fake import FakeListLLM
from langchain_community.embeddings import BedrockEmbeddings, FakeEmbeddings
from app.config.model_config import get_model_config, DEFAULT_MODEL_ID

# 初始化日志
logger = logging.getLogger(__name__)

def initialize_bedrock_client():
    """
    初始化Bedrock客户端
    
    Returns:
        tuple: (client, model_id, success_flag)
    """
    try:
        # 获取AWS会话，使用本地凭证
        session = boto3.Session()
        region_name = session.region_name or "ap-northeast-1"
        
        # 尝试初始化Bedrock LLM
        logger.info(f"尝试初始化Bedrock LLM，使用区域: {region_name}...")
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name,
            endpoint_url=os.environ.get("BEDROCK_ENDPOINT", f"bedrock-runtime.{region_name}.amazonaws.com")
        )
        
        # 默认使用Amazon Titan模型，而不是Claude
        model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
        
        return client, model_id, True
    except Exception as e:
        logger.error(f"初始化Bedrock服务失败: {str(e)}")
        return None, "fake.model", False


def create_model(client, model_id: str, use_fake: bool = False) -> tuple:
    """
    创建适合的模型实例
    
    Args:
        client: Bedrock客户端
        model_id: 模型ID
        use_fake: 是否使用假模型
        
    Returns:
        tuple: (llm, chat_model, embeddings, use_fake_embeddings)
    """
    if use_fake:
        # 如果请求使用假模型
        embeddings = FakeEmbeddings(size=1536)
        llm = FakeListLLM(
            responses=["这是一个测试响应，实际AWS Bedrock服务初始化失败。"]
        )
        return llm, None, embeddings, True
    
    # 获取模型配置
    model_config = get_model_config(model_id)
    
    try:
        if "claude-3" in model_id:
            # 使用BedrockChat用于Claude 3模型
            llm = BedrockChat(
                model_id=model_id,
                client=client,
                model_kwargs={
                    "anthropic_version": model_config.get("anthropic_version", "bedrock-2023-05-31"),
                    "max_tokens": model_config.get("max_tokens", 4096),
                    "temperature": model_config.get("temperature", 0.7)
                }
            )
            
            # 初始化chat_model作为同样的实例
            chat_model = llm
        else:
            # 对于其他模型（如Titan），使用CommunityBedrock
            llm = CommunityBedrock(
                model_id=model_id,
                client=client
            )
            
            # 尝试作为BedrockChat初始化chat_model
            chat_model = BedrockChat(
                model_id=model_id,
                client=client,
                model_kwargs={
                    "temperature": model_config.get("temperature", 0.7),
                    "max_tokens": model_config.get("max_tokens", 4096)
                }
            )
        
        # 初始化 Bedrock 嵌入模型
        embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v1",
            client=client
        )
        logger.info("成功初始化 Bedrock 嵌入模型")
        
        logger.info(f"成功初始化Bedrock LLM和嵌入模型，模型: {model_id}")
        return llm, chat_model, embeddings, False
        
    except Exception as e:
        # 如果初始化失败，使用假的嵌入和LLM
        logger.error(f"初始化模型失败: {str(e)}，将使用假的嵌入和LLM")
        embeddings = FakeEmbeddings(size=1536)
        llm = FakeListLLM(
            responses=["这是一个测试响应，实际AWS Bedrock服务初始化失败。"]
        )
        return llm, None, embeddings, True


def get_model_for_generation(
    service_instance, 
    model_id: Optional[str] = None
) -> Union[BedrockChat, CommunityBedrock]:
    """
    获取用于生成文本的模型实例
    
    Args:
        service_instance: LangChain服务实例
        model_id: 可选的模型ID
        
    Returns:
        Union[BedrockChat, CommunityBedrock]: 适合的模型实例
    """
    # 使用传入的模型ID或默认模型ID
    used_model_id = model_id if model_id else service_instance.default_model_id
    
    # 如果是默认模型或者请求使用假的嵌入
    if used_model_id == service_instance.default_model_id or service_instance.use_fake_embeddings:
        return service_instance.llm
    
    # 根据模型类型使用不同的实例化方式
    model_config = get_model_config(used_model_id)
    
    if "claude-3" in used_model_id:
        logger.info(f"使用Claude 3模型: {used_model_id}")
        return BedrockChat(
            model_id=used_model_id,
            client=service_instance.bedrock_client,
            model_kwargs={
                "anthropic_version": model_config.get("anthropic_version", "bedrock-2023-05-31"),
                "max_tokens": model_config.get("max_tokens", 4096),
                "temperature": model_config.get("temperature", 0.7)
            }
        )
    else:
        logger.info(f"使用标准Bedrock模型: {used_model_id}")
        return CommunityBedrock(
            model_id=used_model_id,
            client=service_instance.bedrock_client,
            model_kwargs={
                "temperature": model_config.get("temperature", 0.7),
                "maxTokens": model_config.get("max_tokens", 4096)
            }
        )
