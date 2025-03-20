import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Grid,
  TextField,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Divider,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  ArrowBack as BackIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { getReport, getReportSettings, updateReportSettings, regenerateReport } from '../services/api';

function SettingsPage() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // 获取报告和设置数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 获取报告数据
        const reportData = await getReport(reportId);
        setReport(reportData);
        
        // 获取报告设置
        const settingsData = await getReportSettings(reportId);
        setSettings(settingsData);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('无法加载数据。请稍后再试。');
        setLoading(false);
      }
    };

    fetchData();
  }, [reportId]);

  // 处理设置更新
  const handleSettingChange = (key, value) => {
    setSettings({
      ...settings,
      [key]: value,
    });
  };

  // 处理保存设置
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      await updateReportSettings(reportId, settings);
      
      setSuccess('设置已成功保存');
      setSaving(false);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError('保存设置失败。请稍后再试。');
      setSaving(false);
    }
  };

  // 处理重新生成报告
  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      setError(null);
      setSuccess(null);
      
      const data = await regenerateReport(reportId, settings);
      setReport(data);
      
      setSuccess('报告已成功重新生成');
      setRegenerating(false);
      
      // 导航到报告页面
      navigate(`/report/${reportId}`);
    } catch (err) {
      console.error('Error regenerating report:', err);
      setError('重新生成报告失败。请稍后再试。');
      setRegenerating(false);
    }
  };

  // 返回报告页面
  const handleBack = () => {
    navigate(`/report/${reportId}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
          {error}
        </Alert>
        <Button startIcon={<BackIcon />} onClick={handleBack}>
          返回报告
        </Button>
      </Box>
    );
  }

  if (!report || !settings) {
    return (
      <Box>
        <Alert severity="warning" sx={{ mt: 2, mb: 2 }}>
          未找到报告或设置数据
        </Alert>
        <Button startIcon={<BackIcon />} onClick={handleBack}>
          返回
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* 页面标题和操作按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          报告设置
        </Typography>

        <Box>
          <Button
            variant="outlined"
            startIcon={<BackIcon />}
            onClick={handleBack}
            sx={{ mr: 1 }}
          >
            返回报告
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={handleSaveSettings}
            disabled={saving}
            sx={{ mr: 1 }}
          >
            {saving ? '保存中...' : '保存设置'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<RefreshIcon />}
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            {regenerating ? '生成中...' : '重新生成报告'}
          </Button>
        </Box>
      </Box>

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {/* 报告信息 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          报告信息
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              文件名: {report.original_filename}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              分类: {report.category}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              使用模型: {report.model_name}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              生成时间: {new Date(report.generated_at).toLocaleString()}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* 模型设置 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          模型设置
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel id="model-select-label">选择模型</InputLabel>
              <Select
                labelId="model-select-label"
                value={settings.model_id || ''}
                label="选择模型"
                onChange={(e) => handleSettingChange('model_id', e.target.value)}
              >
                {settings.available_models && settings.available_models.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name} - {model.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 3 }}>
              <Typography gutterBottom>温度 (Temperature)</Typography>
              <Slider
                value={settings.temperature || 0.7}
                min={0}
                max={1}
                step={0.1}
                valueLabelDisplay="auto"
                onChange={(e, value) => handleSettingChange('temperature', value)}
              />
              <Typography variant="caption" color="text.secondary">
                较低的值使输出更确定，较高的值使输出更多样化
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* 报告内容设置 */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">报告内容设置</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.include_summary || false}
                    onChange={(e) => handleSettingChange('include_summary', e.target.checked)}
                  />
                }
                label="包含摘要"
              />
              <Typography variant="caption" color="text.secondary" display="block">
                在报告中包含文档摘要
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.include_key_points || false}
                    onChange={(e) => handleSettingChange('include_key_points', e.target.checked)}
                  />
                }
                label="包含关键点"
              />
              <Typography variant="caption" color="text.secondary" display="block">
                在报告中包含关键点列表
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.include_recommendations || false}
                    onChange={(e) => handleSettingChange('include_recommendations', e.target.checked)}
                  />
                }
                label="包含建议"
              />
              <Typography variant="caption" color="text.secondary" display="block">
                在报告中包含建议列表
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="关键点数量"
                type="number"
                value={settings.key_points_count || 5}
                onChange={(e) => handleSettingChange('key_points_count', parseInt(e.target.value))}
                InputProps={{ inputProps: { min: 1, max: 20 } }}
              />
              <Typography variant="caption" color="text.secondary" display="block">
                生成的关键点数量
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 提示词设置 */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">提示词设置</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="摘要提示词"
                multiline
                rows={3}
                value={settings.summary_prompt || ''}
                onChange={(e) => handleSettingChange('summary_prompt', e.target.value)}
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                用于生成摘要的提示词模板
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="关键点提示词"
                multiline
                rows={3}
                value={settings.key_points_prompt || ''}
                onChange={(e) => handleSettingChange('key_points_prompt', e.target.value)}
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                用于生成关键点的提示词模板
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="建议提示词"
                multiline
                rows={3}
                value={settings.recommendations_prompt || ''}
                onChange={(e) => handleSettingChange('recommendations_prompt', e.target.value)}
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                用于生成建议的提示词模板
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 高级设置 */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">高级设置</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>最大标记数 (Max Tokens)</Typography>
                <Slider
                  value={settings.max_tokens || 1000}
                  min={100}
                  max={4000}
                  step={100}
                  valueLabelDisplay="auto"
                  onChange={(e, value) => handleSettingChange('max_tokens', value)}
                />
                <Typography variant="caption" color="text.secondary">
                  生成的最大标记数量
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Top P</Typography>
                <Slider
                  value={settings.top_p || 0.9}
                  min={0.1}
                  max={1}
                  step={0.1}
                  valueLabelDisplay="auto"
                  onChange={(e, value) => handleSettingChange('top_p', value)}
                />
                <Typography variant="caption" color="text.secondary">
                  控制生成文本的多样性
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.use_streaming || false}
                    onChange={(e) => handleSettingChange('use_streaming', e.target.checked)}
                  />
                }
                label="使用流式生成"
              />
              <Typography variant="caption" color="text.secondary" display="block">
                启用流式生成以获得更快的响应
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.use_cache || true}
                    onChange={(e) => handleSettingChange('use_cache', e.target.checked)}
                  />
                }
                label="使用缓存"
              />
              <Typography variant="caption" color="text.secondary" display="block">
                启用缓存以提高性能
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 底部操作按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<BackIcon />}
          onClick={handleBack}
          sx={{ mr: 1 }}
        >
          取消
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
          disabled={saving}
          sx={{ mr: 1 }}
        >
          {saving ? '保存中...' : '保存设置'}
        </Button>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<RefreshIcon />}
          onClick={handleRegenerate}
          disabled={regenerating}
        >
          {regenerating ? '生成中...' : '应用并重新生成'}
        </Button>
      </Box>
    </Box>
  );
}

export default SettingsPage; 