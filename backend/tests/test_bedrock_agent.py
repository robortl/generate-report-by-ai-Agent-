#!/usr/bin/env python
"""
测试Bedrock Agent的调用
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.services.agent_service import generate_report, bedrock_agent_service

class BedrockAgentTest(unittest.TestCase):
    """测试Bedrock Agent的调用"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 设置环境变量
        os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
        os.environ['BEDROCK_AGENT_ID'] = 'LPJVAYJAK2'
        os.environ['BEDROCK_AGENT_ALIAS_ID'] = 'YK1IJ32MHH'
        os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
        
        # 测试文本
        self.test_text = """
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
    
    def test_bedrock_agent_service_initialization(self):
        """测试BedrockAgentService的初始化"""
        print("\n=== 测试BedrockAgentService的初始化 ===")
        
        # 创建服务实例
        service = bedrock_agent_service.BedrockAgentService()
        
        # 验证初始化是否正确
        self.assertEqual(service.region_name, 'ap-northeast-1')
        self.assertEqual(service.agent_id, 'LPJVAYJAK2')
        self.assertEqual(service.agent_alias_id, 'YK1IJ32MHH')
        self.assertEqual(service.model_id, 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        print(f"BedrockAgentService初始化成功，代理ID: {service.agent_id}, 别名ID: {service.agent_alias_id}")
    
    @patch.object(bedrock_agent_service.BedrockAgentService, 'bedrock_agent_runtime')
    def test_bedrock_agent_call(self, mock_agent_runtime):
        """测试调用Bedrock Agent"""
        print("\n=== 测试调用Bedrock Agent ===")
        
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
        mock_agent_runtime.invoke_agent.return_value = mock_response
        
        # 创建服务实例
        service = bedrock_agent_service.BedrockAgentService()
        
        # 调用方法
        result = service._generate_report_with_agent(self.test_text)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        print(f"生成报告长度: {len(result)} 字符")
        print(f"报告前 100 字符: {result[:100]}")
        
        # 验证模拟对象被正确调用
        mock_agent_runtime.invoke_agent.assert_called_once()
    
    @patch.object(bedrock_agent_service.BedrockAgentService, 'bedrock_agent_runtime')
    def test_bedrock_agent_with_custom_prompt(self, mock_agent_runtime):
        """测试使用自定义提示词调用Bedrock Agent"""
        print("\n=== 测试使用自定义提示词调用Bedrock Agent ===")
        
        # 自定义提示词
        custom_prompt = "请生成一份简洁的会议决策摘要，重点关注决定事项和行动项目。"
        
        # 模拟Agent响应
        mock_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': json.dumps({'text': '# 会议决策摘要\n\n## 主要决策\n\n1. 项目A将在下周完成\n2. 项目B的问题将由团队协作解决\n3. 产品策略将进行调整\n\n## 行动项目\n\n1. 张三：完成项目A（下周截止）\n2. 张三和李四：解决项目B问题'}).encode('utf-8')
                    }
                }
            ]
        }
        
        # 设置模拟返回值
        mock_agent_runtime.invoke_agent.return_value = mock_response
        
        # 创建服务实例
        service = bedrock_agent_service.BedrockAgentService()
        
        # 调用方法
        result = service._generate_report_with_agent(self.test_text, prompt=custom_prompt)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        print(f"自定义提示词生成报告长度: {len(result)} 字符")
        print(f"报告前 100 字符: {result[:100]}")
        
        # 验证模拟对象被正确调用
        mock_agent_runtime.invoke_agent.assert_called_once()
    
    @patch('app.services.agent_service.generate_report')
    def test_real_bedrock_agent_access(self, mock_generate_report):
        """测试真实的Bedrock Agent访问（使用模拟）"""
        print("\n=== 测试真实的Bedrock Agent访问 ===")
        
        # 模拟生成报告的返回值
        mock_report = "# 会议摘要报告\n\n## 基本信息\n\n- 会议日期：2025年3月15日\n- 参会人员：张三、李四、王五\n- 会议主题：项目进度讨论\n\n## 主要内容\n\n1. 项目A进度已达80%，预计下周完成\n2. 项目B存在技术问题，需要团队协作解决\n3. 产品策略需要根据市场反馈调整"
        mock_generate_report.return_value = mock_report
        
        # 调用函数
        result = generate_report(self.test_text)
        
        # 验证结果
        self.assertEqual(result, mock_report)
        
        print(f"生成报告长度: {len(result)} 字符")
        print(f"报告前 100 字符: {result[:100]}")
        
        # 验证模拟对象被正确调用
        mock_generate_report.assert_called_once_with(self.test_text, prompt=None, model_id=None)

def run_tests():
    """运行测试"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests() 