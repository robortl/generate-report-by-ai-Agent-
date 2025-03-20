#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
报告生成Lambda函数
Report Generation Lambda Function
レポート生成Lambda関数
"""

import os
import json
import logging
import uuid
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# 配置日志
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')  # 默认使用DEBUG级别以显示更多信息

# 创建logger
logger = logging.getLogger('ReportGenerator')
logger.setLevel(getattr(logging, log_level))

# 清除所有已存在的处理器
if logger.handlers:
    logger.handlers.clear()

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, log_level))

# 设置日志格式
formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] [%(funcName)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

# 添加处理器到logger
logger.addHandler(console_handler)

# 禁用其他模块的DEBUG日志
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# 环境变量
AWS_REGION = os.environ.get('APP_AWS_REGION', 'ap-northeast-1')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
DYNAMODB_FILES_TABLE = os.environ.get('DYNAMODB_FILES_TABLE', 'report_files')
DYNAMODB_REPORTS_TABLE = os.environ.get('DYNAMODB_REPORTS_TABLE', 'report_reports')

# 验证环境变量
if not S3_BUCKET_NAME:
    logger.error("环境变量S3_BUCKET_NAME未设置")
    raise ValueError("S3_BUCKET_NAME is required")

logger.info("=== Lambda函数初始化开始 ===")
logger.info(f"Region: {AWS_REGION}")
logger.info(f"S3 Bucket: {S3_BUCKET_NAME}")
logger.info(f"DynamoDB Files Table: {DYNAMODB_FILES_TABLE}")
logger.info(f"DynamoDB Reports Table: {DYNAMODB_REPORTS_TABLE}")
logger.info("=== Lambda函数初始化完成 ===")

# 创建AWS客户端
def create_aws_client(service_name):
    """创建AWS客户端"""
    return boto3.client(
        service_name,
        region_name=AWS_REGION
    )

# 初始化AWS客户端
s3_client = create_aws_client('s3')
dynamodb_client = create_aws_client('dynamodb')
bedrock_client = create_aws_client('bedrock-runtime')

def get_file_content(file_id):
    """从S3获取文件内容"""
    try:
        # 首先从DynamoDB获取文件信息
        response = dynamodb_client.get_item(
            TableName=DYNAMODB_FILES_TABLE,
            Key={'file_id': {'S': file_id}}
        )
        
        if 'Item' not in response:
            logger.error(f"文件不存在: {file_id}")
            return None
        
        file_info = response['Item']
        s3_key = file_info['s3_key']['S']
        
        # 从S3获取文件内容
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        file_content = response['Body'].read().decode('utf-8')
        
        return file_content
    except Exception as e:
        logger.error(f"获取文件内容时出错: {e}")
        return None

def generate_report_with_langchain(file_content, model_id, prompt_template):
    """使用LangChain生成报告"""
    try:
        from langchain.llms import Bedrock
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        
        # 创建Bedrock LLM
        llm = Bedrock(
            model_id=model_id,
            client=bedrock_client,
            model_kwargs={"temperature": 0.7, "max_tokens_to_sample": 4096}
        )
        
        # 创建提示模板
        prompt = PromptTemplate(
            input_variables=["content"],
            template=prompt_template
        )
        
        # 创建链
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # 生成报告
        report = chain.run(content=file_content)
        
        return report
    except Exception as e:
        logger.error(f"使用LangChain生成报告时出错: {e}")
        return None

def generate_report_with_haystack(file_content, model_id, prompt_template):
    """使用Haystack生成报告"""
    try:
        from haystack.nodes import PromptNode
        
        # 创建PromptNode
        prompt_node = PromptNode(
            model_name_or_path=model_id,
            api_key="dummy",  # 使用AWS凭证，不需要实际的API密钥
            aws_region=AWS_REGION,
            aws_bedrock_client=bedrock_client,
            max_length=4096,
            temperature=0.7
        )
        
        # 准备提示
        prompt = prompt_template.replace("{content}", file_content)
        
        # 生成报告
        result = prompt_node(prompt)
        report = result[0]
        
        return report
    except Exception as e:
        logger.error(f"使用Haystack生成报告时出错: {e}")
        return None

def generate_report_from_text(text_content, model_id="anthropic.claude-v2", framework="langchain"):
    """直接从文本内容生成报告"""
    try:
        # 根据内容类型选择合适的提示模板
        if "会议" in text_content or "记录" in text_content:
            prompt_template = "请根据以下会议记录生成一份详细的会议报告，包括主要讨论内容、决定事项和后续行动:\n\n{content}\n\n报告:"
        elif "患者" in text_content or "护理" in text_content or "医疗" in text_content:
            prompt_template = "请根据以下患者信息生成一份详细的看护报告，包括患者状况、治疗计划和护理建议:\n\n{content}\n\n看护报告:"
        else:
            prompt_template = "请根据以下内容生成一份详细的报告:\n\n{content}\n\n报告:"
        
        # 根据框架选择生成方法
        if framework.lower() == 'langchain':
            report_content = generate_report_with_langchain(text_content, model_id, prompt_template)
        elif framework.lower() == 'haystack':
            report_content = generate_report_with_haystack(text_content, model_id, prompt_template)
        else:
            logger.error(f"不支持的框架: {framework}")
            return None
        
        return report_content
    except Exception as e:
        logger.error(f"从文本生成报告时出错: {e}")
        return None

def save_report(file_id, report_content, model_id, framework):
    """保存报告到S3和DynamoDB"""
    try:
        # 生成唯一ID
        report_id = str(uuid.uuid4())
        creation_date = datetime.now().isoformat()
        
        logger.info(f"[REPORT_START] 开始保存报告 | Report ID: {report_id} | File ID: {file_id}")
        logger.debug(f"[REPORT_CONTENT] 报告内容长度: {len(report_content)} 字符 | 前100个字符: {report_content[:100]}")
        
        # 保存到S3
        s3_key = f"reports/{report_id}.txt"
        logger.info(f"[S3_UPLOAD_START] Bucket: {S3_BUCKET_NAME} | Key: {s3_key}")
        
        try:
            start_time = datetime.now()
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=report_content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'file_id': file_id,
                    'model_id': model_id,
                    'framework': framework,
                    'creation_date': creation_date
                }
            )
            upload_duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[S3_UPLOAD_SUCCESS] 上传耗时: {upload_duration}秒")
            
            # 验证文件是否成功上传
            try:
                s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                logger.info("[S3_VERIFY_SUCCESS] 文件验证成功")
            except Exception as verify_error:
                logger.error(f"[S3_VERIFY_ERROR] 文件验证失败: {verify_error}")
                raise
                
        except Exception as s3_error:
            logger.error(f"[S3_UPLOAD_ERROR] 上传失败: {str(s3_error)}")
            raise
        
        # 保存到DynamoDB
        logger.info(f"[DYNAMODB_SAVE_START] Table: {DYNAMODB_REPORTS_TABLE}")
        dynamodb_item = {
            'report_id': {'S': report_id},
            'file_id': {'S': file_id},
            'creation_date': {'S': creation_date},
            's3_key': {'S': s3_key},
            'model_id': {'S': model_id},
            'framework': {'S': framework},
            'status': {'S': 'completed'},
            'content_length': {'N': str(len(report_content))}
        }
        logger.debug(f"[DYNAMODB_ITEM] {json.dumps(dynamodb_item, indent=2)}")
        
        try:
            start_time = datetime.now()
            dynamodb_client.put_item(
                TableName=DYNAMODB_REPORTS_TABLE,
                Item=dynamodb_item
            )
            save_duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[DYNAMODB_SAVE_SUCCESS] 保存耗时: {save_duration}秒")
        except Exception as dynamo_error:
            logger.error(f"[DYNAMODB_SAVE_ERROR] 保存失败: {str(dynamo_error)}")
            raise
        
        logger.info(f"[REPORT_COMPLETE] 报告保存完成 | Report ID: {report_id} | S3 Key: {s3_key}")
        return report_id
    except Exception as e:
        logger.error(f"[REPORT_ERROR] 保存报告失败: {str(e)}", exc_info=True)  # 添加完整的异常堆栈
        return None

def lambda_handler(event, context):
    """Lambda处理函数"""
    try:
        logger.info("=== 开始处理Lambda请求 ===")
        logger.info(f"Request ID: {context.aws_request_id}")
        logger.info(f"Function Name: {context.function_name}")
        logger.info(f"Memory Limit: {context.memory_limit_in_mb}MB")
        logger.info(f"Time Remaining: {context.get_remaining_time_in_millis()}ms")
        
        # 记录事件内容
        logger.info("Event内容:")
        logger.info(json.dumps(event, indent=2, ensure_ascii=False))
        
        # 检查是否是Bedrock Agent的调用
        if 'actionGroup' in event and 'apiPath' in event:
            logger.info("=== 处理Bedrock Agent请求 ===")
            result = handle_bedrock_agent_request(event, context)
            logger.info("=== Bedrock Agent请求处理完成 ===")
            return result
        
        # 处理常规API请求
        try:
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        except Exception as e:
            logger.error(f"解析请求体失败: {str(e)}")
            body = {}
        
        logger.info("请求参数:")
        logger.info(json.dumps(body, indent=2, ensure_ascii=False))
        
        file_id = body.get('file_id')
        model_id = body.get('model_id', 'anthropic.claude-v2')
        framework = body.get('framework', 'langchain')
        prompt_template = body.get('prompt_template', "请根据以下内容生成一份详细的会议报告:\n\n{content}\n\n报告:")
        
        logger.info(f"处理参数 - File ID: {file_id}")
        logger.info(f"处理参数 - Model ID: {model_id}")
        logger.info(f"处理参数 - Framework: {framework}")
        
        # 验证参数
        if not file_id:
            error_msg = "缺少必要参数: file_id"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg})
            }
        
        # 获取文件内容
        logger.info(f"=== 开始获取文件内容 - File ID: {file_id} ===")
        file_content = get_file_content(file_id)
        if not file_content:
            error_msg = f"无法获取文件内容: {file_id}"
            logger.error(error_msg)
            return {
                'statusCode': 404,
                'body': json.dumps({'error': error_msg})
            }
        logger.info(f"文件内容获取成功 - 长度: {len(file_content)} 字符")
        
        # 生成报告
        logger.info(f"=== 开始生成报告 - Framework: {framework} ===")
        if framework.lower() == 'langchain':
            report_content = generate_report_with_langchain(file_content, model_id, prompt_template)
        elif framework.lower() == 'haystack':
            report_content = generate_report_with_haystack(file_content, model_id, prompt_template)
        else:
            error_msg = f"不支持的框架: {framework}"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg})
            }
        
        if not report_content:
            error_msg = "生成报告失败"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg})
            }
        logger.info(f"报告生成成功 - 长度: {len(report_content)} 字符")
        
        # 保存报告
        logger.info("=== 开始保存报告 ===")
        report_id = save_report(file_id, report_content, model_id, framework)
        if not report_id:
            error_msg = "保存报告失败"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg})
            }
        
        # 返回结果
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'report_id': report_id,
                'file_id': file_id,
                'model_id': model_id,
                'framework': framework
            })
        }
        logger.info(f"=== Lambda请求处理完成 - Report ID: {report_id} ===")
        return result
        
    except Exception as e:
        error_msg = f"处理请求时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

def handle_bedrock_agent_request(event, context):
    """处理来自Bedrock Agent的请求"""
    try:
        logger.info("处理Bedrock Agent请求")
        
        # 获取API路径和动作组
        api_path = event.get('apiPath')
        action_group = event.get('actionGroup')
        
        # 获取请求参数
        parameters = event.get('parameters', [])
        param_dict = {}
        for param in parameters:
            param_dict[param.get('name')] = param.get('value')
        
        logger.info(f"API路径: {api_path}, 动作组: {action_group}, 参数: {param_dict}")
        
        # 处理生成报告请求
        if api_path == "/generateReport":
            report_type = param_dict.get('report_type', 'general')
            data_source = param_dict.get('data_source', 'meeting minutes')
            time_period = param_dict.get('time_period', 'weekly')
            
            # 从请求体中获取文本内容
            request_body = event.get('requestBody', {})
            text_content = request_body.get('content', '')
            
            # 如果请求体中没有内容，则使用会话历史
            if not text_content:
                session_attributes = event.get('sessionAttributes', {})
                messages = session_attributes.get('messages', [])
                if messages:
                    # 使用最后一条用户消息作为内容
                    for msg in reversed(messages):
                        if msg.get('role') == 'user':
                            text_content = msg.get('content', '')
                            break
            
            # 如果仍然没有内容，则使用事件本身作为内容
            if not text_content:
                text_content = json.dumps(event)
            
            # 生成报告
            model_id = "anthropic.claude-v2"
            framework = "langchain"
            report_content = generate_report_from_text(text_content, model_id, framework)
            
            if not report_content:
                return {
                    "messageVersion": "1.0",
                    "response": {
                        "actionGroup": action_group,
                        "apiPath": api_path,
                        "httpMethod": event.get('httpMethod', 'POST'),
                        "httpStatusCode": 500,
                        "responseBody": {
                            "error": "生成报告失败"
                        }
                    }
                }
            
            # 返回结果
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": action_group,
                    "apiPath": api_path,
                    "httpMethod": event.get('httpMethod', 'POST'),
                    "httpStatusCode": 200,
                    "responseBody": {
                        "application/json": {
                            "report": report_content,
                            "report_type": report_type,
                            "data_source": data_source,
                            "time_period": time_period,
                            "generation_time": datetime.now().isoformat()
                        }
                    }
                }
            }
        else:
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": action_group,
                    "apiPath": api_path,
                    "httpMethod": event.get('httpMethod', 'POST'),
                    "httpStatusCode": 400,
                    "responseBody": {
                        "error": f"不支持的API路径: {api_path}"
                    }
                }
            }
    except Exception as e:
        logger.error(f"处理Bedrock Agent请求时出错: {e}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', ''),
                "apiPath": event.get('apiPath', ''),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 500,
                "responseBody": {
                    "error": f"处理请求时出错: {str(e)}"
                }
            }
        } 