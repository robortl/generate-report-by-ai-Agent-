import os
import sys
import json
import time
import logging
import pytest
import requests
from datetime import datetime

# 配置日志
def setup_logging():
    """设置日志配置"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# 获取logger实例
logger = setup_logging()

# API配置
API_BASE_URL = "http://localhost:5000"
TEST_REPORT_ID = "6ef60bec-49d5-45a3-b845-da1767ee3d8a"

def test_get_report():
    """测试获取报告API"""
    logger.info(f"[步骤1] 获取报告内容 | 报告ID: {TEST_REPORT_ID}")
    
    try:
        # 发送请求
        response = requests.get(
            f"{API_BASE_URL}/api/report/{TEST_REPORT_ID}",
            timeout=30
        )
        
        # 记录响应详情
        logger.info(f"获取报告响应状态码: {response.status_code}")
        logger.info(f"获取报告响应头: {dict(response.headers)}")
        
        # 解析响应内容
        response_data = response.json()
        logger.info(f"获取报告响应内容: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        # 使用pytest断言验证响应
        assert response.status_code == 200, f"预期状态码200，实际获得{response.status_code}"
        
        # 验证响应数据结构
        required_fields = ['report_id', 'content', 'file_id', 'status', 's3_key']
        for field in required_fields:
            assert field in response_data, f"响应中缺少必要字段: {field}"
        
        # 验证报告ID
        assert response_data['report_id'] == TEST_REPORT_ID, \
            f"报告ID不匹配，预期: {TEST_REPORT_ID}, 实际: {response_data['report_id']}"
        
        # 验证报告内容
        assert response_data['content'], "报告内容为空"
        
        # 验证状态
        assert response_data['status'] == 'completed', \
            f"报告状态不正确，预期: completed, 实际: {response_data['status']}"
        
        # 记录成功信息
        logger.info("✅ 测试通过：成功获取报告内容")
        logger.info(f"报告ID: {response_data['report_id']}")
        logger.info(f"文件ID: {response_data['file_id']}")
        logger.info(f"S3路径: {response_data['s3_key']}")
        logger.info(f"报告内容长度: {len(response_data['content'])}")
        
    except requests.exceptions.Timeout:
        logger.error("请求超时")
        pytest.fail("API请求超时")
    except requests.exceptions.RequestException as e:
        logger.error(f"请求异常: {str(e)}")
        pytest.fail(f"API请求异常: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"响应解析失败: {str(e)}")
        logger.error(f"原始响应: {response.text}")
        pytest.fail(f"响应不是有效的JSON: {str(e)}")
    except AssertionError as e:
        logger.error(f"断言失败: {str(e)}")
        raise  # 重新抛出断言错误，让pytest捕获
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        pytest.fail(f"未预期的错误: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 