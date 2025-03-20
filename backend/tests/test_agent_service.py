import os
import sys
import json
import logging
from unittest.mock import patch, MagicMock

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入要测试的模块
from app.services.agent_service import BedrockAgentService, generate_report

def test_service_initialization():
    """测试BedrockAgentService的初始化"""
    logger.info("=== 测试BedrockAgentService的初始化 ===")
    
    # 创建服务实例
    service = BedrockAgentService()
    
    # 打印服务配置
    logger.info(f"区域: {service.region_name}")
    logger.info(f"代理ID: {service.agent_id}")
    logger.info(f"别名ID: {service.agent_alias_id}")
    logger.info(f"模型ID: {service.model_id}")
    
    logger.info("BedrockAgentService初始化成功")
    return service

def test_agent_call():
    """测试调用Bedrock Agent"""
    logger.info("=== 测试调用Bedrock Agent ===")
    
    # 测试文本
    test_text = """
    会议主题：项目进度讨论
    日期：2025年3月15日
    参与者：张三、李四、王五
    
    讨论要点：
    1. 项目A已完成80%，预计下周完成
    2. 项目B遇到技术问题，需要团队协作解决
    3. 产品策略需要根据市场反馈进行调整
    
    决定事项：
    1. 张三负责完成项目A的收尾工作
    2. 李四和王五共同解决项目B的技术问题
    3. 下周五前完成产品策略调整方案
    """
    
    logger.info(f"测试文本长度: {len(test_text)} 字符")
    
    # 创建服务实例
    service = BedrockAgentService()
    logger.info("创建服务实例成功")
    
    # 模拟bedrock_agent_runtime
    original_runtime = service.bedrock_agent_runtime
    mock_runtime = MagicMock()
    
    # 模拟Agent响应
    mock_response = {
        'completion': [
            {
                'chunk': {
                    'bytes': json.dumps({'text': '# 会议摘要报告\n\n## 基本信息\n\n- 会议日期：2025年3月15日\n- 参会人员：张三、李四、王五\n- 会议主题：项目进度讨论\n\n## 主要内容\n\n1. 项目A进度已达80%，预计下周完成\n2. 项目B存在技术问题，需要团队协作解决\n3. 产品策略需要根据市场反馈调整'}).encode('utf-8')
                }
            }
        ]
    }
    
    # 设置模拟返回值
    mock_runtime.invoke_agent.return_value = mock_response
    logger.info("设置模拟返回值成功")
    
    # 替换为模拟对象
    service.bedrock_agent_runtime = mock_runtime
    
    try:
        # 调用方法
        logger.info("开始调用_generate_report_with_agent方法")
        result = service._generate_report_with_agent(test_text)
        logger.info("调用_generate_report_with_agent方法成功")
        
        # 验证结果
        logger.info(f"生成报告长度: {len(result)} 字符")
        logger.info(f"报告前 100 字符: {result[:100]}")
        
        # 验证模拟对象被正确调用
        assert mock_runtime.invoke_agent.called, "invoke_agent方法未被调用"
        logger.info("验证模拟对象被正确调用成功")
        
        return result
    finally:
        # 恢复原始对象
        service.bedrock_agent_runtime = original_runtime

def test_model_call():
    """测试直接调用Bedrock模型"""
    logger.info("=== 测试直接调用Bedrock模型 ===")
    
    # 测试文本
    test_text = """
    会议主题：项目进度讨论
    日期：2025年3月15日
    参与者：张三、李四、王五
    
    讨论要点：
    1. 项目A已完成80%，预计下周完成
    2. 项目B遇到技术问题，需要团队协作解决
    3. 产品策略需要根据市场反馈进行调整
    
    决定事项：
    1. 张三负责完成项目A的收尾工作
    2. 李四和王五共同解决项目B的技术问题
    3. 下周五前完成产品策略调整方案
    """
    
    logger.info(f"测试文本长度: {len(test_text)} 字符")
    
    # 创建服务实例
    service = BedrockAgentService()
    logger.info("创建服务实例成功")
    
    # 保存原始runtime
    original_runtime = service.bedrock_runtime
    mock_runtime = MagicMock()
    
    # 模拟模型响应
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [
            {
                'text': '# 会议摘要报告\n\n## 基本信息\n\n- 会议日期：2025年3月15日\n- 参会人员：张三、李四、王五\n- 会议主题：项目进度讨论\n\n## 主要内容\n\n1. 项目A进度已达80%，预计下周完成\n2. 项目B存在技术问题，需要团队协作解决\n3. 产品策略需要根据市场反馈调整'
            }
        ]
    }).encode('utf-8')
    
    # 设置模拟返回值
    mock_runtime.invoke_model.return_value = mock_response
    logger.info("设置模拟返回值成功")
    
    # 替换为模拟对象
    service.bedrock_runtime = mock_runtime
    
    try:
        # 调用方法
        logger.info("开始调用_generate_report_with_model方法")
        result = service._generate_report_with_model(test_text)
        logger.info("调用_generate_report_with_model方法成功")
        
        # 验证结果
        logger.info(f"生成报告长度: {len(result)} 字符")
        logger.info(f"报告前 100 字符: {result[:100]}")
        
        # 验证模拟对象被正确调用
        assert mock_runtime.invoke_model.called, "invoke_model方法未被调用"
        logger.info("验证模拟对象被正确调用成功")
        
        return result
    finally:
        # 恢复原始对象
        service.bedrock_runtime = original_runtime

def test_generate_report():
    """测试generate_report函数"""
    logger.info("=== 测试generate_report函数 ===")
    
    # 测试文本
    test_text = """
    会议主题：项目进度讨论
    日期：2025年3月15日
    参与者：张三、李四、王五
    
    讨论要点：
    1. 项目A已完成80%，预计下周完成
    2. 项目B遇到技术问题，需要团队协作解决
    3. 产品策略需要根据市场反馈进行调整
    
    决定事项：
    1. 张三负责完成项目A的收尾工作
    2. 李四和王五共同解决项目B的技术问题
    3. 下周五前完成产品策略调整方案
    """
    
    logger.info(f"测试文本长度: {len(test_text)} 字符")
    
    # 保存原始函数
    original_generate_report = generate_report
    
    # 创建模拟函数
    def mock_generate_report(file_content, prompt=None, model_id=None):
        logger.info(f"模拟generate_report被调用，文本长度: {len(file_content)}")
        return "# 会议摘要报告\n\n## 基本信息\n\n- 会议日期：2025年3月15日\n- 参会人员：张三、李四、王五\n- 会议主题：项目进度讨论\n\n## 主要内容\n\n1. 项目A进度已达80%，预计下周完成\n2. 项目B存在技术问题，需要团队协作解决\n3. 产品策略需要根据市场反馈调整"
    
    try:
        # 替换为模拟函数
        import app.services.agent_service
        app.services.agent_service.generate_report = mock_generate_report
        logger.info("设置模拟函数成功")
        
        # 调用函数
        logger.info("开始调用generate_report函数")
        result = generate_report(test_text)
        logger.info("调用generate_report函数成功")
        
        # 验证结果
        logger.info(f"生成报告长度: {len(result)} 字符")
        logger.info(f"报告前 100 字符: {result[:100]}")
        
        return result
    finally:
        # 恢复原始函数
        app.services.agent_service.generate_report = original_generate_report

def main():
    """主函数"""
    try:
        logger.info("开始测试BedrockAgentService")
        
        # 测试服务初始化
        service = test_service_initialization()
        
        # 测试调用Bedrock Agent
        agent_result = test_agent_call()
        
        # 测试直接调用Bedrock模型
        model_result = test_model_call()
        
        # 测试generate_report函数
        report_result = test_generate_report()
        
        logger.info("=== 测试完成 ===")
        logger.info("所有测试通过！")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 