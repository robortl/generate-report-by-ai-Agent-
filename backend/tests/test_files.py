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

class TestFilesAPI:
    """测试文件列表相关的API"""

    @patch('app.api.files.list_files_from_dynamodb')
    def test_get_files_success(self, mock_list_files, client):
        """测试成功获取文件列表"""
        # 模拟 DynamoDB 返回数据
        mock_data = {
            'items': [
                {
                    'file_id': 'test-file-id-1',
                    'original_filename': 'test1.txt',
                    'category': 'meeting',
                    's3_key': 'meeting/test-file-id-1/test1.txt',
                    's3_url': 'https://test-bucket.s3.amazonaws.com/meeting/test-file-id-1/test1.txt',
                    'status': 'uploaded',
                    'upload_time': '2025-03-07T12:00:00',
                    'created_at': '2025-03-07T12:00:00'
                },
                {
                    'file_id': 'test-file-id-2',
                    'original_filename': 'test2.txt',
                    'category': 'report',
                    's3_key': 'report/test-file-id-2/test2.txt',
                    's3_url': 'https://test-bucket.s3.amazonaws.com/report/test-file-id-2/test2.txt',
                    'status': 'uploaded',
                    'upload_time': '2025-03-07T13:00:00',
                    'created_at': '2025-03-07T13:00:00'
                }
            ],
            'last_evaluated_key': None
        }
        mock_list_files.return_value = mock_data
        
        # 发送请求
        response = client.get('/api/files?limit=10')
        
        # 验证响应
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert 'items' in json_data
        assert len(json_data['items']) == 2
        assert json_data['items'][0]['file_id'] == 'test-file-id-1'
        assert json_data['items'][1]['file_id'] == 'test-file-id-2'
        
        # 验证模拟函数被调用
        mock_list_files.assert_called_once_with(None, 10, None)

    @patch('app.api.files.list_files_from_dynamodb')
    def test_get_files_with_category(self, mock_list_files, client):
        """测试按分类获取文件列表"""
        # 模拟 DynamoDB 返回数据
        mock_data = {
            'items': [
                {
                    'file_id': 'test-file-id-1',
                    'original_filename': 'test1.txt',
                    'category': 'meeting',
                    's3_key': 'meeting/test-file-id-1/test1.txt',
                    's3_url': 'https://test-bucket.s3.amazonaws.com/meeting/test-file-id-1/test1.txt',
                    'status': 'uploaded',
                    'upload_time': '2025-03-07T12:00:00',
                    'created_at': '2025-03-07T12:00:00'
                }
            ],
            'last_evaluated_key': None
        }
        mock_list_files.return_value = mock_data
        
        # 发送请求
        response = client.get('/api/files?category=meeting&limit=5')
        
        # 验证响应
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert 'items' in json_data
        assert len(json_data['items']) == 1
        assert json_data['items'][0]['category'] == 'meeting'
        
        # 验证模拟函数被调用
        mock_list_files.assert_called_once_with('meeting', 5, None)

    @patch('app.api.files.list_files_from_dynamodb')
    def test_get_files_with_pagination(self, mock_list_files, client):
        """测试分页获取文件列表"""
        # 模拟 DynamoDB 返回数据
        mock_data = {
            'items': [
                {
                    'file_id': 'test-file-id-3',
                    'original_filename': 'test3.txt',
                    'category': 'general',
                    's3_key': 'general/test-file-id-3/test3.txt',
                    's3_url': 'https://test-bucket.s3.amazonaws.com/general/test-file-id-3/test3.txt',
                    'status': 'uploaded',
                    'upload_time': '2025-03-07T14:00:00',
                    'created_at': '2025-03-07T14:00:00'
                }
            ],
            'last_evaluated_key': 'test-file-id-3'
        }
        mock_list_files.return_value = mock_data
        
        # 发送请求
        response = client.get('/api/files?limit=1&last_key=test-file-id-2')
        
        # 验证响应
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert 'items' in json_data
        assert len(json_data['items']) == 1
        assert json_data['last_evaluated_key'] == 'test-file-id-3'
        
        # 验证模拟函数被调用
        mock_list_files.assert_called_once_with(None, 1, 'test-file-id-2')

    @patch('app.api.files.list_files_from_dynamodb')
    def test_get_files_error_handling(self, mock_list_files, client):
        """测试错误处理"""
        # 模拟 DynamoDB 抛出异常
        mock_list_files.side_effect = Exception("DynamoDB connection error")
        
        # 发送请求
        response = client.get('/api/files')
        
        # 验证响应 - 应该返回模拟数据而不是错误
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert 'items' in json_data
        assert len(json_data['items']) == 1  # 模拟数据中有一个样本文件 