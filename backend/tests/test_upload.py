import pytest
import json
import os
import io
from unittest.mock import patch, MagicMock
from app import create_app
from app.services.storage import upload_file_to_s3, save_metadata_to_dynamodb

@pytest.fixture
def app():
    """创建测试应用实例"""
    app = create_app({'TESTING': True})
    yield app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

class TestUploadAPI:
    """测试上传相关的API"""

    def test_allowed_file(self, app):
        """测试文件类型检查功能"""
        with app.app_context():
            from app.api.upload import allowed_file
            
            # 测试允许的文件类型
            assert allowed_file('test.txt') == True
            assert allowed_file('test.pdf') == True
            assert allowed_file('test.doc') == True
            assert allowed_file('test.docx') == True
            assert allowed_file('test.md') == True
            
            # 测试不允许的文件类型
            assert allowed_file('test.exe') == False
            assert allowed_file('test.js') == False
            assert allowed_file('test') == False

    @patch('app.api.upload.upload_file_to_s3')
    @patch('app.api.upload.save_metadata_to_dynamodb')
    def test_upload_file_success(self, mock_save_metadata, mock_upload, client):
        """测试文件上传成功的情况"""
        # 模拟S3上传返回URL
        mock_upload.return_value = 'https://test-bucket.s3.amazonaws.com/test/file.txt'
        mock_save_metadata.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # 创建测试文件
        data = dict(
            file=(io.BytesIO(b'This is a test file content'), 'test.txt'),
            category='meeting'
        )
        
        # 发送请求
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        
        # 验证响应
        assert response.status_code == 201
        json_data = json.loads(response.data)
        assert 'file_id' in json_data
        assert 's3_url' in json_data
        assert json_data['message'] == 'File uploaded successfully'
        
        # 验证模拟函数被调用
        mock_upload.assert_called_once()
        mock_save_metadata.assert_called_once()

    def test_upload_file_no_file(self, client):
        """测试没有文件的情况"""
        response = client.post('/api/upload', data={}, content_type='multipart/form-data')
        assert response.status_code == 400
        json_data = json.loads(response.data)
        assert json_data['error'] == 'No file part'

    def test_upload_file_empty_filename(self, client):
        """测试空文件名的情况"""
        data = dict(
            file=(io.BytesIO(b''), ''),
            category='meeting'
        )
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        json_data = json.loads(response.data)
        assert json_data['error'] == 'No selected file'

    def test_upload_file_invalid_type(self, client):
        """测试不允许的文件类型"""
        data = dict(
            file=(io.BytesIO(b'Test content'), 'test.exe'),
            category='meeting'
        )
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        json_data = json.loads(response.data)
        assert 'File type not allowed' in json_data['error']

    def test_get_categories(self, client):
        """测试获取分类列表"""
        response = client.get('/api/upload/categories')
        assert response.status_code == 200
        categories = json.loads(response.data)
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert all('id' in category and 'name' in category for category in categories) 