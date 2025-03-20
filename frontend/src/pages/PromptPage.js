import React, { useState } from 'react';
import {
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Grid,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material';

function PromptPage() {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePromptChange = (event) => {
    setPrompt(event.target.value);
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      setError('请输入提示词');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 这里应该调用API来测试提示词，但目前我们只是模拟一个响应
      // 实际实现时，应该替换为真实的API调用
      setTimeout(() => {
        setResult(
          `这是基于提示词 "${prompt}" 生成的示例响应。\n\n在实际应用中，这里会显示模型基于您的提示词生成的内容。您可以根据生成结果调整提示词，以获得更好的输出。`
        );
        setLoading(false);
      }, 1500);
    } catch (err) {
      console.error('Error testing prompt:', err);
      setError('测试提示词时出错。请稍后再试。');
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        提示词调整
      </Typography>
      <Typography variant="body1" paragraph>
        在这里您可以测试和优化提示词，以获得更好的生成结果。
      </Typography>

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              输入提示词
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={10}
              variant="outlined"
              placeholder="请输入您想要测试的提示词..."
              value={prompt}
              onChange={handlePromptChange}
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmit}
              disabled={loading || !prompt.trim()}
            >
              {loading ? <CircularProgress size={24} /> : '测试提示词'}
            </Button>
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              生成结果
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {loading ? (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '200px',
                }}
              >
                <CircularProgress />
              </Box>
            ) : result ? (
              <Typography
                variant="body1"
                component="pre"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  p: 2,
                  bgcolor: '#f5f5f5',
                  borderRadius: 1,
                  minHeight: '200px',
                }}
              >
                {result}
              </Typography>
            ) : (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ fontStyle: 'italic', textAlign: 'center', py: 10 }}
              >
                测试提示词后，生成的结果将显示在这里
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Paper elevation={2} sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          提示词优化技巧
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="body1" paragraph>
          1. <strong>明确指定输出格式</strong>：例如，"生成一份包含标题、摘要和三个主要部分的报告"
        </Typography>
        <Typography variant="body1" paragraph>
          2. <strong>提供足够的上下文</strong>：包含相关背景信息，帮助模型理解任务
        </Typography>
        <Typography variant="body1" paragraph>
          3. <strong>使用示例</strong>：提供输入-输出的示例，说明您期望的结果
        </Typography>
        <Typography variant="body1" paragraph>
          4. <strong>分步骤引导</strong>：将复杂任务分解为步骤，引导模型逐步思考
        </Typography>
        <Typography variant="body1">
          5. <strong>迭代优化</strong>：根据生成结果不断调整提示词，直到获得满意的输出
        </Typography>
      </Paper>
    </Box>
  );
}

export default PromptPage; 