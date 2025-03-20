import os
# 设置环境变量，确保不使用模拟数据
os.environ['USE_LOCAL_MOCK'] = 'false'
os.environ['DYNAMODB_TABLE'] = 'report'  # 修正表名前缀，实际表名为report_files, report_models, report_reports

import sys
import json
import requests
import logging
import time
import boto3
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# API基础URL
API_BASE_URL = "http://127.0.0.1:5000"

def create_test_file():
    """创建测试文件"""
    logger.info("创建测试文件")
    
    # 创建一个临时文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"test_record_{timestamp}.txt"
    file_path = f"test_record_{timestamp}.txt"
    
    # 写入一些测试内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件，用于API集成测试。\n")
        f.write(f"创建时间: {timestamp}\n")
        f.write("会议内容：\n")
        f.write("张三：大家好，今天我们讨论一下项目进度。\n")
        f.write("李四：好的，我这边的模块已经完成了80%。\n")
        f.write("王五：我负责的部分也已经测试通过了。\n")
        f.write("张三：太好了，看来我们可以按时交付了。\n")
    
    logger.info(f"测试文件已创建: {file_path}")
    return file_path, file_name

def check_dynamodb_directly(file_id):
    """直接从DynamoDB中获取文件元数据，验证数据是否正确保存"""
    logger.info(f"直接从DynamoDB中获取文件元数据: {file_id}")
    
    try:
        # 创建DynamoDB资源
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table_name = f"{os.environ.get('DYNAMODB_TABLE', 'report')}-files"
        logger.info(f"使用DynamoDB表名: {table_name}")
        table = dynamodb.Table(table_name)
        
        # 获取文件元数据
        response = table.get_item(Key={'file_id': file_id})
        
        if 'Item' in response:
            file_metadata = response['Item']
            logger.info(f"从DynamoDB直接获取的文件元数据: {json.dumps(file_metadata, indent=2)}")
            return file_metadata
        else:
            logger.error(f"在DynamoDB中未找到文件ID: {file_id}")
            return None
    except Exception as e:
        logger.error(f"从DynamoDB获取文件元数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_upload_file():
    """测试上传文件接口"""
    logger.info("=== 测试上传文件接口 ===")
    
    # 创建测试文件
    file_path, file_name = create_test_file()
    
    try:
        # 上传文件
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            data = {'category': 'meeting'}
            response = requests.post(f"{API_BASE_URL}/api/upload", files=files, data=data)
        
        if response.status_code not in [200, 201]:
            logger.error(f"上传文件失败: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return None
        
        result = response.json()
        file_id = result.get('file_id')
        logger.info(f"文件上传成功，ID: {file_id}")
        
        # 获取文件元数据 - 使用/api/files?file_id={file_id}路由
        response = requests.get(f"{API_BASE_URL}/api/files?file_id={file_id}")
        if response.status_code != 200:
            logger.error(f"获取文件元数据失败: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return None
        
        result = response.json()
        logger.info(f"文件元数据响应: {json.dumps(result, indent=2)}")
        
        # 处理返回的数据格式
        if isinstance(result, dict) and 'items' in result:
            # 返回的是文件列表，尝试在列表中找到匹配的文件
            file_metadata = None
            for item in result['items']:
                if item.get('file_id') == file_id:
                    file_metadata = item
                    break
            
            if not file_metadata:
                logger.error(f"在返回的文件列表中未找到匹配的文件ID: {file_id}")
                # 检查是否返回了模拟数据
                if result['items'] and result['items'][0].get('file_id') == 'sample-file-id-1':
                    logger.error("API返回的是模拟数据，而不是真实的DynamoDB数据")
                return None
        else:
            # 返回的是单个文件的元数据
            file_metadata = result
        
        logger.info(f"处理后的文件元数据: {json.dumps(file_metadata, indent=2)}")
        
        # 验证文件元数据
        assert file_metadata['file_id'] == file_id, "文件ID不匹配"
        assert 'original_filename' in file_metadata, "文件名不存在"
        assert file_metadata['category'] == 'meeting', "分类不匹配"
        assert 'status' in file_metadata, "状态不存在"
        assert 's3_key' in file_metadata, "S3键不存在"
        assert 's3_url' in file_metadata, "S3 URL不存在"
        
        logger.info("文件元数据验证成功")
        return file_id, file_metadata
        
    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"临时文件已删除: {file_path}")

def test_create_report(file_id):
    """测试创建报告接口"""
    logger.info("=== 测试创建报告接口 ===")
    
    # 创建报告
    data = {
        'file_id': file_id
    }
    response = requests.post(f"{API_BASE_URL}/api/reports", json=data)
    if response.status_code != 201:
        logger.error(f"创建报告失败: {response.status_code}")
        logger.error(f"错误信息: {response.text}")
        return None
    
    result = response.json()
    report_id = result.get('report_id')
    logger.info(f"报告创建成功，ID: {report_id}")
    
    # 等待报告生成完成
    max_retries = 10
    retry_interval = 2  # 秒
    
    for i in range(max_retries):
        # 获取报告
        response = requests.get(f"{API_BASE_URL}/api/reports/{report_id}")
        if response.status_code != 200:
            logger.error(f"获取报告失败: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return None
        
        report = response.json()
        status = report.get('status')
        
        if status == 'completed':
            logger.info(f"报告生成完成，状态: {status}")
            break
        elif status == 'failed':
            logger.error(f"报告生成失败，状态: {status}")
            return None
        else:
            logger.info(f"报告正在生成中，状态: {status}，等待 {retry_interval} 秒后重试...")
            time.sleep(retry_interval)
    else:
        logger.error(f"报告生成超时，最后状态: {status}")
        return None
    
    # 验证报告内容
    logger.info(f"报告标题: {report.get('title')}")
    logger.info(f"报告状态: {report.get('status')}")
    
    if 'content' in report:
        content_length = len(report['content'])
        logger.info(f"报告内容长度: {content_length} 字符")
        if content_length > 0:
            logger.info(f"报告内容前100个字符: {report['content'][:100]}")
    else:
        logger.warning("报告内容不存在")
    
    # 获取文件元数据，验证report_id字段
    response = requests.get(f"{API_BASE_URL}/api/files/{file_id}")
    if response.status_code != 200:
        logger.error(f"获取文件元数据失败: {response.status_code}")
        logger.error(f"错误信息: {response.text}")
        return None

    result = response.json()
    
    # 检查是否返回了单个文件的元数据
    if isinstance(result, dict) and 'items' in result:
        # 返回的是文件列表，尝试在列表中找到匹配的文件
        file_metadata = None
        for item in result['items']:
            if item.get('file_id') == file_id:
                file_metadata = item
                break
        
        if not file_metadata:
            logger.error(f"在返回的文件列表中未找到匹配的文件ID: {file_id}")
            return None
    else:
        # 返回的是单个文件的元数据
        file_metadata = result
    
    logger.info(f"更新后的文件元数据: {json.dumps(file_metadata, indent=2)}")
    
    # 验证文件元数据中的report_id字段
    if 'report_id' in file_metadata and file_metadata['report_id'] == report_id:
        logger.info(f"文件元数据中的report_id字段已正确更新: {report_id}")
    else:
        logger.error(f"文件元数据中的report_id字段未正确更新，期望: {report_id}, 实际: {file_metadata.get('report_id')}")
    
    # 验证文件状态
    if file_metadata.get('status') == 'processed':
        logger.info("文件状态已正确更新为'processed'")
    else:
        logger.error(f"文件状态未正确更新，期望: processed, 实际: {file_metadata.get('status')}")
    
    return report_id, report

def test_api_integration():
    """测试API集成"""
    logger.info("=== 开始API集成测试 ===")
    
    # 测试上传文件
    result = test_upload_file()
    if not result:
        logger.error("上传文件测试失败")
        return False
    
    file_id, file_metadata = result
    
    # 测试创建报告
    result = test_create_report(file_id)
    if not result:
        logger.error("创建报告测试失败")
        return False
    
    report_id, report = result
    
    logger.info("=== API集成测试完成 ===")
    return True

def main():
    """主函数"""
    try:
        # 测试API集成
        success = test_api_integration()
        
        if success:
            logger.info("所有测试通过！")
        else:
            logger.error("测试失败！")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 