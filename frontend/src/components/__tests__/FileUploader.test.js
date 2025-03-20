import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileUploader from '../FileUploader';
import * as api from '../../services/api';

// 模拟 API 服务
jest.mock('../../services/api');

describe('FileUploader Component Tests', () => {
  // 每个测试前重置模拟
  beforeEach(() => {
    jest.clearAllMocks();
    
    // 模拟分类数据
    api.getCategories.mockResolvedValue([
      { id: 'meeting', name: '会议记录' },
      { id: 'report', name: '业务报告' }
    ]);
  });

  test('renders file uploader correctly', async () => {
    // 渲染组件
    render(<FileUploader onUploadSuccess={jest.fn()} />);
    
    // 等待分类加载完成
    await waitFor(() => {
      expect(api.getCategories).toHaveBeenCalled();
    });
    
    // 验证组件渲染
    expect(screen.getByText(/上传文件/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/选择文件/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/文件分类/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /上传/i })).toBeInTheDocument();
  });

  test('displays categories correctly', async () => {
    // 渲染组件
    render(<FileUploader onUploadSuccess={jest.fn()} />);
    
    // 等待分类加载完成
    await waitFor(() => {
      expect(api.getCategories).toHaveBeenCalled();
    });
    
    // 验证分类选项
    const categorySelect = screen.getByLabelText(/文件分类/i);
    expect(categorySelect).toBeInTheDocument();
    
    // 打开下拉菜单
    fireEvent.mouseDown(categorySelect);
    
    // 验证分类选项
    await waitFor(() => {
      expect(screen.getByText('会议记录')).toBeInTheDocument();
      expect(screen.getByText('业务报告')).toBeInTheDocument();
    });
  });

  test('handles file selection correctly', async () => {
    // 渲染组件
    render(<FileUploader onUploadSuccess={jest.fn()} />);
    
    // 等待分类加载完成
    await waitFor(() => {
      expect(api.getCategories).toHaveBeenCalled();
    });
    
    // 模拟文件选择
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/选择文件/i);
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // 验证文件名显示
    expect(screen.getByText('test.txt')).toBeInTheDocument();
  });

  test('handles file upload correctly', async () => {
    // 模拟上传成功响应
    const mockResponse = {
      message: 'File uploaded successfully',
      file_id: 'test-file-id',
      s3_url: 'https://test-bucket.s3.amazonaws.com/test/file.txt'
    };
    api.uploadFile.mockResolvedValue(mockResponse);
    
    // 模拟上传成功回调
    const onUploadSuccess = jest.fn();
    
    // 渲染组件
    render(<FileUploader onUploadSuccess={onUploadSuccess} />);
    
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
    
    // 验证成功回调
    await waitFor(() => {
      expect(onUploadSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  test('displays error message on upload failure', async () => {
    // 模拟上传失败
    api.uploadFile.mockRejectedValue(new Error('Upload failed'));
    
    // 渲染组件
    render(<FileUploader onUploadSuccess={jest.fn()} />);
    
    // 等待分类加载完成
    await waitFor(() => {
      expect(api.getCategories).toHaveBeenCalled();
    });
    
    // 模拟文件选择
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/选择文件/i);
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // 点击上传按钮
    const uploadButton = screen.getByRole('button', { name: /上传/i });
    fireEvent.click(uploadButton);
    
    // 验证错误消息
    await waitFor(() => {
      expect(screen.getByText(/上传失败/i)).toBeInTheDocument();
    });
  });
}); 