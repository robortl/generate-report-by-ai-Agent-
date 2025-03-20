import os
import sys
import json
import requests
import logging
from datetime import datetime

# 配置日志
def setup_logging():
    """设置日志配置"""
    # 创建logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # 确保没有重复的处理器
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
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

# API基础URL
API_BASE_URL = "http://localhost:5000"
TEST_FILE_ID = "97598f92-cb02-4693-950a-2a1c559c31aa"

def test_create_report():
    """测试创建报告API"""
    logger.info("=== 测试创建报告API ===")
    
    # 强制刷新输出缓冲区
    sys.stdout.flush()
    
    # 获取文件列表
    response = requests.get(f"{API_BASE_URL}/api/files?file_id={TEST_FILE_ID}",timeout=30)
    if response.status_code != 200:
        logger.error(f"获取文件列表失败: {response.status_code}")
        logger.error(f"错误响应: {response.text}")
        return None
    
    response_data = response.json()
    files = response_data.get('items', [])
    if not files:
        logger.error("没有可用的文件")
        logger.error(f"API响应: {response_data}")
        return None
    
    # 选择第一个文件
    file_id = files[0].get('file_id')
    if not file_id:
        logger.error("文件元数据中没有file_id字段")
        logger.error(f"文件元数据: {response.json()}")
        return None
        
    logger.info(f"选择文件: {file_id}")
    
    # 创建报告
    data = {
        'file_id': file_id
    }
    response = requests.post(f"{API_BASE_URL}/api/report/generate", json=data,timeout=30)
    if response.status_code != 201 and response.status_code != 200:
        logger.error(f"创建报告失败: {response.status_code}")
        logger.error(f"错误响应: {response.text}")
        return None
    
    result = response.json()
    report_id = result.get('data').get('report_id')
    if not report_id:
        logger.error("响应中没有report_id字段")
        logger.error(f"API响应: {result}")
        return None
        
    logger.info(f"报告创建成功，ID: {report_id}")
    
    # 获取报告
    response = requests.get(f"{API_BASE_URL}/api/report/{report_id}",timeout=30)
    if response.status_code != 200:
        logger.error(f"获取报告失败: {response.status_code}")
        logger.error(f"错误响应: {response.text}")
        return None
    
    report = response.json()
    logger.info(f"报告标题: {report.get('title')}")
    logger.info(f"报告状态: {report.get('status')}")
    
    # 获取文件元数据
    response = requests.get(f"{API_BASE_URL}/api/report/{report_id}",timeout=30)
    if response.status_code != 200:
        logger.error(f"获取文件元数据失败: {response.status_code}")
        logger.error(f"错误响应: {response.text}")
        return None
    
    file_metadata = response.json()
    logger.info(f"文件元数据: {json.dumps(file_metadata, indent=2)}")
    
    # 验证文件元数据中的report_id字段
    if 'report_id' in file_metadata and file_metadata['report_id'] == report_id:
        logger.info(f"文件元数据中的report_id字段已正确更新: {report_id}")
    else:
        logger.error(f"文件元数据中的report_id字段未正确更新，期望: {report_id}, 实际: {file_metadata.get('report_id')}")
    
    return report_id, file_id

def main():
    """主函数"""
    try:
        logger.info("开始执行测试...")
        # 测试创建报告API
        result = test_create_report()
        
        if result:
            logger.info("测试成功完成")
        else:
            logger.error("测试执行失败")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 确保所有日志都被输出
        sys.stdout.flush()
        logging.shutdown()

if __name__ == "__main__":
    main() 