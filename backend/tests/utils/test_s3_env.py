import os
import boto3
import logging
from botocore.exceptions import ClientError

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_s3_env():
    """测试S3环境变量和连接"""
    # 打印环境变量
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME', 'default-bucket-name')
    logger.info(f"S3_BUCKET_NAME环境变量: {s3_bucket_name}")
    
    # 测试S3连接
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        logger.info("S3连接成功！")
        logger.info("存储桶列表:")
        for bucket in response['Buckets']:
            logger.info(f"  - {bucket['Name']}")
        
        # 检查指定的存储桶是否存在
        bucket_exists = False
        for bucket in response['Buckets']:
            if bucket['Name'] == s3_bucket_name:
                bucket_exists = True
                logger.info(f"指定的存储桶 {s3_bucket_name} 存在")
                break
        
        if not bucket_exists:
            logger.warning(f"指定的存储桶 {s3_bucket_name} 不存在")
        
        return True
    except ClientError as e:
        logger.error(f"S3连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_s3_env() 