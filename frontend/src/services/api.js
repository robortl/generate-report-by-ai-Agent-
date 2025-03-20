import axios from 'axios';

// 创建axios实例
const api = axios.create({
  // 使用相对路径在开发环境中，使用容器名在生产环境中
  baseURL: '/api',  // 统一使用 /api 前缀，让nginx处理代理
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 60000, // 增加超时时间到60秒
  // 重试配置
  withCredentials: false,
});

// 添加请求拦截器
api.interceptors.request.use(
  config => {
    console.log(`发送请求到: ${config.url}`);
    console.log(`完整URL: ${config.baseURL}${config.url}`);
    console.log(`环境: ${process.env.NODE_ENV}`);
    return config;
  },
  error => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器
api.interceptors.response.use(
  response => {
    console.log(`收到来自 ${response.config.url} 的响应`);
    return response;
  },
  error => {
    if (error.code === 'ECONNABORTED') {
      console.error('请求超时:', error);
    } else if (error.message === 'Network Error') {
      console.error('网络错误 - 请检查服务器连接:', error);
    } else {
      console.error('响应错误:', error);
    }
    return Promise.reject(error);
  }
);

// 文件上传API
export const uploadFile = async (file, category) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// 获取文件分类
export const getCategories = async () => {
  const response = await api.get('/upload/categories');
  return response.data;
};

// 生成报告
export const generateReport = async (fileId, prompt, modelId) => {
  const response = await api.post('/report/generate', {
    file_id: fileId,
    prompt: prompt,
    model_id: modelId,
  });
  
  return response.data;
};

// 获取报告
export const getReport = async (reportId) => {
  const response = await api.get(`/report/${reportId}`);
  return response.data;
};

// 更新报告
export const updateReport = async (reportId, content) => {
  const response = await api.put(`/report/${reportId}`, {
    content: content,
  });
  
  return response.data;
};

// 获取可用模型
export const getModels = async () => {
  try {
    console.log('Calling getModels API...');
    console.log('API URL:', `${api.defaults.baseURL}/model/list`);
    const response = await api.get('/model/list');
    console.log('API Response:', response);
    
    // 将回姍数据过滤，只保留两个指定模型
    const allowedModels = [
      {
        id: 'anthropic.claude-3-haiku-20240307-v1:0',
        name: 'Claude 3 Haiku',
        provider: 'Anthropic',
        description: '高速モデル - 日常的なタスクに最適'
      },
      {
        id: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
        name: 'Claude 3.5 Sonnet',
        provider: 'Anthropic',
        description: '高性能モデル - 複雑なタスクに適した高品質出力'
      }
    ];
    
    console.log('Filtered to allowed models only:', allowedModels);
    return allowedModels;
    
  } catch (error) {
    console.error('Error fetching models:', error);
    return [];
  }
};

// 比较模型（用于文件比较）
export const compareModels = async (fileId, modelIds, prompt) => {
  try {
    console.log('Calling compareModels API with:', { fileId, modelIds, prompt });
    const response = await api.post('/model/compare', {
      file_id: fileId,
      model_ids: modelIds,
      prompt: prompt,
    });
    
    console.log('compareModels response:', response);
    
    // 确保返回数据有正确的结构
    if (!response.data) {
      throw new Error('API响应为空');
    }
    
    // 如果comparisons不存在或不是数组，初始化为空数组
    if (!response.data.comparisons || !Array.isArray(response.data.comparisons)) {
      console.warn('API响应中缺少comparisons数组，初始化为空数组');
      response.data.comparisons = [];
    }
    
    return response.data;
  } catch (error) {
    console.error('比较模型时出错:', error);
    // 返回一个带有错误信息的默认结构，这样UI层不会崩溃
    return { 
      comparisons: [], 
      analysis: `发生错误: ${error.message}`,
      error: error.message
    };
  }
};

// 比较报告（用于报告比较）
export const compareReports = async (reportId, modelId) => {
  try {
    console.log('Comparing reports with params:', { reportId, modelId });
    const response = await api.post('/report/compare', {
      report_id: reportId,
      model_id: modelId
    });
    
    console.log('Compare response:', response);
    
    if (!response || !response.data) {
      throw new Error('无效的比较响应');
    }
    
    return response.data;
  } catch (error) {
    console.error('Error comparing reports:', error);
    throw new Error(error.response?.data?.message || '比较报告失败');
  }
};

// 提取关键词
export const extractKeywords = async (fileId, topN = 10) => {
  const response = await api.post('/model/semantic/keywords', {
    file_id: fileId,
    top_n: topN,
  });
  
  return response.data;
};

// 处理结构化数据
export const processStructuredData = async (fileId, schema = null) => {
  const response = await api.post('/model/semantic/structure', {
    file_id: fileId,
    schema: schema,
  });
  
  return response.data;
};

// 重试机制
const retryRequest = async (apiCall, maxRetries = 3) => {
  let retries = 0;
  let lastError;
  
  while (retries <= maxRetries) {
    try {
      // 每次重试增加日志
      if (retries > 0) {
        console.log(`尝试第 ${retries} 次重试请求...`);
      }
      
      return await apiCall();
    } catch (error) {
      lastError = error;
      retries++;
      
      // 如果是最后一次重试或者有响应状态码（表示服务器已响应），则不再重试
      if (retries > maxRetries || (error.response && error.response.status !== 0)) {
        throw error;
      }
      
      // 按指数退避策略增加等待时间
      const delay = Math.min(1000 * Math.pow(2, retries - 1), 10000);
      console.log(`网络错误，将在 ${delay}ms 后重试...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

// 获取文件列表
export const getFiles = async (category = null, limit = 50, lastKey = null) => {
  // 记录当前环境和baseURL
  console.log('当前环境:', process.env.NODE_ENV);
  console.log('API baseURL:', process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000');
  
  let url = '/files';
  const params = {};
  
  if (category) params.category = category;
  if (limit) params.limit = limit;
  if (lastKey) params.last_key = lastKey;
  
  try {
    console.log('正在获取文件列表...');
    const response = await retryRequest(() => api.get(url, { params }));
    console.log('成功获取文件列表:', response.data);
    return response.data;
  } catch (error) {
    console.error('获取文件列表失败:', error);
    console.error('错误详情:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      code: error.code,
      url: url,
      params: params
    });
    
    // 如果是网络错误或超时, 返回空结果而不是抛出错误
    if (error.message === 'Network Error' || 
        error.code === 'ECONNABORTED' || 
        error.code === 'ERR_NETWORK' ||
        error.message.includes('timeout') ||
        error.message.includes('reset')) {
      console.log('网络错误或超时，返回空数组');
      return { items: [] };
    }
    throw error;
  }
};

// 重新生成报告
export const regenerateReport = async (reportId, prompt, modelId) => {
  const response = await api.post(`/report/${reportId}/regenerate`, {
    prompt: prompt,
    model_id: modelId,
  });
  
  return response.data;
};

// 下载S3文件
export const downloadS3File = async (reportId) => {
  const response = await api.get(`/report/${reportId}/download`, {
    params: { format: 's3' },
    responseType: 'blob',
  });
  
  // 从响应头获取文件名
  const contentDisposition = response.headers['content-disposition'];
  let filename = `file_${reportId}`;
  if (contentDisposition) {
    const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
    if (matches != null && matches[1]) {
      filename = matches[1].replace(/['"]/g, '');
    }
  }

  // 创建下载链接
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
  
  return true;
};

export const getReportsList = async () => {
  try {
    console.log('Fetching reports list...');
    const response = await api.get('/report/list');
    console.log('Reports list response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching reports list:', error);
    console.error('Error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });
    throw error;
  }
};

export default api; 