#!/usr/bin/env python
"""
测试AWS S3连接并上传测试文件
"""
import os
import boto3
import botocore.exceptions
import uuid
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_s3_connection():
    """测试与AWS S3的连接"""
    try:
        # 获取AWS会话，使用本地凭证
        session = boto3.Session()
        region_name = session.region_name or "ap-northeast-1"
        
        # 获取S3客户端
        s3_client = session.client('s3', region_name=region_name)
        
        # 列出所有存储桶
        response = s3_client.list_buckets()
        
        # 打印存储桶列表
        logger.info("S3连接成功！")
        logger.info(f"区域: {region_name}")
        logger.info(f"存储桶列表:")
        for bucket in response['Buckets']:
            logger.info(f"  - {bucket['Name']}")
        
        return True, response['Buckets']
    except botocore.exceptions.NoCredentialsError:
        logger.error("未找到AWS凭证")
        return False, None
    except botocore.exceptions.ClientError as e:
        logger.error(f"AWS S3客户端错误: {str(e)}")
        return False, None
    except Exception as e:
        logger.error(f"测试S3连接时出错: {str(e)}")
        return False, None

def create_bucket_if_not_exists(bucket_name, region=None):
    """如果存储桶不存在，则创建"""
    try:
        session = boto3.Session()
        region_name = region or session.region_name or "ap-northeast-1"
        s3_client = session.client('s3', region_name=region_name)
        
        # 检查存储桶是否存在
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"存储桶 {bucket_name} 已存在")
            return True
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                # 存储桶不存在，创建它
                logger.info(f"存储桶 {bucket_name} 不存在，正在创建...")
                
                if region_name == 'us-east-1':
                    # us-east-1 区域需要特殊处理
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region_name}
                    )
                
                logger.info(f"存储桶 {bucket_name} 创建成功")
                return True
            else:
                logger.error(f"检查存储桶时出错: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"创建存储桶时出错: {str(e)}")
        return False

def upload_test_file(bucket_name, file_content="这是一个测试文件内容"):
    """上传测试文件到S3存储桶"""
    try:
        session = boto3.Session()
        region_name = session.region_name or "ap-northeast-1"
        s3_client = session.client('s3', region_name=region_name)
        
        # 生成唯一的文件名
        file_name = f"test-file-{uuid.uuid4()}.txt"
        
        # 上传文件
        logger.info(f"正在上传测试文件 {file_name} 到存储桶 {bucket_name}...")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_content
        )
        
        # 获取文件URL
        s3_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{file_name}"
        
        logger.info(f"文件上传成功！")
        logger.info(f"文件URL: {s3_url}")
        
        return True, file_name, s3_url
    except botocore.exceptions.NoCredentialsError:
        logger.error("未找到AWS凭证")
        return False, None, None
    except botocore.exceptions.ClientError as e:
        logger.error(f"AWS S3客户端错误: {str(e)}")
        return False, None, None
    except Exception as e:
        logger.error(f"上传测试文件时出错: {str(e)}")
        return False, None, None

def download_test_file(bucket_name, file_name):
    """从S3存储桶下载测试文件"""
    try:
        session = boto3.Session()
        region_name = session.region_name or "ap-northeast-1"
        s3_client = session.client('s3', region_name=region_name)
        
        # 下载文件
        logger.info(f"正在从存储桶 {bucket_name} 下载文件 {file_name}...")
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        
        # 读取文件内容
        file_content = response['Body'].read().decode('utf-8')
        
        logger.info(f"文件下载成功！")
        logger.info(f"文件内容: {file_content}")
        
        return True, file_content
    except botocore.exceptions.NoCredentialsError:
        logger.error("未找到AWS凭证")
        return False, None
    except botocore.exceptions.ClientError as e:
        logger.error(f"AWS S3客户端错误: {str(e)}")
        return False, None
    except Exception as e:
        logger.error(f"下载测试文件时出错: {str(e)}")
        return False, None

def main():
    """主函数"""
    # 测试S3连接
    connection_success, buckets = test_s3_connection()
    if not connection_success:
        logger.error("S3连接测试失败，请检查AWS凭证和网络连接")
        return
    
    # 设置存储桶名称
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'meeting-reports-bucket')
    
    # 检查存储桶是否存在，如果不存在则创建
    bucket_exists = create_bucket_if_not_exists(bucket_name)
    if not bucket_exists:
        logger.error(f"无法创建或访问存储桶 {bucket_name}")
        return
    
    # 上传测试文件
    upload_success, file_name, s3_url = upload_test_file(bucket_name)
    if not upload_success:
        logger.error("上传测试文件失败")
        return
    
    # 下载测试文件以验证上传成功
    download_success, file_content = download_test_file(bucket_name, file_name)
    if not download_success:
        logger.error("下载测试文件失败")
        return
    
    logger.info("AWS S3测试完成！所有操作都成功。")

if __name__ == "__main__":
    main() 