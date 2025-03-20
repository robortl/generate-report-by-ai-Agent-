import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加应用程序目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ['S3_BUCKET_NAME'] = 'report-langchain-haystack-files'

# 导入存储服务
from app.services.storage import upload_file_to_s3, S3_BUCKET_NAME

def create_test_file():
    """创建测试文件"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = f"test_direct_upload_{timestamp}.txt"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("这是一个直接测试S3上传的文件内容")
        
        logger.info(f"测试文件创建成功: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"创建测试文件时出错: {str(e)}")
        return None

def test_direct_upload():
    """直接测试S3上传"""
    # 打印环境变量
    logger.info(f"S3_BUCKET_NAME环境变量: {S3_BUCKET_NAME}")
    
    # 创建测试文件
    file_path = create_test_file()
    if not file_path:
        return
    
    try:
        # 打开文件并上传
        with open(file_path, 'rb') as file:
            s3_key = f"test/{file_path}"
            logger.info(f"正在上传文件 {file_path} 到S3，键: {s3_key}")
            
            s3_url = upload_file_to_s3(file, s3_key)
            logger.info(f"文件上传成功！URL: {s3_url}")
    except Exception as e:
        logger.error(f"上传文件时出错: {str(e)}")
    finally:
        # 清理测试文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"测试文件已删除: {file_path}")
        except Exception as e:
            logger.error(f"删除测试文件时出错: {str(e)}")

if __name__ == "__main__":
    test_direct_upload() 