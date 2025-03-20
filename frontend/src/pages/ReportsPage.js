import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondary,
  Container,
} from '@mui/material';
import {
  Description as ReportIcon,
  Download as DownloadIcon,
  KeyboardArrowRight as ArrowIcon,
} from '@mui/icons-material';
import { getReportsList } from '../services/api';

function ReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        console.log('开始获取报告列表...');
        const response = await getReportsList();
        console.log('获取到的报告列表数据:', response);
        
        if (!response || !response.items) {
          throw new Error('Invalid response format: missing items array');
        }
        
        // 验证数据格式
        const validReports = response.items.filter(report => {
          const isValid = report && report.report_id && report.title;
          if (!isValid) {
            console.warn('发现无效的报告数据:', report);
          }
          return isValid;
        });
        
        console.log('有效的报告数量:', validReports.length);
        setReports(validReports);
        setLoading(false);
      } catch (err) {
        console.error('获取报告列表失败:', err);
        console.error('错误详情:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status
        });
        setError('无法加载报告列表。请稍后再试。');
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const handleViewReport = (reportId) => {
    console.log('查看报告:', reportId);
    navigate(`/report/${reportId}`);
  };

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Typography color="error" variant="h6">
          Error: {error}
        </Typography>
      </Container>
    );
  }

  console.log('渲染报告列表，数量:', reports.length);

  return (
    <Container>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          レポート管理 ({reports.length})
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          すべての生成されたレポートを表示し管理する
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {reports.map((report) => {
          console.log('渲染报告:', report);
          return (
            <Grid item xs={12} md={6} key={report.report_id}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <ReportIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6" component="h2">
                      {report.title || '名称未設定レポート'}
                    </Typography>
                  </Box>
                  {report.summary && (
                    <Typography variant="body2" color="textSecondary" paragraph>
                      {report.summary}
                    </Typography>
                  )}
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    作成日時: {new Date(new Date(report.created_at).getTime() + 9*60*60*1000).toLocaleString('ja-JP')}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    ステータス: {report.status === 'completed' ? '完了' : '処理中'}
                  </Typography>
                </CardContent>
                <Divider />
                <CardActions>
                  <Button
                    startIcon={<ArrowIcon />}
                    onClick={() => handleViewReport(report.report_id)}
                  >
                    レポートを表示
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {reports.length === 0 && (
        <Box textAlign="center" mt={4}>
          <Typography variant="h6" color="textSecondary">
            レポートがありません
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/upload')}
            sx={{ mt: 2 }}
          >
            ファイルをアップロードしてレポートを生成
          </Button>
        </Box>
      )}
    </Container>
  );
}

export default ReportsPage; 