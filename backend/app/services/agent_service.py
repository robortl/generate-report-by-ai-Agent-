import os
import boto3
import json
import time
import logging
import uuid
from typing import Dict, Any, Optional

# 配置日志
def setup_logging():
    """设置日志配置"""
    # 创建logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # 确保没有重复的处理器
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        logger.addHandler(console_handler)
    
    return logger

# 获取logger实例
logger = setup_logging()

class BedrockAgentService:
    """Bedrock Agent服务，用于调用AWS Bedrock Agent生成报告"""
    
    def __init__(self):
        """初始化Bedrock Agent服务"""
        self.region_name = os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1')
        self.agent_id = os.environ.get('BEDROCK_AGENT_ID', 'LPJVAYJAK2')
        self.agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        # 更新模型ID为有效的Bedrock模型
        self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        # 创建Bedrock Runtime客户端（用于直接调用模型）
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region_name)
        
        # 创建Bedrock Agent Runtime客户端
        # 注意：如果此服务不可用，将会抛出异常，需要确保AWS环境正确配置
        try:
            # 使用正确的角色ARN配置会话
            session = boto3.Session(region_name=self.region_name)
            # 创建带有角色ARN的客户端
            self.bedrock_agent_runtime = session.client('bedrock-agent-runtime', region_name=self.region_name)
            logger.info("成功创建Bedrock Agent Runtime客户端")
            logger.info(f"使用Agent ID: {self.agent_id}")
        except Exception as e:
            logger.error(f"无法创建Bedrock Agent Runtime客户端: {e}")
            logger.error("请确保AWS环境正确配置，并且bedrock-agent-runtime服务在当前区域可用")
            logger.error("可能需要更新boto3库或检查AWS区域设置")
            # 重新抛出异常，确保错误被暴露
            raise
        
        logger.info(f"初始化Bedrock Agent服务，区域: {self.region_name}, 代理ID: {self.agent_id}, 别名ID: {self.agent_alias_id}, 模型ID: {self.model_id}")
    
    def generate_report(self, file_content: str, prompt: Optional[str] = None, model_id: Optional[str] = None) -> str:
        """调用Bedrock Agent生成报告"""
        try:
            # 尝试使用Agent生成报告
            return self._generate_report_with_agent(file_content, prompt, model_id)
        except Exception as e:
            logger.error(f"使用Agent生成报告失败: {str(e)}")
            # 不再静默降级到模型调用，而是重新抛出异常
            raise Exception(f"Bedrock Agent调用失败，请检查AWS配置和服务可用性: {str(e)}")
    
    def _generate_report_with_agent(self, file_content: str, prompt: Optional[str] = None, model_id: Optional[str] = None) -> str:
        """使用Bedrock Agent生成报告"""
        # 创建会话ID
        session_id = f"report-session-{uuid.uuid4()}"
        
        # 构建输入文本
        input_text = f"请根据以下内容生成一份报告:\n\n{file_content}"
        
        # 如果有自定义提示，添加到输入文本中
        if prompt:
            input_text = f"{prompt}\n\n{input_text}"
        
        # 记录调用信息
        logger.info(f"[AGENT_START] 调用Bedrock Agent生成报告 | 会话ID: {session_id}")
        logger.debug(f"[AGENT_INPUT] 输入文本长度: {len(input_text)} | 前200个字符: {input_text[:200]}...")
        
        try:
            # 调用Bedrock Agent
            logger.info("[AGENT_INVOKE] 开始调用Bedrock Agent")
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=True
            )
            logger.info("[AGENT_INVOKE] Bedrock Agent调用成功")
            
            # 处理响应
            completion = ""
            event_count = 0
            
            # 处理EventStream
            if 'completion' in response:
                logger.info("[AGENT_STREAM] 开始处理事件流")
                
                for event in response['completion']:
                    event_count += 1
                    logger.debug(f"[AGENT_EVENT_{event_count}] 处理事件")
                    
                    try:
                        # 如果事件是字典类型
                        if isinstance(event, dict):
                            if 'chunk' in event and 'bytes' in event['chunk']:
                                chunk_data = event['chunk']['bytes'].decode('utf-8')
                                logger.debug(f"[AGENT_CHUNK] 解码后的chunk数据: {chunk_data}")
                                
                                # 尝试解析JSON
                                try:
                                    chunk_json = json.loads(chunk_data)
                                    if 'content' in chunk_json:
                                        for content_item in chunk_json['content']:
                                            if content_item.get('type') == 'text':
                                                text_content = content_item.get('text', '')
                                                completion += text_content
                                                logger.debug(f"[AGENT_TEXT] 提取的文本: {text_content[:100]}...")
                                except json.JSONDecodeError as json_error:
                                    logger.warning(f"[AGENT_JSON_ERROR] JSON解码错误: {json_error}")
                                    logger.debug("[AGENT_FALLBACK] 作为原始文本添加: {chunk_data}")
                                    completion += chunk_data
                        
                        # 如果事件是字符串类型
                        elif isinstance(event, str):
                            try:
                                event_json = json.loads(event)
                                if 'content' in event_json:
                                    for content_item in event_json['content']:
                                        if content_item.get('type') == 'text':
                                            text_content = content_item.get('text', '')
                                            completion += text_content
                                            logger.debug(f"[AGENT_TEXT] 提取的文本: {text_content[:100]}...")
                            except json.JSONDecodeError as json_error:
                                logger.warning(f"[AGENT_JSON_ERROR] JSON解码错误: {json_error}")
                                logger.debug(f"[AGENT_FALLBACK] 作为原始文本添加: {event}")
                                completion += event
                    
                    except Exception as event_error:
                        logger.error(f"[AGENT_EVENT_ERROR] 处理事件时出错: {event_error}")
                        continue
                
                logger.info(f"[AGENT_STREAM] 事件流处理完成，共处理 {event_count} 个事件")
            
            # 显示最终的Agent响应
            if completion:
                final_report = completion.strip()
                logger.info(f"[AGENT_SUCCESS] 报告生成成功 | 长度: {len(final_report)} 字符")
                logger.debug(f"[AGENT_REPORT] 报告前500个字符: {final_report[:500]}...")
                return final_report
            else:
                error_msg = "未能从响应中提取有效的报告内容"
                logger.error(f"[AGENT_ERROR] {error_msg}")
                logger.debug(f"[AGENT_RESPONSE] 原始响应: {response}")
                raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"调用Bedrock Agent生成报告时出错: {str(e)}"
            logger.error(f"[AGENT_ERROR] {error_msg}", exc_info=True)
            raise Exception(error_msg)
    
    def _generate_report_with_model(self, file_content: str, prompt: Optional[str] = None, model_id: Optional[str] = None) -> str:
        """直接使用Bedrock模型生成报告"""
        # 使用指定的模型ID或默认模型ID
        model_to_use = model_id or self.model_id
        
        # 构建输入文本
        input_text = f"请根据以下内容生成一份报告:\n\n{file_content}"
        
        # 如果有自定义提示，添加到输入文本中
        if prompt:
            input_text = f"{prompt}\n\n{input_text}"
        
        # 记录调用信息
        logger.info(f"直接调用Bedrock模型生成报告，模型ID: {model_to_use}")
        logger.debug(f"输入文本: {input_text[:200]}...")
        
        try:
            # 根据模型ID选择不同的请求体格式
            if model_to_use.startswith('anthropic.claude-3'):
                # Claude 3模型的请求体
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": input_text
                        }
                    ]
                }
            elif model_to_use.startswith('anthropic.claude-'):
                # Claude模型的请求体
                request_body = {
                    "prompt": f"\n\nHuman: {input_text}\n\nAssistant:",
                    "max_tokens_to_sample": 4000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            elif model_to_use.startswith('amazon.titan'):
                # Titan模型的请求体
                request_body = {
                    "inputText": input_text,
                    "textGenerationConfig": {
                        "maxTokenCount": 4000,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
            else:
                # 默认请求体格式
                request_body = {
                    "prompt": input_text,
                    "max_tokens_to_sample": 4000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            
            # 调用Bedrock模型
            response = self.bedrock_runtime.invoke_model(
                modelId=model_to_use,
                body=json.dumps(request_body)
            )
            
            # 解析响应
            response_body = json.loads(response['body'].read().decode('utf-8'))
            
            # 根据模型ID解析不同的响应格式
            if model_to_use.startswith('anthropic.claude-3'):
                # Claude 3模型的响应格式
                full_response = response_body.get('content', [{}])[0].get('text', '')
            elif model_to_use.startswith('anthropic.claude-'):
                # Claude模型的响应格式
                full_response = response_body.get('completion', '')
            elif model_to_use.startswith('amazon.titan'):
                # Titan模型的响应格式
                full_response = response_body.get('results', [{}])[0].get('outputText', '')
            else:
                # 默认响应格式
                full_response = response_body.get('completion', '')
            
            logger.info(f"Bedrock模型报告生成成功，长度: {len(full_response)}")
            return full_response
            
        except Exception as e:
            logger.error(f"直接调用Bedrock模型生成报告时出错: {str(e)}")
            raise Exception(f"Failed to generate report using Bedrock model: {str(e)}")

# 创建Bedrock Agent服务实例
bedrock_agent_service = BedrockAgentService()

# 导出函数
def generate_report(file_content: str, prompt: Optional[str] = None, model_id: Optional[str] = None) -> str:
    """调用Bedrock Agent生成报告"""
    return bedrock_agent_service.generate_report(file_content, prompt, model_id) 