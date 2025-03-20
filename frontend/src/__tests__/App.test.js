import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';
import * as api from '../services/api';

// 模拟 API 服务
jest.mock('../services/api');

describe('App Integration Tests', () => {
  // 每个测试前重置模拟
  beforeEach(() => {
    jest.clearAllMocks();
    
    // 模拟常用 API 响应
    api.getCategories.mockResolvedValue([
      { id: 'meeting', name: '会议记录' },
      { id: 'report', name: '业务报告' }
    ]);
    
    api.getFiles.mockResolvedValue({
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
    });
  });

  test('renders home page correctly', async () => {
    // 渲染应用
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // 验证首页元素
    expect(screen.getByText(/会议报告生成系统/i)).toBeInTheDocument();
    expect(screen.getByText(/上传文件/i)).toBeInTheDocument();
    expect(screen.getByText(/查看报告/i)).toBeInTheDocument();
    
    // 等待最近文件加载
    await waitFor(() => {
      expect(api.getFiles).toHaveBeenCalled();
    });
    
    // 验证最近文件显示
    expect(screen.getByText(/最近文件/i)).toBeInTheDocument();
    expect(screen.getByText('test1.txt')).toBeInTheDocument();
  });

  test('navigates to upload page correctly', async () => {
    // 渲染应用
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // 点击上传文件按钮
    const uploadButton = screen.getByText(/上传文件/i);
    fireEvent.click(uploadButton);
    
    // 验证导航到上传页面
    await waitFor(() => {
      expect(screen.getByText(/选择文件/i)).toBeInTheDocument();
      expect(screen.getByText(/文件分类/i)).toBeInTheDocument();
    });
    
    // 验证分类加载
    await waitFor(() => {
      expect(api.getCategories).toHaveBeenCalled();
    });
  });

  test('navigates to report page correctly', async () => {
    // 模拟报告数据
    api.getReport.mockResolvedValue({
      report_id: 'test-report-id',
      file_id: 'test-file-id',
      content: '# Test Report\n\nThis is a generated report.',
      model_id: 'test-model',
      prompt: 'Generate a test report',
      created_at: '2025-03-07T12:00:00'
    });
    
    // 渲染应用
    render(
      <MemoryRouter initialEntries={['/report/test-report-id']}>
        <App />
      </MemoryRouter>
    );
    
    // 验证报告页面加载
    await waitFor(() => {
      expect(api.getReport).toHaveBeenCalledWith('test-report-id');
    });
    
    // 验证报告内容显示
    await waitFor(() => {
      expect(screen.getByText(/Test Report/i)).toBeInTheDocument();
      expect(screen.getByText(/This is a generated report./i)).toBeInTheDocument();
    });
  });

  test('complete file upload and report generation flow', async () => {
    // 模拟上传成功响应
    api.uploadFile.mockResolvedValue({
      message: 'File uploaded successfully',
      file_id: 'test-file-id',
      s3_url: 'https://test-bucket.s3.amazonaws.com/test/file.txt'
    });
    
    // 模拟报告生成成功响应
    api.generateReport.mockResolvedValue({
      message: 'Report generated successfully',
      report_id: 'test-report-id'
    });
    
    // 模拟报告数据
    api.getReport.mockResolvedValue({
      report_id: 'test-report-id',
      file_id: 'test-file-id',
      content: '# Test Report\n\nThis is a generated report.',
      model_id: 'test-model',
      prompt: 'Generate a test report',
      created_at: '2025-03-07T12:00:00'
    });
    
    // 渲染应用
    render(
      <MemoryRouter initialEntries={['/upload']}>
        <App />
      </MemoryRouter>
    );
    
    // 等待分类加载完成
    await waitFor(() => {
      expect(api.getCategories).toHaveBeenCalled();
    });
    
    // 模拟文件选择
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/选择文件/i);
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // 选择分类
    const categorySelect = screen.getByLabelText(/文件分类/i);
    fireEvent.mouseDown(categorySelect);
    const meetingOption = await screen.findByText('会议记录');
    fireEvent.click(meetingOption);
    
    // 点击上传按钮
    const uploadButton = screen.getByRole('button', { name: /上传/i });
    fireEvent.click(uploadButton);
    
    // 验证上传调用
    await waitFor(() => {
      expect(api.uploadFile).toHaveBeenCalledWith(file, 'meeting');
    });
    
    // 验证生成报告按钮显示
    await waitFor(() => {
      expect(screen.getByText(/生成报告/i)).toBeInTheDocument();
    });
    
    // 点击生成报告按钮
    const generateButton = screen.getByText(/生成报告/i);
    fireEvent.click(generateButton);
    
    // 验证报告生成调用
    await waitFor(() => {
      expect(api.generateReport).toHaveBeenCalledWith('test-file-id', undefined, undefined);
    });
    
    // 验证导航到报告页面
    await waitFor(() => {
      expect(api.getReport).toHaveBeenCalledWith('test-report-id');
    });
    
    // 验证报告内容显示
    await waitFor(() => {
      expect(screen.getByText(/Test Report/i)).toBeInTheDocument();
      expect(screen.getByText(/This is a generated report./i)).toBeInTheDocument();
    });
  });
}); 