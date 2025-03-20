import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Divider,
  Card,
  CardContent,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Compare as CompareIcon,
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { getReport, getModels, compareReports } from '../services/api';
import MarkdownRenderer from '../components/MarkdownRenderer';

// 标签面板组件
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`compare-tabpanel-${index}`}
      aria-labelledby={`compare-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function ComparePage() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md')); // 检测是否为移动设备
  const [originalReport, setOriginalReport] = useState(null);
  const [comparisonReport, setComparisonReport] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  // 获取原始报告和可用模型
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 获取原始报告
        const reportData = await getReport(reportId);
        
        if (!reportData) {
          throw new Error('无法获取报告数据');
        }
        
        setOriginalReport(reportData);
        
        // 获取可用模型列表
        const modelsData = await getModels();
        
        if (!Array.isArray(modelsData) || modelsData.length === 0) {
          setModels([]);
          setError('没有找到可用的模型');
          setLoading(false);
          return;
        }
        
        // 过滤掉当前使用的模型
        const currentModelId = reportData?.model_id || reportData?.modelId;
        
        const filteredModels = modelsData.filter(model => model.id !== currentModelId);
        
        if (filteredModels.length === 0) {
          setError('没有其他可用的模型进行比较');
          setModels([]);
        } else {
          setModels(filteredModels);
          setSelectedModel(filteredModels[0].id);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message || '加载数据时发生错误');
        setLoading(false);
        setModels([]);
        setSelectedModel('');
      }
    };

    if (reportId) {
      fetchData();
    }
  }, [reportId]);

  // 处理标签切换
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // 处理模型选择
  const handleModelChange = (event) => {
    const value = event.target.value;
    setSelectedModel(value);
  };

  // 处理比较生成
  const handleCompare = async () => {
    if (!selectedModel) {
      setError('请选择要比较的模型');
      return;
    }

    try {
      setComparing(true);
      setError(null);
      
      const comparisonData = await compareReports(reportId, selectedModel);
      
      if (!comparisonData) {
        throw new Error('未收到比较数据');
      }
      
      setComparisonReport(comparisonData);
      setComparing(false);
    } catch (err) {
      console.error('Error comparing reports:', err);
      setError(err.message || '生成比较报告失败。请稍后再试。');
      setComparing(false);
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
          レポートに戻る
        </Button>
      </Box>
    );
  }

  if (!originalReport) {
    return (
      <Box>
        <Alert severity="warning" sx={{ mt: 2, mb: 2 }}>
          未找到原始报告数据
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
          <CompareIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          モデル比较
        </Typography>

        <Button startIcon={<BackIcon />} onClick={handleBack}>
          返回报告
        </Button>
      </Box>

      {/* 原始报告信息 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          原版レポート情報
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              ファイル名: {originalReport?.original_filename || '不明'}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              分類: {originalReport?.category || '不明'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              使用モデル: {originalReport?.model_name || '不明'}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              生成日時: {originalReport?.generated_at ? new Date(new Date(originalReport.generated_at).getTime() + 9*60*60*1000).toLocaleString('ja-JP') : '不明'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* 模型选择和比较按钮 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          比较モデルを選択
        </Typography>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        ) : error && !models.length ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : !models || models.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            比较可能な他のモデルがありません
          </Alert>
        ) : (
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <FormControl fullWidth error={!selectedModel}>
                <InputLabel id="model-select-label">モデルを選択</InputLabel>
                <Select
                  labelId="model-select-label"
                  id="model-select"
                  value={selectedModel}
                  label="モデルを選択"
                  onChange={handleModelChange}
                >
                  <MenuItem value="">
                    <em>モデルを選択してください</em>
                  </MenuItem>
                  
                  {models.map((model) => (
                    <MenuItem key={model.id} value={model.id}>
                      <Box sx={{ py: 1 }}>
                        <Typography variant="subtitle1" component="div">
                          {model.name || '不明モデル'}
                        </Typography>
                        {model.provider && (
                          <Typography variant="caption" color="text.secondary" component="div">
                            プロバイダー: {model.provider}
                          </Typography>
                        )}
                        {model.description && (
                          <Typography variant="body2" color="text.secondary" component="div" sx={{ mt: 0.5 }}>
                            {model.description}
                          </Typography>
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                variant="contained"
                startIcon={comparing ? <CircularProgress size={20} /> : <RefreshIcon />}
                onClick={handleCompare}
                disabled={comparing || !selectedModel}
                fullWidth
                sx={{ py: 1.5 }}
              >
                {comparing ? '比较生成中...' : '比较レポートを生成'}
              </Button>
            </Grid>
          </Grid>
        )}
      </Paper>

      {/* 比较结果 */}
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              fontWeight: 'bold',
              py: 2
            }
          }}
        >
          <Tab label="要約比较" />
          <Tab label="内容比较" />
          <Tab label="キーポイント比较" />
          <Tab label="提案比较" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    原版モデル: {originalReport.model_name || '不明'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {originalReport.summary ? (
                    <MarkdownRenderer content={originalReport.summary} />
                  ) : (
                    <Typography variant="body1">要約がありません</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    比较模型: {comparisonReport?.model_name || '未选择'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {comparisonReport?.summary ? (
                    <MarkdownRenderer content={comparisonReport.summary} />
                  ) : (
                    <Typography variant="body1">请先点击"生成比较报告"按钮生成比较内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3} sx={{ height: '100%' }}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: '0 0 auto' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    原始模型: {originalReport.model_name || '未知'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                </CardContent>
                <CardContent sx={{ flex: '1 1 auto', overflow: 'auto', maxHeight: isMobile ? '400px' : '70vh' }}>
                  {originalReport.content ? (
                    <MarkdownRenderer content={originalReport.content} />
                  ) : (
                    <Typography variant="body1">无详细内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: '0 0 auto' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    比较模型: {comparisonReport?.model_name || '未选择'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                </CardContent>
                <CardContent sx={{ flex: '1 1 auto', overflow: 'auto', maxHeight: isMobile ? '400px' : '70vh' }}>
                  {comparisonReport?.content ? (
                    <MarkdownRenderer content={comparisonReport.content} />
                  ) : (
                    <Typography variant="body1">请先点击"生成比较报告"按钮生成比较内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3} sx={{ height: '100%' }}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: '0 0 auto' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    原始模型: {originalReport.model_name || '未知'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                </CardContent>
                <CardContent sx={{ flex: '1 1 auto', overflow: 'auto', maxHeight: isMobile ? '400px' : '70vh' }}>
                  {originalReport.key_points && originalReport.key_points.length > 0 ? (
                    <Box sx={{ '& ul': { pl: 4, my: 1 } }}>
                      <ul>
                        {originalReport.key_points.map((point, index) => (
                          <li key={index}>
                            <MarkdownRenderer content={point} />
                          </li>
                        ))}
                      </ul>
                    </Box>
                  ) : originalReport.content ? (
                    // 如果没有key_points字段，但有内容，显示内容
                    <MarkdownRenderer content={originalReport.content} />
                  ) : (
                    <Typography variant="body1">无关键点内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: '0 0 auto' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    比较模型: {comparisonReport?.model_name || '未选择'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                </CardContent>
                <CardContent sx={{ flex: '1 1 auto', overflow: 'auto', maxHeight: isMobile ? '400px' : '70vh' }}>
                  {comparisonReport?.key_points && comparisonReport.key_points.length > 0 ? (
                    <Box sx={{ '& ul': { pl: 4, my: 1 } }}>
                      <ul>
                        {comparisonReport.key_points.map((point, index) => (
                          <li key={index}>
                            <MarkdownRenderer content={point} />
                          </li>
                        ))}
                      </ul>
                    </Box>
                  ) : comparisonReport?.content ? (
                    // 如果没有key_points字段，但有内容，显示内容
                    <MarkdownRenderer content={comparisonReport.content} />
                  ) : (
                    <Typography variant="body1">请先点击"生成比较报告"按钮生成比较内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3} sx={{ height: '100%' }}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: '0 0 auto' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    原始模型: {originalReport.model_name || '未知'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                </CardContent>
                <CardContent sx={{ flex: '1 1 auto', overflow: 'auto', maxHeight: isMobile ? '400px' : '70vh' }}>
                  {originalReport.recommendations && originalReport.recommendations.length > 0 ? (
                    <Box sx={{ '& ul': { pl: 4, my: 1 } }}>
                      <ul>
                        {originalReport.recommendations.map((recommendation, index) => (
                          <li key={index}>
                            <MarkdownRenderer content={recommendation} />
                          </li>
                        ))}
                      </ul>
                    </Box>
                  ) : originalReport.content ? (
                    // 如果没有recommendations字段，但有内容，显示内容
                    <MarkdownRenderer content={originalReport.content} />
                  ) : (
                    <Typography variant="body1">无建议内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: '0 0 auto' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    比较模型: {comparisonReport?.model_name || '未选择'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                </CardContent>
                <CardContent sx={{ flex: '1 1 auto', overflow: 'auto', maxHeight: isMobile ? '400px' : '70vh' }}>
                  {comparisonReport?.recommendations && comparisonReport.recommendations.length > 0 ? (
                    <Box sx={{ '& ul': { pl: 4, my: 1 } }}>
                      <ul>
                        {comparisonReport.recommendations.map((recommendation, index) => (
                          <li key={index}>
                            <MarkdownRenderer content={recommendation} />
                          </li>
                        ))}
                      </ul>
                    </Box>
                  ) : comparisonReport?.content ? (
                    // 如果没有recommendations字段，但有内容，显示内容
                    <MarkdownRenderer content={comparisonReport.content} />
                  ) : (
                    <Typography variant="body1">请先点击"生成比较报告"按钮生成比较内容</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
}

export default ComparePage;