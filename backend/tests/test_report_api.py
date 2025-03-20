import boto3
import pytest

def test_generate_report():
    """测试报告生成API"""
    # 创建测试文件
    file_id, file_metadata = create_test_file()
    
    # 准备请求数据
    data = {
        'file_id': file_id,
        'prompt': 'Generate a summary of the meeting',
        'model_id': 'anthropic.claude-v2'
    }
    
    # 发送请求
    response = client.post('/api/report/generate', json=data)
    assert response.status_code == 201
    
    # 验证响应
    response_data = response.get_json()
    assert 'report_id' in response_data
    assert 'status' in response_data
    assert response_data['status'] == 'completed'
    
    # 获取报告ID
    report_id = response_data['report_id']
    
    # 验证报告是否保存到DynamoDB
    report = get_report_from_dynamodb(report_id)
    assert report is not None
    assert report['report_id'] == report_id
    assert report['file_id'] == file_id
    assert report['status'] == 'completed'
    assert 'content' in report
    assert 's3_key' in report
    assert 's3_url' in report
    
    # 验证报告是否保存到S3
    s3_client = boto3.client('s3')
    try:
        s3_response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=report['s3_key']
        )
        s3_content = s3_response['Body'].read().decode('utf-8')
        assert s3_content == report['content']
    except Exception as e:
        pytest.fail(f"Failed to get report from S3: {str(e)}")
    
    # 验证文件元数据是否更新
    updated_metadata = get_metadata_from_dynamodb(file_id)
    assert updated_metadata is not None
    assert updated_metadata['report_id'] == report_id
    assert updated_metadata['status'] == 'processed' 