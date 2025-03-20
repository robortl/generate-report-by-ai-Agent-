#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试get_metadata_from_dynamodb函数
"""

import os
import sys
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加应用程序目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试文件ID
TEST_FILE_ID = "36f4fc32-122a-475c-803d-ee3e183e9c5d"

def test_get_metadata_function():
    """测试get_metadata_from_dynamodb函数"""
    logger.info(f"=== 测试get_metadata_from_dynamodb函数 ===")
    logger.info(f"测试文件ID: {TEST_FILE_ID}")
    
    try:
        # 直接导入函数
        from app.services.storage import get_metadata_from_dynamodb
        
        # 打印函数源代码
        import inspect
        logger.info(f"函数源代码:\n{inspect.getsource(get_metadata_from_dynamodb)}")
        
        # 检查环境变量
        logger.info(f"环境变量:")
        logger.info(f"USE_LOCAL_MOCK: {os.environ.get('USE_LOCAL_MOCK')}")
        logger.info(f"DYNAMODB_TABLE: {os.environ.get('DYNAMODB_TABLE')}")
        logger.info(f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION')}")
        
        # 设置环境变量
        os.environ['USE_LOCAL_MOCK'] = 'false'
        logger.info(f"设置USE_LOCAL_MOCK为false")
        
        # 调用函数
        logger.info(f"调用get_metadata_from_dynamodb({TEST_FILE_ID})")
        result = get_metadata_from_dynamodb(TEST_FILE_ID)
        
        # 打印结果
        logger.info(f"函数返回结果: {result}")
        if result:
            logger.info(f"结果类型: {type(result)}")
            logger.info(f"结果内容:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            logger.warning(f"函数返回空结果")
        
        # 检查函数是否使用了模拟数据
        logger.info(f"检查是否使用了模拟数据...")
        
        # 再次调用函数，但使用一个不存在的ID
        fake_id = "non-existent-id"
        logger.info(f"调用get_metadata_from_dynamodb({fake_id})")
        fake_result = get_metadata_from_dynamodb(fake_id)
        
        logger.info(f"函数返回结果: {fake_result}")
        if fake_result:
            logger.info(f"结果类型: {type(fake_result)}")
            logger.info(f"结果内容:\n{json.dumps(fake_result, indent=2, ensure_ascii=False)}")
            logger.warning(f"函数可能使用了模拟数据，因为不存在的ID也返回了结果")
        else:
            logger.info(f"函数返回空结果，这是正确的行为")
        
        return True
    except Exception as e:
        logger.error(f"测试get_metadata_from_dynamodb函数时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    try:
        test_get_metadata_function()
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 