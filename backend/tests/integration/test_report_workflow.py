#!/usr/bin/env python
"""
报告工作流集成测试 - 测试报告更新和重新生成功能
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import uuid

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app import create_app
from app.services.storage import save_metadata_to_dynamodb, upload_file_to_s3

class ReportWorkflowTest(unittest.TestCase):
    """报告工作流集成测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试应用
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
        
        # 创建测试文件
        self.test_content = """这是一个测试会议记录文件，用于测试报告生成功能。
会议日期：2025年3月15日
参会人员：张三、李四、王五
会议主题：项目进度讨论
会议内容：
1. 张三汇报了项目A的进度，目前已完成80%。
2. 李四提出了项目B的几个问题，需要团队协作解决。
3. 王五分享了市场调研结果，建议调整产品策略。
会议结论：
1. 项目A将在下周完成。
2. 项目B的问题将由张三和李四共同解决。
3. 产品策略调整方案将在下次会议讨论。
"""
        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        self.temp_file.write(self.test_content.encode('utf-8'))
        self.temp_file.close()
        
        # 模拟文件上传
        self.file_id = str(uuid.uuid4())
        self.s3_key = f"meeting/{self.file_id}/test_meeting.txt"
        
        # 设置模拟数据
        self.report_id = None
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时文件
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    @patch('app.api.report.generate_report')
    @patch('app.api.report.get_file_content_by_id')
    @patch('app.api.report.get_metadata_from_dynamodb')
    def test_report_update_and_regenerate(self, mock_get_metadata, mock_get_file_content, mock_generate_report):
        """测试报告更新和重新生成功能"""
        print("\n=== 测试报告更新和重新生成功能 ===")
        
        # 1. 模拟文件元数据
        mock_metadata = {
            'file_id': self.file_id,
            'original_filename': 'test_meeting.txt',
            'category': 'meeting',
            's3_key': self.s3_key,
            's3_url': f"https://test-bucket.s3.amazonaws.com/{self.s3_key}",
            'status': 'uploaded'
        }
        mock_get_metadata.return_value = mock_metadata
        
        # 2. 模拟文件内容
        mock_get_file_content.return_value = self.test_content
        
        # 3. 模拟报告生成
        mock_generate_report.return_value = "# 测试报告\n\n这是一个通过Bedrock Agent生成的测试报告。"
        
        # 4. 创建报告
        print("步骤1: 创建报告")
        response = self.client.post(
            '/api/report/generate',
            data=json.dumps({'file_id': self.file_id}),
            content_type='application/json'
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('report_id', data)
        self.assertEqual(data['message'], 'Report generated successfully')
        
        # 保存报告ID
        self.report_id = data['report_id']
        print(f"报告ID: {self.report_id}")
        
        # 5. 获取报告
        print("\n步骤2: 获取报告")
        with patch('app.api.report.get_report_from_dynamodb') as mock_get_report:
            # 模拟报告数据
            mock_report = {
                'report_id': self.report_id,
                'file_id': self.file_id,
                'content': "# 测试报告\n\n这是一个通过Bedrock Agent生成的测试报告。",
                'status': 'completed',
                's3_key': f"reports/{self.report_id}.txt",
                's3_url': f"https://test-bucket.s3.amazonaws.com/reports/{self.report_id}.txt"
            }
            mock_get_report.return_value = mock_report
            
            response = self.client.get(f'/api/report/{self.report_id}')
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['report_id'], self.report_id)
            self.assertEqual(data['content'], "# 测试报告\n\n这是一个通过Bedrock Agent生成的测试报告。")
            print(f"报告内容: {data['content'][:50]}...")
        
        # 6. 更新报告
        print("\n步骤3: 更新报告")
        with patch('app.api.report.get_report_from_dynamodb') as mock_get_report, \
             patch('app.api.report.update_report_in_dynamodb') as mock_update_report:
            # 模拟报告数据
            mock_report = {
                'report_id': self.report_id,
                'file_id': self.file_id,
                'content': "# 测试报告\n\n这是一个通过Bedrock Agent生成的测试报告。",
                'status': 'completed',
                's3_key': f"reports/{self.report_id}.txt",
                's3_url': f"https://test-bucket.s3.amazonaws.com/reports/{self.report_id}.txt"
            }
            mock_get_report.return_value = mock_report
            
            # 模拟更新成功
            mock_update_report.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
            
            # 更新报告内容
            updated_content = "# 更新后的报告\n\n这是手动更新的报告内容。"
            response = self.client.put(
                f'/api/report/{self.report_id}',
                data=json.dumps({'content': updated_content}),
                content_type='application/json'
            )
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Report updated successfully')
            self.assertEqual(data['report_id'], self.report_id)
            
            # 验证更新调用
            mock_update_report.assert_called_once()
            update_args = mock_update_report.call_args[0][0]
            self.assertEqual(update_args['content'], updated_content)
            self.assertEqual(update_args['status'], 'updated')
            print(f"更新后的报告状态: {update_args['status']}")
        
        # 7. 重新生成报告
        print("\n步骤4: 重新生成报告")
        with patch('app.api.report.get_report_from_dynamodb') as mock_get_report, \
             patch('app.api.report.update_report_in_dynamodb') as mock_update_report:
            # 模拟报告数据
            mock_report = {
                'report_id': self.report_id,
                'file_id': self.file_id,
                'content': "# 更新后的报告\n\n这是手动更新的报告内容。",
                'status': 'updated',
                's3_key': f"reports/{self.report_id}.txt",
                's3_url': f"https://test-bucket.s3.amazonaws.com/reports/{self.report_id}.txt"
            }
            mock_get_report.return_value = mock_report
            
            # 模拟更新成功
            mock_update_report.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
            
            # 模拟重新生成的报告内容
            mock_generate_report.return_value = "# 重新生成的报告\n\n这是通过Bedrock Agent重新生成的报告内容。"
            
            # 重新生成报告
            response = self.client.post(
                f'/api/report/{self.report_id}/regenerate',
                data=json.dumps({'prompt': '请重新生成一份更详细的报告'}),
                content_type='application/json'
            )
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Report regenerated successfully')
            self.assertEqual(data['report_id'], self.report_id)
            
            # 验证更新调用
            self.assertEqual(mock_update_report.call_count, 2)
            
            # 验证第一次调用（状态更新为processing）
            first_call_args = mock_update_report.call_args_list[0][0][0]
            self.assertEqual(first_call_args['status'], 'processing')
            
            # 验证第二次调用（更新报告内容和状态）
            second_call_args = mock_update_report.call_args_list[1][0][0]
            self.assertEqual(second_call_args['content'], "# 重新生成的报告\n\n这是通过Bedrock Agent重新生成的报告内容。")
            self.assertEqual(second_call_args['status'], 'completed')
            print(f"重新生成后的报告状态: {second_call_args['status']}")
            
            # 验证generate_report调用
            mock_generate_report.assert_called_with(
                self.test_content,
                prompt='请重新生成一份更详细的报告',
                model_id=None
            )
        
        print("\n测试完成: 报告更新和重新生成功能测试通过")

def run_tests():
    """运行集成测试"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests() 