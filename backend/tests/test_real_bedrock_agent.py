#!/usr/bin/env python
"""
测试真实的Bedrock Agent调用
"""
import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 确保不使用本地模拟模式
os.environ['USE_LOCAL_MOCK'] = 'false'

# 设置正确的DynamoDB表名前缀
os.environ['DYNAMODB_TABLE'] = 'report'

from app.services.agent_service import generate_report, bedrock_agent_service
from app.services.storage import save_report, get_report_from_dynamodb

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_to_file(content, filename):
    """保存内容到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"报告已保存到 {filename}")

def read_file(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件时出错: {e}")
        return None

def test_with_file(file_path, prompt=None):
    """使用文件内容测试Bedrock Agent"""
    logger.info(f"使用文件 {file_path} 测试Bedrock Agent")
    
    # 读取文件内容
    content = read_file(file_path)
    if not content:
        logger.error("无法读取文件内容")
        return False
    
    logger.info(f"文件内容长度: {len(content)} 字符")
    
    # 打印Bedrock Agent服务信息
    logger.info(f"Bedrock Agent ID: {bedrock_agent_service.agent_id}")
    logger.info(f"Bedrock Agent Alias ID: {bedrock_agent_service.agent_alias_id}")
    logger.info(f"AWS Region: {bedrock_agent_service.region_name}")
    logger.info(f"DynamoDB表名前缀: {os.environ.get('DYNAMODB_TABLE')}")
    logger.info(f"S3存储桶名称: {os.environ.get('S3_BUCKET_NAME')}")
    
    try:
        # 调用Bedrock Agent生成报告
        logger.info("调用Bedrock Agent生成报告...")
        start_time = time.time()
        
        report_content = generate_report(content, prompt=prompt)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"报告生成完成，耗时: {elapsed_time:.2f} 秒")
        logger.info(f"报告长度: {len(report_content)} 字符")
        
        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"generated_report_{timestamp}.md"
        save_to_file(report_content, output_file)
        
        # 保存报告到S3和DynamoDB
        report_id = f"test-report-{timestamp}"
        file_id = f"test-file-{timestamp}"
        
        # 创建一个虚拟的文件元数据，确保报告可以关联到一个文件
        file_metadata = {
            'file_id': file_id,
            'original_filename': f'test_file_{timestamp}.txt',
            'category': 'meeting',
            's3_key': f'uploads/{file_id}_test_file_{timestamp}.txt',
            's3_url': f'https://{os.environ.get("S3_BUCKET_NAME")}.s3.{bedrock_agent_service.region_name}.amazonaws.com/uploads/{file_id}_test_file_{timestamp}.txt',
            'status': 'uploaded',
            'created_at': datetime.now().isoformat()
        }
        
        # 保存文件内容到S3
        from app.services.storage import upload_file_to_s3, save_metadata_to_dynamodb
        try:
            # 创建临时文件
            temp_file_path = f'temp_file_{timestamp}.txt'
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 上传文件到S3
            with open(temp_file_path, 'rb') as f:
                upload_file_to_s3(f, file_metadata['s3_key'])
            
            # 保存文件元数据到DynamoDB
            save_metadata_to_dynamodb(file_metadata)
            
            # 删除临时文件
            os.remove(temp_file_path)
            
            logger.info(f"文件已上传到S3，文件ID: {file_id}")
        except Exception as e:
            logger.error(f"上传文件到S3时出错: {e}")
        
        report_data = {
            'report_id': report_id,
            'file_id': file_id,
            'content': report_content,
            'model_id': 'anthropic.claude-v2',
            'prompt': prompt,
            'status': 'completed'
        }
        
        logger.info(f"保存报告到S3和DynamoDB，报告ID: {report_id}")
        save_report(report_data)
        
        # 验证报告是否保存成功
        logger.info(f"从DynamoDB获取报告，报告ID: {report_id}")
        saved_report = get_report_from_dynamodb(report_id)
        
        if saved_report:
            logger.info(f"报告成功保存到DynamoDB，报告ID: {report_id}")
            logger.info(f"S3键: {saved_report.get('s3_key')}")
            logger.info(f"S3 URL: {saved_report.get('s3_url')}")
            
            # 检查S3中是否有报告文件
            from app.services.storage import get_s3_client
            try:
                s3_client = get_s3_client()
                s3_response = s3_client.head_object(
                    Bucket=os.environ.get('S3_BUCKET_NAME'),
                    Key=saved_report.get('s3_key')
                )
                logger.info(f"报告文件存在于S3，大小: {s3_response.get('ContentLength')} 字节")
            except Exception as e:
                logger.error(f"检查S3报告文件时出错: {e}")
        else:
            logger.error(f"报告未保存到DynamoDB，报告ID: {report_id}")
        
        # 打印报告前500个字符
        preview_length = min(500, len(report_content))
        logger.info(f"报告预览 (前 {preview_length} 字符):\n{report_content[:preview_length]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"生成报告时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_with_text(text, prompt=None):
    """使用文本测试Bedrock Agent"""
    logger.info("使用文本测试Bedrock Agent")
    logger.info(f"文本长度: {len(text)} 字符")
    
    # 打印Bedrock Agent服务信息
    logger.info(f"Bedrock Agent ID: {bedrock_agent_service.agent_id}")
    logger.info(f"Bedrock Agent Alias ID: {bedrock_agent_service.agent_alias_id}")
    logger.info(f"AWS Region: {bedrock_agent_service.region_name}")
    logger.info(f"DynamoDB表名前缀: {os.environ.get('DYNAMODB_TABLE')}")
    logger.info(f"S3存储桶名称: {os.environ.get('S3_BUCKET_NAME')}")
    
    try:
        # 调用Bedrock Agent生成报告
        logger.info("调用Bedrock Agent生成报告...")
        start_time = time.time()
        
        report_content = generate_report(text, prompt=prompt)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"报告生成完成，耗时: {elapsed_time:.2f} 秒")
        logger.info(f"报告长度: {len(report_content)} 字符")
        
        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"generated_report_{timestamp}.md"
        save_to_file(report_content, output_file)
        
        # 保存报告到S3和DynamoDB
        report_id = f"test-report-{timestamp}"
        file_id = f"test-file-{timestamp}"
        
        # 创建一个虚拟的文件元数据，确保报告可以关联到一个文件
        file_metadata = {
            'file_id': file_id,
            'original_filename': f'test_file_{timestamp}.txt',
            'category': 'meeting',
            's3_key': f'uploads/{file_id}_test_file_{timestamp}.txt',
            's3_url': f'https://{os.environ.get("S3_BUCKET_NAME")}.s3.{bedrock_agent_service.region_name}.amazonaws.com/uploads/{file_id}_test_file_{timestamp}.txt',
            'status': 'uploaded',
            'created_at': datetime.now().isoformat()
        }
        
        # 保存文件内容到S3
        from app.services.storage import upload_file_to_s3, save_metadata_to_dynamodb
        try:
            # 创建临时文件
            temp_file_path = f'temp_file_{timestamp}.txt'
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # 上传文件到S3
            with open(temp_file_path, 'rb') as f:
                upload_file_to_s3(f, file_metadata['s3_key'])
            
            # 保存文件元数据到DynamoDB
            save_metadata_to_dynamodb(file_metadata)
            
            # 删除临时文件
            os.remove(temp_file_path)
            
            logger.info(f"文件已上传到S3，文件ID: {file_id}")
        except Exception as e:
            logger.error(f"上传文件到S3时出错: {e}")
        
        report_data = {
            'report_id': report_id,
            'file_id': file_id,
            'content': report_content,
            'model_id': 'anthropic.claude-v2',
            'prompt': prompt,
            'status': 'completed'
        }
        
        logger.info(f"保存报告到S3和DynamoDB，报告ID: {report_id}")
        save_report(report_data)
        
        # 验证报告是否保存成功
        logger.info(f"从DynamoDB获取报告，报告ID: {report_id}")
        saved_report = get_report_from_dynamodb(report_id)
        
        if saved_report:
            logger.info(f"报告成功保存到DynamoDB，报告ID: {report_id}")
            logger.info(f"S3键: {saved_report.get('s3_key')}")
            logger.info(f"S3 URL: {saved_report.get('s3_url')}")
            
            # 检查S3中是否有报告文件
            from app.services.storage import get_s3_client
            try:
                s3_client = get_s3_client()
                s3_response = s3_client.head_object(
                    Bucket=os.environ.get('S3_BUCKET_NAME'),
                    Key=saved_report.get('s3_key')
                )
                logger.info(f"报告文件存在于S3，大小: {s3_response.get('ContentLength')} 字节")
            except Exception as e:
                logger.error(f"检查S3报告文件时出错: {e}")
        else:
            logger.error(f"报告未保存到DynamoDB，报告ID: {report_id}")
        
        # 打印报告前500个字符
        preview_length = min(500, len(report_content))
        logger.info(f"报告预览 (前 {preview_length} 字符):\n{report_content[:preview_length]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"生成报告时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='测试Bedrock Agent生成报告')
    parser.add_argument('--file', '-f', help='输入文件路径')
    parser.add_argument('--text', '-t', help='输入文本')
    parser.add_argument('--prompt', '-p', help='自定义提示词')
    parser.add_argument('--aws-profile', help='AWS配置文件名称')
    parser.add_argument('--s3-bucket', help='S3存储桶名称')
    parser.add_argument('--dynamodb-table', help='DynamoDB表名前缀')
    parser.add_argument('--region', help='AWS区域')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置AWS配置
    if args.aws_profile:
        os.environ['AWS_PROFILE'] = args.aws_profile
    
    if args.s3_bucket:
        os.environ['S3_BUCKET_NAME'] = args.s3_bucket
    
    if args.dynamodb_table:
        os.environ['DYNAMODB_TABLE'] = args.dynamodb_table
    
    if args.region:
        os.environ['AWS_DEFAULT_REGION'] = args.region
    
    if args.file:
        test_with_file(args.file, prompt=args.prompt)
    elif args.text:
        test_with_text(args.text, prompt=args.prompt)
    else:
        # 使用默认测试文本
        default_text = """这是一个测试会议记录文件，用于测试报告生成功能。
会议日期：2025年3月15日
参会人员：张三、李四、王五
会议主题：项目进度讨论
会议内容：
1. 张三汇报了项目A的进度，目前已完成80%。
2. 李四提出了项目B的几个问题，需要团队协作解决。
3. 王五分享了市场调研结果，建议调整产品策略。
会议结论：
1. 项目A将在下周完成。
2. 项目B的问题将由张三和李四共同解决。
3. 产品策略调整方案将在下次会议讨论。
"""
        test_with_text(default_text, prompt=args.prompt)

if __name__ == '__main__':
    main() 