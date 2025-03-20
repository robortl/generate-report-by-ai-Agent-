#!/usr/bin/env python
"""
报告生成功能测试 - 测试通过Bedrock Agent生成报告的功能
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 导入需要测试的模块
from app.services.agent_service import generate_report
from app.services.storage import get_file_content_by_id

class ReportGenerationTest(unittest.TestCase):
    """报告生成功能测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 测试文件路径
        self.test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'meeting_minutes_test.txt')
        
        # 如果测试文件不存在，则创建一个测试文件
        if not os.path.exists(self.test_file_path):
            with open(self.test_file_path, 'w', encoding='utf-8') as f:
                f.write("这是一个测试会议记录文件，用于测试报告生成功能。\n")
                f.write("会议日期：2025年3月15日\n")
                f.write("参会人员：张三、李四、王五\n")
                f.write("会议主题：项目进度讨论\n")
                f.write("会议内容：\n")
                f.write("1. 张三汇报了项目A的进度，目前已完成80%。\n")
                f.write("2. 李四提出了项目B的几个问题，需要团队协作解决。\n")
                f.write("3. 王五分享了市场调研结果，建议调整产品策略。\n")
                f.write("会议结论：\n")
                f.write("1. 项目A将在下周完成。\n")
                f.write("2. 项目B的问题将由张三和李四共同解决。\n")
                f.write("3. 产品策略调整方案将在下次会议讨论。\n")
        
        # 读取测试文件内容
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            self.test_content = f.read()
    
    @patch('app.services.agent_service.bedrock_agent_runtime')
    def test_agent_report_generation(self, mock_bedrock_agent_runtime):
        """测试通过Bedrock Agent生成报告"""
        print("\n=== 测试通过Bedrock Agent生成报告 ===")
        
        # 模拟Bedrock Agent的响应
        mock_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': json.dumps({'text': '# 会议摘要报告\n\n## 基本信息\n\n- 会议日期：2025年3月15日\n- 参会人员：张三、李四、王五\n- 会议主题：项目进度讨论\n\n## 主要内容\n\n1. 项目A进度已达80%，预计下周完成\n2. 项目B存在问题，需要团队协作解决\n3. 市场调研结果表明需要调整产品策略\n\n## 行动项目\n\n1. 张三负责完成项目A\n2. 张三和李四共同解决项目B的问题\n3. 下次会议讨论产品策略调整方案'}).encode('utf-8')
                    }
                }
            ],
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        # 配置模拟对象的行为
        mock_bedrock_agent_runtime.invoke_agent.return_value = mock_response
        
        # 调用被测试的函数
        report = generate_report(self.test_content)
        
        # 验证Bedrock Agent是否被正确调用
        mock_bedrock_agent_runtime.invoke_agent.assert_called_once()
        
        # 验证调用参数
        call_args = mock_bedrock_agent_runtime.invoke_agent.call_args[1]
        self.assertIn('inputText', call_args)
        self.assertIn(self.test_content, call_args['inputText'])
        
        # 验证报告内容
        self.assertIsNotNone(report)
        self.assertIsInstance(report, str)
        self.assertIn('会议摘要报告', report)
        self.assertIn('基本信息', report)
        self.assertIn('主要内容', report)
        self.assertIn('行动项目', report)
        
        print(f"生成报告长度: {len(report)} 字符")
        print(f"报告前 100 字符: {report[:100]}...")
    
    @patch('app.services.agent_service.bedrock_agent_runtime')
    def test_agent_custom_prompt_report(self, mock_bedrock_agent_runtime):
        """测试使用自定义提示词通过Bedrock Agent生成报告"""
        print("\n=== 测试使用自定义提示词通过Bedrock Agent生成报告 ===")
        
        # 自定义提示词
        custom_prompt = """
        请根据以下会议记录生成一份简洁的摘要报告，重点关注：
        1. 会议的主要决策
        2. 分配的行动项目和负责人
        3. 关键的讨论点
        
        请使用简洁明了的语言，并按重要性排序。
        """
        
        # 模拟Bedrock Agent的响应
        mock_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': json.dumps({'text': '# 会议决策摘要\n\n## 主要决策\n\n1. 项目A将在下周完成\n2. 项目B的问题将由团队协作解决\n3. 产品策略将进行调整\n\n## 行动项目\n\n1. 张三：完成项目A（下周截止）\n2. 张三和李四：共同解决项目B问题\n3. 全体：准备产品策略调整方案\n\n## 关键讨论点\n\n1. 项目A已完成80%\n2. 项目B存在需要协作解决的问题\n3. 市场调研结果表明需要调整产品策略'}).encode('utf-8')
                    }
                }
            ],
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        # 配置模拟对象的行为
        mock_bedrock_agent_runtime.invoke_agent.return_value = mock_response
        
        # 调用被测试的函数
        report = generate_report(self.test_content, prompt=custom_prompt)
        
        # 验证Bedrock Agent是否被正确调用
        mock_bedrock_agent_runtime.invoke_agent.assert_called_once()
        
        # 验证调用参数
        call_args = mock_bedrock_agent_runtime.invoke_agent.call_args[1]
        self.assertIn('inputText', call_args)
        self.assertIn(self.test_content, call_args['inputText'])
        self.assertIn(custom_prompt, call_args['inputText'])
        
        # 验证报告内容
        self.assertIsNotNone(report)
        self.assertIsInstance(report, str)
        self.assertIn('会议决策摘要', report)
        self.assertIn('主要决策', report)
        self.assertIn('行动项目', report)
        self.assertIn('关键讨论点', report)
        
        print(f"自定义提示词生成报告长度: {len(report)} 字符")
        print(f"报告前 100 字符: {report[:100]}...")
    
    @patch('app.services.agent_service.bedrock_agent_runtime')
    def test_agent_error_handling(self, mock_bedrock_agent_runtime):
        """测试Bedrock Agent错误处理"""
        print("\n=== 测试Bedrock Agent错误处理 ===")
        
        # 模拟Bedrock Agent抛出异常
        mock_bedrock_agent_runtime.invoke_agent.side_effect = Exception("模拟的Bedrock Agent错误")
        
        # 调用被测试的函数并验证异常处理
        with self.assertRaises(Exception) as context:
            generate_report(self.test_content)
        
        # 验证异常信息
        self.assertIn("Failed to generate report using Bedrock Agent", str(context.exception))
        
        # 验证Bedrock Agent是否被调用
        mock_bedrock_agent_runtime.invoke_agent.assert_called_once()
        
        print(f"错误处理测试通过: {str(context.exception)}")

def run_tests():
    """运行功能测试"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests()

 