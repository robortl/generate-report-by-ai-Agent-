"""
报告生成模块 - 处理各种报告生成功能
"""

import logging
import traceback
from typing import Optional, List, Dict, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema.messages import HumanMessage
from app.config.model_config import get_model_config
from app.services.modules.vector_store import create_vector_store
from app.services.modules.model_handlers import get_model_for_generation

# 初始化日志
logger = logging.getLogger(__name__)

def generate_report_with_rag(
    service_instance,
    document: str, 
    prompt: Optional[str] = None, 
    model_id: Optional[str] = None
) -> str:
    """
    使用RAG生成报告
    
    Args:
        service_instance: LangChain服务实例
        document: 文档内容
        prompt: 可选的自定义提示词
        model_id: 可选的模型ID
        
    Returns:
        str: 生成的报告内容
    """
    try:
        # 如果使用假的嵌入，返回一个有意义的示例报告
        if service_instance.use_fake_embeddings:
            logger.warning("使用假的嵌入和LLM生成报告，这只是一个示例")
            return """
# 会议报告摘要

## 会议摘要
这次会议讨论了产品开发进度、市场营销策略和客户反馈。团队成员分享了各自负责领域的最新进展，并确定了下一步行动计划。

## 主要讨论点
1. 产品开发团队报告了新功能的实施进度
2. 市场营销团队提出了新的推广策略
3. 客户服务团队分享了最近收到的用户反馈
4. 讨论了项目时间线和资源分配

## 决策和行动项
1. 批准了新功能的开发计划
2. 同意增加市场营销预算
3. 决定优先解决用户报告的三个主要问题
4. 计划在下周举行用户测试会议

## 后续步骤
1. 产品团队将在周五前完成功能规格文档
2. 市场团队将在两周内提交详细的营销计划
3. 所有团队将在下次会议前更新各自的进度报告
4. 下次全体会议定于两周后举行

注意：这是一个示例报告，因为AWS Bedrock服务未正确配置。请确保AWS凭证已正确设置并有权限访问Bedrock服务。
            """
        
        # 默认提示词
        default_prompt = """
        你是一位专业的会议记录分析师。请根据以下会议记录生成一份结构化的会议报告。
        报告应包括以下部分：
        1. 会议摘要
        2. 主要讨论点
        3. 决策和行动项
        4. 后续步骤
        
        会议记录：
        {context}
        
        请生成一份专业、简洁且结构清晰的报告。
        """
        
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
        
        # 分割文档
        texts = service_instance.text_splitter.split_text(document)
        
        # 创建向量存储
        try:
            vectorstore = create_vector_store(texts, service_instance.embeddings)
        except Exception as e:
            # 如果创建向量存储失败，返回错误信息
            logger.error(f"创建向量存储失败: {str(e)}")
            return f"创建向量存储失败: {str(e)}"
        
        # 创建检索器
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # 使用传入的模型ID或默认模型ID
        used_model_id = model_id if model_id else service_instance.default_model_id
        logger.info(f"使用模型ID: {used_model_id} 生成报告")
        
        # 创建指定模型的LLM实例
        try:
            # 获取适合的模型
            llm = get_model_for_generation(service_instance, used_model_id)
            
            # 创建提示模板
            prompt_template = PromptTemplate(
                template=final_prompt,
                input_variables=["context"]
            )
            
            # 获取相关上下文
            docs = retriever.get_relevant_documents(document[:1000])  # 使用文档开头作为查询
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # 添加调试日志，显示文档内容的前200个字符
            if context:
                logger.info(f"成功检索到文档内容，长度: {len(context)} 字符，前200字符预览: {context[:200]}...")
            else:
                logger.warning("检索到的文档内容为空")
            
            # 格式化提示词以便于直接传递给模型
            formatted_prompt = prompt_template.format(context=context)
            
            # 如果是ChatModel类型模型
            if "claude-3" in used_model_id and hasattr(llm, "invoke"):
                messages = [HumanMessage(content=formatted_prompt)]
                response = llm.invoke(messages)
                report = response.content
                return report
            else:
                # 标准LLM链调用
                chain = LLMChain(llm=llm, prompt=prompt_template)
                report = chain.run(context=context)
                return report
                
        except Exception as e:
            logger.error(f"使用模型 {used_model_id} 时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 尝试使用另一个可能支持的模型作为备选
            if model_id and model_id != "amazon.titan-text-express-v1":
                logger.info("尝试使用备选模型 amazon.titan-text-express-v1")
                return generate_report_with_rag(service_instance, document, prompt, "amazon.titan-text-express-v1")
            else:
                raise e
                
    except Exception as e:
        logger.error(f"生成报告时出错: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 返回一个错误信息
        return f"""
# 报告生成失败

无法生成报告，可能是由于以下原因：
1. AWS凭证配置问题 - 请确保已正确配置AWS凭证
2. 网络连接问题 - 请检查与AWS服务的连接
3. 服务错误 - AWS Bedrock服务可能暂时不可用或指定的模型不可用

错误详情: {str(e)}

请检查系统日志获取更多信息，并确保AWS凭证已正确配置。
        """


def prepare_context(service_instance, document: str) -> tuple:
    """
    准备上下文内容
    
    Args:
        service_instance: LangChain服务实例
        document: 文档内容
        
    Returns:
        tuple: (检索器, 上下文文本, 向量存储)
    """
    # 分割文档
    texts = service_instance.text_splitter.split_text(document)
    
    # 创建向量存储
    vectorstore = create_vector_store(texts, service_instance.embeddings)
    
    # 创建检索器
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # 获取相关上下文
    docs = retriever.get_relevant_documents(document[:1000])  # 使用文档开头作为查询
    context = "\n\n".join([doc.page_content for doc in docs])
    
    return retriever, context, vectorstore
