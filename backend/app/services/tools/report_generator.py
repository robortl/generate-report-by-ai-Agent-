"""
使用工具生成增强报告的功能实现
"""

import logging
import traceback
from typing import Optional, List, Dict, Any

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema.messages import HumanMessage
from langchain_community.chat_models import BedrockChat
from langchain_community.llms import Bedrock as CommunityBedrock

from app.config.model_config import get_model_config
from app.services.modules.report_generators import prepare_context
from app.services.modules.model_handlers import get_model_for_generation
from .tool_definitions import get_tool_definitions

# 配置日志
logger = logging.getLogger(__name__)

def generate_report_with_tools(
    service, 
    document: str, 
    prompt: Optional[str] = None, 
    model_id: Optional[str] = None
) -> str:
    """
    使用工具生成报告
    
    Args:
        service: LangChain 服务实例
        document: 文档内容
        prompt: 可选的自定义提示词
        model_id: 可选的模型 ID
        
    Returns:
        str: 生成的报告内容
    """
    try:
        # 如果使用假的嵌入，返回简单的示例报告
        if service.use_fake_embeddings:
            logger.warning("使用假的嵌入和LLM生成报告，这只是一个示例")
            return "示例报告 - AWS Bedrock服务未正确配置"
        
        # 简化的默认提示词
        default_prompt = "请根据文本内容生成结构化报告: {context}"
        
        # 使用自定义提示词或默认提示词
        if prompt:
            # 检查自定义提示词是否包含{context}占位符
            if "{context}" not in prompt:
                # 如果没有占位符，将文件内容追加到提示词后
                final_prompt = f"""{prompt}

以下是文件内容，请基于这些内容生成报告：

{{context}}
"""
                logger.info("自定义提示词中没有{context}占位符，已自动添加文件内容占位符")
            else:
                final_prompt = prompt
                logger.info("使用包含{context}占位符的自定义提示词")
        else:
            final_prompt = default_prompt
            logger.info("使用默认提示词")
        
        # 向量化和检索
        retriever, context, vectorstore = prepare_context(service, document)
        
        # 添加调试日志，显示文档内容的前200个字符
        if context:
            logger.info(f"成功检索到文档内容，长度: {len(context)} 字符，前200字符预览: {context[:200]}...")
        else:
            logger.warning("检索到的文档内容为空")
        
        # 设置模型和配置
        used_model_id = model_id if model_id else service.default_model_id
        logger.info(f"使用模型ID: {used_model_id} 生成报告")
        
        # 准备工具和提示
        tools = get_tool_definitions()
        
        # 创建提示模板
        prompt_template = PromptTemplate(
            template=final_prompt,
            input_variables=["context"]
        )
        
        # 格式化提示词
        formatted_prompt = prompt_template.format(context=context)
        
        # 根据模型类型选择合适的方法生成报告
        if "claude-3" in used_model_id and service.chat_model:
            return _generate_with_claude(
                service, used_model_id, formatted_prompt, tools
            )
        else:
            return _generate_with_standard_model(
                service, used_model_id, prompt_template, context
            )
                
    except Exception as e:
        logger.error(f"生成报告时出错: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 返回一个错误信息
        return f"""
# 使用工具生成报告失败

无法生成报告，可能是由于以下原因：
1. AWS凭证配置问题 - 请确保已正确配置AWS凭证
2. 网络连接问题 - 请检查与AWS服务的连接
3. 模型不支持工具功能 - 所选模型可能不支持工具调用

错误详情: {str(e)}

请检查系统日志获取更多信息，并确保AWS凭证已正确配置。
        """


def _generate_with_claude(service, model_id: str, formatted_prompt: str, tools: List[dict]) -> str:
    """
    使用 Claude 模型生成报告
    
    Args:
        service: LangChain 服务实例
        model_id: 模型 ID
        formatted_prompt: 格式化后的提示词
        tools: 工具定义列表
        
    Returns:
        str: 生成的报告
    """
    try:
        # 使用BedrockChat调用工具
        bedrock_chat = BedrockChat(
            model_id=model_id,
            client=service.bedrock_client,
            model_kwargs={
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.7,
                "tools": tools
            }
        )
        
        # 发送消息
        messages = [HumanMessage(content=formatted_prompt)]
        response = bedrock_chat.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"使用Claude模型生成报告失败: {str(e)}")
        logger.warning("回退到标准方法生成报告")
        raise e


def _generate_with_standard_model(service, model_id: str, prompt_template: PromptTemplate, context: str) -> str:
    """
    使用标准模型生成报告
    
    Args:
        service: LangChain 服务实例
        model_id: 模型 ID
        prompt_template: 提示模板
        context: 上下文内容
        
    Returns:
        str: 生成的报告
    """
    try:
        # 获取模型配置
        model_config = get_model_config(model_id)
        
        # 创建LLM实例
        llm = CommunityBedrock(
            model_id=model_id,
            client=service.bedrock_client,
            model_kwargs={
                "temperature": model_config.get("temperature", 0.7),
                "maxTokens": model_config.get("max_tokens", 4096)
            }
        )
        
        # 创建LLM链
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        # 生成报告
        return chain.run(context=context)
    except Exception as e:
        logger.error(f"使用标准模型生成报告失败: {str(e)}")
        raise e
