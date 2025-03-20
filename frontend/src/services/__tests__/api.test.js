import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import * as api from '../api';

// 创建 axios 模拟适配器
const mock = new MockAdapter(axios);

describe('API Service Tests', () => {
  // 每个测试后重置模拟
  afterEach(() => {
    mock.reset();
  });

  // 测试获取分类
  test('getCategories should fetch categories correctly', async () => {
    const mockCategories = [
      { id: 'meeting', name: '会议记录' },
      { id: 'report', name: '业务报告' }
    ];
    
    // 模拟 API 响应
    mock.onGet('/api/upload/categories').reply(200, mockCategories);
    
    // 调用 API 方法
    const result = await api.getCategories();
    
    // 验证结果
    expect(result).toEqual(mockCategories);
  });

  // 测试上传文件
  test('uploadFile should upload file correctly', async () => {
    const mockResponse = {
      message: 'File uploaded successfully',
      file_id: 'test-file-id',
      s3_url: 'https://test-bucket.s3.amazonaws.com/test/file.txt'
    };
    
    // 模拟 API 响应
    mock.onPost('/api/upload').reply(201, mockResponse);
    
    // 创建测试文件和分类
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const category = 'meeting';
    
    // 调用 API 方法
    const result = await api.uploadFile(file, category);
    
    // 验证结果
    expect(result).toEqual(mockResponse);
  });

  // 测试生成报告
  test('generateReport should generate report correctly', async () => {
    const mockResponse = {
      message: 'Report generated successfully',
      report_id: 'test-report-id'
    };
    
    // 模拟 API 响应
    mock.onPost('/api/report/generate').reply(201, mockResponse);
    
    // 创建请求参数
    const fileId = 'test-file-id';
    const prompt = 'Generate a test report';
    const modelId = 'test-model';
    
    // 调用 API 方法
    const result = await api.generateReport(fileId, prompt, modelId);
    
    // 验证结果
    expect(result).toEqual(mockResponse);
    
    // 验证请求体
    expect(mock.history.post[0].data).toEqual(JSON.stringify({
      file_id: fileId,
      prompt: prompt,
      model_id: modelId
    }));
  });

  // 测试获取报告
  test('getReport should fetch report correctly', async () => {
    const mockReport = {
      report_id: 'test-report-id',
      file_id: 'test-file-id',
      content: '# Test Report\n\nThis is a generated report.',
      model_id: 'test-model',
      prompt: 'Generate a test report',
      created_at: '2025-03-07T12:00:00'
    };
    
    // 模拟 API 响应
    mock.onGet('/api/report/test-report-id').reply(200, mockReport);
    
    // 调用 API 方法
    const result = await api.getReport('test-report-id');
    
    // 验证结果
    expect(result).toEqual(mockReport);
  });

  // 测试更新报告
  test('updateReport should update report correctly', async () => {
    const mockResponse = {
      message: 'Report updated successfully',
      report_id: 'test-report-id'
    };
    
    // 模拟 API 响应
    mock.onPut('/api/report/test-report-id').reply(200, mockResponse);
    
    // 创建请求参数
    const reportId = 'test-report-id';
    const content = '# Updated Report\n\nThis is an updated report.';
    
    // 调用 API 方法
    const result = await api.updateReport(reportId, content);
    
    // 验证结果
    expect(result).toEqual(mockResponse);
    
    // 验证请求体
    expect(mock.history.put[0].data).toEqual(JSON.stringify({
      content: content
    }));
  });

  // 测试获取文件列表
  test('getFiles should fetch files correctly', async () => {
    const mockFiles = {
      items: [
        {
          file_id: 'test-file-id-1',
          original_filename: 'test1.txt',
          category: 'meeting',
          s3_key: 'meeting/test-file-id-1/test1.txt',
          s3_url: 'https://test-bucket.s3.amazonaws.com/meeting/test-file-id-1/test1.txt',
          status: 'uploaded',
          upload_time: '2025-03-07T12:00:00',
          created_at: '2025-03-07T12:00:00'
        }
      ],
      last_evaluated_key: null
    };
    
    // 模拟 API 响应
    mock.onGet('/api/files').reply(config => {
      // 验证查询参数
      expect(config.params).toEqual({
        category: 'meeting',
        limit: 10
      });
      
      return [200, mockFiles];
    });
    
    // 调用 API 方法
    const result = await api.getFiles('meeting', 10);
    
    // 验证结果
    expect(result).toEqual(mockFiles);
  });

  // 测试错误处理
  test('API should handle errors correctly', async () => {
    // 模拟 API 错误响应
    mock.onGet('/api/upload/categories').reply(500, { error: 'Internal Server Error' });
    
    // 调用 API 方法并捕获异常
    await expect(api.getCategories()).rejects.toThrow();
  });
}); 