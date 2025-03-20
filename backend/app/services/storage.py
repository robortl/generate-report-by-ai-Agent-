import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import logging
import uuid

# 配置日志
logger = logging.getLogger(__name__)

# 获取环境变量
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'report-langchain-haystack-files')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'report')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1')


# 本地存储（用于测试）
local_files = {}
local_metadata = {}
local_reports = {}

# 创建AWS客户端
def get_s3_client():
    """获取S3客户端"""

    # 如果环境变量中没有凭证，尝试使用默认凭证提供链
    logger.info("使用默认凭证提供链")
    return boto3.client('s3', region_name=AWS_REGION)

def get_dynamodb_client():
    """获取DynamoDB客户端"""

    # 如果环境变量中没有凭证，尝试使用默认凭证提供链
    logger.info("使用默认凭证提供链")
    return boto3.client('dynamodb', region_name=AWS_REGION)

def get_dynamodb_resource():
    """获取DynamoDB资源"""

    # 如果环境变量中没有凭证，尝试使用默认凭证提供链
    logger.info("使用默认凭证提供链")
    return boto3.resource('dynamodb', region_name=AWS_REGION)

# S3操作函数
def upload_file_to_s3(file, s3_key):
    """上传文件到S3"""
    logger.info(f"S3_BUCKET_NAME环境变量: {S3_BUCKET_NAME}")
    

    
    # 检查S3存储桶是否存在，如果不存在则创建
    s3_client = get_s3_client()
    logger.info(f"使用S3客户端上传文件到存储桶: {S3_BUCKET_NAME}")
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == '404':
            logger.info(f"S3存储桶 {S3_BUCKET_NAME} 不存在，正在创建...")
            try:
                s3_client.create_bucket(
                    Bucket=S3_BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
                logger.info(f"S3存储桶 {S3_BUCKET_NAME} 创建成功")
            except ClientError as create_error:
                logger.error(f"创建S3存储桶失败: {str(create_error)}")
                raise Exception(f"Error creating S3 bucket: {str(create_error)}")
        else:
            logger.error(f"检查S3存储桶时出错: {str(e)}")
            raise Exception(f"Error checking S3 bucket: {str(e)}")
    
    try:
        file.seek(0)  # 重置文件指针
        s3_client.upload_fileobj(file, S3_BUCKET_NAME, s3_key)
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except ClientError as e:
        logger.error(f"上传文件到S3时出错: {str(e)}")
        raise Exception(f"Error uploading file to S3: {str(e)}")

def get_file_from_s3(s3_key):
    """从S3获取文件内容"""

    
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        logger.error(f"从S3获取文件时出错: {str(e)}")
        raise Exception(f"Error getting file from S3: {str(e)}")

def delete_file_from_s3(s3_key):
    """从S3删除文件"""

    s3_client = get_s3_client()
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        logger.error(f"从S3删除文件时出错: {str(e)}")
        raise Exception(f"Error deleting file from S3: {str(e)}")

# DynamoDB操作函数
def save_metadata_to_dynamodb(metadata):
    """保存元数据到DynamoDB"""

    dynamodb = get_dynamodb_resource()
    table_name = "report_files"  # 使用固定的表名
    
    # 检查表是否存在，如果不存在则创建
    try:
        dynamodb_client = get_dynamodb_client()
        dynamodb_client.describe_table(TableName=table_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info(f"DynamoDB表 {table_name} 不存在，正在创建...")
            try:
                dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
                    ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                )
                # 等待表创建完成
                waiter = dynamodb_client.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
                logger.info(f"DynamoDB表 {table_name} 创建成功")
            except ClientError as create_error:
                logger.error(f"创建DynamoDB表失败: {str(create_error)}")
                raise Exception(f"Error creating DynamoDB table: {str(create_error)}")
        else:
            logger.error(f"检查DynamoDB表时出错: {str(e)}")
            raise Exception(f"Error checking DynamoDB table: {str(e)}")
    
    table = dynamodb.Table(table_name)
    
    try:
        response = table.put_item(Item=metadata)
        return response
    except ClientError as e:
        logger.error(f"保存元数据到DynamoDB时出错: {str(e)}")
        raise Exception(f"Error saving metadata to DynamoDB: {str(e)}")

def get_metadata_from_dynamodb(file_id):
    """从DynamoDB获取元数据"""

    
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table("report_files")  # 使用固定的表名
    
    try:
        response = table.get_item(Key={'file_id': file_id})
        return response.get('Item')
    except ClientError as e:
        logger.error(f"从DynamoDB获取元数据时出错: {str(e)}")
        raise Exception(f"Error getting metadata from DynamoDB: {str(e)}")

def update_metadata_in_dynamodb(metadata):
    """更新DynamoDB中的元数据"""

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(f"{DYNAMODB_TABLE}_files")
    
    try:
        response = table.put_item(Item=metadata)
        return response
    except ClientError as e:
        logger.error(f"更新DynamoDB中的元数据时出错: {str(e)}")
        raise Exception(f"Error updating metadata in DynamoDB: {str(e)}")

def delete_metadata_from_dynamodb(file_id):
    """从DynamoDB删除元数据"""

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(f"{DYNAMODB_TABLE}_files")
    
    try:
        response = table.delete_item(Key={'file_id': file_id})
        return response
    except ClientError as e:
        logger.error(f"从DynamoDB删除元数据时出错: {str(e)}")
        raise Exception(f"Error deleting metadata from DynamoDB: {str(e)}")

def list_files_from_dynamodb(category=None, limit=50, last_evaluated_key=None):
    """从DynamoDB列出文件"""

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table("report_files")  # 使用固定的表名
    
    scan_kwargs = {
        'Limit': limit
    }
    
    if category:
        scan_kwargs['FilterExpression'] = boto3.dynamodb.conditions.Attr('category').eq(category)
    
    if last_evaluated_key:
        scan_kwargs['ExclusiveStartKey'] = {'file_id': last_evaluated_key}
    
    try:
        response = table.scan(**scan_kwargs)
        return response
    except ClientError as e:
        logger.error(f"从DynamoDB列出文件时出错: {str(e)}")
        raise Exception(f"Error listing files from DynamoDB: {str(e)}")

def save_report(file_id: str, report_content: str) -> Dict[str, Any]:
    """保存报告到S3和DynamoDB"""
    try:
        logger.info(f"[STORAGE_START] 开始保存报告 | 文件ID: {file_id}")
        
        # 生成报告ID
        report_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        # 检查report_content是否为JSON字符串
        try:
            # 尝试解析JSON
            if isinstance(report_content, str) and report_content.strip().startswith('{'):
                report_data = json.loads(report_content)
                report_id = report_data.get('report_id', report_id)
                content = report_data.get('content', report_content)
                status = report_data.get('status', 'completed')
                title = report_data.get('title', f"Report for file {file_id}")
                model_id = report_data.get('model_id')
                prompt = report_data.get('prompt')
                created_at = report_data.get('created_at', current_time)
            else:
                # 使用原始内容
                content = report_content
                status = 'completed'
                title = f"Report for file {file_id}"
                model_id = None
                prompt = None
                created_at = current_time
        except json.JSONDecodeError:
            # 如果JSON解析失败，使用原始内容
            content = report_content
            status = 'completed'
            title = f"Report for file {file_id}"
            model_id = None
            prompt = None
            created_at = current_time
            
        logger.debug(f"[STORAGE_CONTENT] 报告内容长度: {len(content)} | 前200个字符: {content[:200]}...")

        # 生成S3键
        s3_key = f"reports/{report_id}.txt"
        logger.info(f"[STORAGE_INFO] 报告ID: {report_id} | S3键: {s3_key}")

        # 保存到S3
        try:
            logger.info("[S3_UPLOAD] 开始上传到S3")
            s3_client = get_s3_client()
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/plain; charset=utf-8'
            )
            logger.info(f"[S3_SUCCESS] 报告成功上传到S3 | 桶: {S3_BUCKET_NAME} | 键: {s3_key}")
        except Exception as s3_error:
            logger.error(f"[S3_ERROR] 上传到S3失败: {str(s3_error)}", exc_info=True)
            raise Exception(f"Failed to upload report to S3: {str(s3_error)}")

        # 更新DynamoDB中的报告数据
        try:
            logger.info("[DYNAMO_UPDATE] 开始更新DynamoDB元数据")
            
            # 准备报告数据
            report_item = {
                'report_id': report_id,
                'file_id': file_id,
                'report_s3_key': s3_key,
                'created_at': created_at,
                'updated_at': current_time,
                'status': status,
                'title': title,
                'model_id': model_id,
                'prompt': prompt
            }
            
            # 更新DynamoDB
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(f"{DYNAMODB_TABLE}_reports")
            response = table.put_item(Item=report_item)
            
            logger.info(f"[DYNAMO_SUCCESS] DynamoDB更新成功 | 报告ID: {report_id}")
            
            return report_item
            
        except Exception as dynamo_error:
            logger.error(f"[DYNAMO_ERROR] 更新DynamoDB失败: {str(dynamo_error)}", exc_info=True)
            # 如果DynamoDB更新失败，尝试删除已上传的S3对象
            try:
                logger.warning(f"[S3_CLEANUP] 尝试删除S3中的报告文件 | 键: {s3_key}")
                delete_file_from_s3(s3_key)
                logger.info("[S3_CLEANUP] S3文件清理成功")
            except Exception as cleanup_error:
                logger.error(f"[S3_CLEANUP_ERROR] 清理S3文件失败: {str(cleanup_error)}")
            raise Exception(f"Failed to update metadata in DynamoDB: {str(dynamo_error)}")

    except Exception as e:
        error_msg = f"保存报告失败: {str(e)}"
        logger.error(f"[STORAGE_ERROR] {error_msg}", exc_info=True)
        raise Exception(error_msg)

def get_report_from_dynamodb(report_id):
    """从DynamoDB获取报告"""

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(f"{DYNAMODB_TABLE}_reports")
    
    try:
        response = table.get_item(Key={'report_id': report_id})
        return response
    except ClientError as e:
        logger.error(f"从DynamoDB获取报告时出错: {str(e)}")
        raise Exception(f"Error getting report from DynamoDB: {str(e)}")

def update_report_in_dynamodb(report_data):
    """更新DynamoDB中的报告"""

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(f"{DYNAMODB_TABLE}_reports")
    
    # 添加更新时间戳
    report_data['updated_at'] = datetime.now().isoformat()
    
    try:
        response = table.put_item(Item=report_data)
        return response
    except ClientError as e:
        logger.error(f"更新DynamoDB中的报告时出错: {str(e)}")
        raise Exception(f"Error updating report in DynamoDB: {str(e)}")

def delete_report_from_dynamodb(report_id):
    """从DynamoDB删除报告"""

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(f"{DYNAMODB_TABLE}_reports")
    
    try:
        response = table.delete_item(Key={'report_id': report_id})
        return response
    except ClientError as e:
        logger.error(f"从DynamoDB删除报告时出错: {str(e)}")
        raise Exception(f"Error deleting report from DynamoDB: {str(e)}")

def get_file_content_by_id(file_id):
    """通过文件ID获取文件内容"""
    try:
        logger.info(f"[获取文件内容] 正在获取文件ID: {file_id} 的内容")
        
        # 获取文件元数据
        metadata = get_metadata_from_dynamodb(file_id)
        if not metadata:
            logger.error(f"[获取文件内容] 找不到文件ID: {file_id} 的元数据")
            return None
            
        logger.info(f"[获取文件内容] 已获取元数据: {metadata.get('original_filename', '未知文件名')} | 类型: {metadata.get('file_type', '未知')}")
        
        # 从元数据获取S3键
        s3_key = metadata.get('s3_key')
        if not s3_key:
            logger.error(f"[获取文件内容] 元数据中找不到S3键，文件ID: {file_id}")
            return None
            
        logger.info(f"[获取文件内容] 正在从S3获取文件: {s3_key}")
        
        # 从S3获取文件内容
        try:
            content = get_file_from_s3(s3_key)
            content_length = len(content) if content else 0
            logger.info(f"[获取文件内容] 成功从S3获取文件内容，长度: {content_length} 字节")
            
            # 添加设置上下文表示这是从文件脚加载的内容
            # 创建一个内容的标记头，帮助模型识别这是一个文件
            original_filename = metadata.get('original_filename', '未知文件名')
            file_type = metadata.get('file_type', '未知文件类型')
            category = metadata.get('category', '未分类')
            
            # 去除文件内容开头的可能的UTF-8 BOM
            if content and content.startswith('\ufeff'):
                content = content[1:]
                
            # 添加文件元数据头
            metadata_header = f"""# 文件元数据
文件名: {original_filename}
文件类型: {file_type}
分类: {category}
文件ID: {file_id}

# 文件内容
"""
            
            # 将元数据头添加到内容开头
            content_with_header = metadata_header + content
            
            return content_with_header
        except Exception as s3_error:
            logger.error(f"[获取文件内容] 从S3获取文件内容时出错: {str(s3_error)}")
            return None
    except Exception as e:
        logger.error(f"[获取文件内容] 获取文件内容时发生未知错误: {str(e)}")
        return None 