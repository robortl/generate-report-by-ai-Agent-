import pytest
import json
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture
def app():
    """创建测试应用实例"""
    app = create_app({'TESTING': True})
    yield app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

class TestReportAPI:
    """测试报告相关的API"""

    @patch('app.api.report.get_file_from_s3')
    @patch('app.api.report.generate_report')
    @patch('app.api.report.save_report')
    @patch('app.api.report.get_metadata_from_dynamodb')
    @patch('app.api.report.update_metadata_in_dynamodb')
    def test_create_report_success(self, mock_update_metadata, mock_get_metadata, 
                                  mock_save_report, mock_generate_report, 
                                  mock_get_file_from_s3, client):
        """测试成功生成报告"""
        # 模拟文件元数据
        mock_metadata = {
            'file_id': 'test-file-id',
            'original_filename': 'test.txt',
            'category': 'meeting',
            's3_key': 'meeting/test-file-id/test.txt',
            's3_url': 'https://test-bucket.s3.amazonaws.com/meeting/test-file-id/test.txt',
            'status': 'uploaded'
        }
        mock_get_metadata.return_value = mock_metadata
        
        # 模拟文件内容
        mock_get_file_from_s3.return_value = "This is a test file content for report generation."
        
        # 模拟报告生成
        mock_generate_report.return_value = "# Test Report\n\nThis is a generated report."
        
        # 模拟报告保存
        mock_save_report.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # 跟踪metadata状态变化
        original_metadata = mock_metadata.copy()
        processing_metadata = None
        completed_metadata = None
        
        # 修改mock_update_metadata的行为，记录每次调用时的metadata状态
        def side_effect(metadata):
            nonlocal processing_metadata, completed_metadata
            if metadata['status'] == 'processing':
                processing_metadata = metadata.copy()
            elif metadata['status'] == 'completed':
                completed_metadata = metadata.copy()
            return {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        mock_update_metadata.side_effect = side_effect
        
        # 请求数据
        data = {
            'file_id': 'test-file-id',
            'prompt': 'Generate a test report',
            'model_id': 'test-model'
        }
        
        # 发送请求
        response = client.post('/api/report/generate', 
                              data=json.dumps(data),
                              content_type='application/json')
        
        # 验证响应
        assert response.status_code == 201
        json_data = json.loads(response.data)
        assert 'report_id' in json_data
        assert json_data['message'] == 'Report generated successfully'
        
        # 验证模拟函数被调用
        mock_get_metadata.assert_called_once_with('test-file-id')
        mock_get_file_from_s3.assert_called_once_with(mock_metadata['s3_key'])
        mock_generate_report.assert_called_once()
        mock_save_report.assert_called_once()
        
        # 验证元数据更新
        assert mock_update_metadata.call_count == 2
        
        # 验证metadata状态变化
        assert processing_metadata is not None, "Processing metadata should be recorded"
        assert completed_metadata is not None, "Completed metadata should be recorded"
        assert processing_metadata['status'] == 'processing'
        assert completed_metadata['status'] == 'completed'

    def test_create_report_missing_file_id(self, client):
        """测试缺少文件ID的情况"""
        data = {
            'prompt': 'Generate a test report',
            'model_id': 'test-model'
        }
        
        response = client.post('/api/report/generate', 
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = json.loads(response.data)
        assert json_data['error'] == 'Missing file_id'

    @patch('app.api.report.get_metadata_from_dynamodb')
    def test_create_report_file_not_found(self, mock_get_metadata, client):
        """测试文件不存在的情况"""
        # 模拟文件不存在
        mock_get_metadata.return_value = None
        
        data = {
            'file_id': 'non-existent-file-id',
            'prompt': 'Generate a test report',
            'model_id': 'test-model'
        }
        
        response = client.post('/api/report/generate', 
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 404
        json_data = json.loads(response.data)
        assert json_data['error'] == 'File not found'

    @patch('app.api.report.get_report_from_dynamodb')
    def test_get_report_success(self, mock_get_report, client):
        """测试成功获取报告"""
        # 模拟报告数据
        mock_report_data = {
            'report_id': 'test-report-id',
            'file_id': 'test-file-id',
            'content': '# Test Report\n\nThis is a generated report.',
            'model_id': 'test-model',
            'prompt': 'Generate a test report',
            'created_at': '2025-03-07T12:00:00'
        }
        mock_get_report.return_value = mock_report_data
        
        # 发送请求
        response = client.get('/api/report/test-report-id')
        
        # 验证响应
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert json_data['report_id'] == 'test-report-id'
        assert json_data['content'] == '# Test Report\n\nThis is a generated report.'
        
        # 验证模拟函数被调用
        mock_get_report.assert_called_once_with('test-report-id')

    @patch('app.api.report.get_report_from_dynamodb')
    def test_get_report_not_found(self, mock_get_report, client):
        """测试报告不存在的情况"""
        # 模拟报告不存在
        mock_get_report.return_value = None
        
        # 发送请求
        response = client.get('/api/report/non-existent-report-id')
        
        # 验证响应
        assert response.status_code == 404
        json_data = json.loads(response.data)
        assert json_data['error'] == 'Report not found'

    @patch('app.api.report.get_report_from_dynamodb')
    @patch('app.api.report.update_report_in_dynamodb')
    def test_update_report_success(self, mock_update_report, mock_get_report, client):
        """测试成功更新报告"""
        # 模拟报告数据
        mock_report_data = {
            'report_id': 'test-report-id',
            'file_id': 'test-file-id',
            'content': '# Test Report\n\nThis is a generated report.',
            'model_id': 'test-model',
            'prompt': 'Generate a test report',
            'created_at': '2025-03-07T12:00:00'
        }
        mock_get_report.return_value = mock_report_data
        
        # 模拟更新成功
        mock_update_report.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # 请求数据
        data = {
            'content': '# Updated Report\n\nThis is an updated report.'
        }
        
        # 发送请求
        response = client.put('/api/report/test-report-id', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        # 验证响应
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert json_data['message'] == 'Report updated successfully'
        assert json_data['report_id'] == 'test-report-id'
        
        # 验证模拟函数被调用
        mock_get_report.assert_called_once_with('test-report-id')
        mock_update_report.assert_called_once()
        # 验证更新的内容
        assert mock_update_report.call_args[0][0]['content'] == '# Updated Report\n\nThis is an updated report.' 