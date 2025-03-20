import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
} from '@mui/material';
import {
  Description as ReportIcon,
  CloudUpload as UploadIcon,
  Compare as CompareIcon,
  Code as PromptIcon,
} from '@mui/icons-material';
import { getFiles } from '../services/api';

function HomePage() {
  const [recentFiles, setRecentFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRecentFiles = async () => {
      try {
        setLoading(true);
        const response = await getFiles(null, 5);
        setRecentFiles(response.items || []);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching recent files:', err);
        // 提供更详细的错误信息
        const errorMessage = err.message || '最近のファイルを読み込めませんでした。';
        setError(`エラー: ${errorMessage}. サーバーが応答していないか、ネットワークの問題が発生している可能性があります。`);
        setLoading(false);
        
        // 尝试使用空数组代替
        setRecentFiles([]);
      }
    };

    // 添加错误处理包装
    fetchRecentFiles().catch(e => {
      console.error('Unhandled error in fetchRecentFiles:', e);
      setError('予期せぬエラーが発生しました。ページを更新してください。');
      setLoading(false);
    });
  }, []);

  const features = [
    {
      title: 'ファイルアップロード',
      description: '記録やビジネス文書をアップロード、複数のファイル形式に対応',
      icon: <UploadIcon fontSize="large" color="primary" />,
      link: '/upload',
    },
    {
      title: 'レポート生成',
      description: 'AIを使用して構造化されたレポートを自動生成、編集や修正も可能',
      icon: <ReportIcon fontSize="large" color="primary" />,
      link: '/upload',
    },
    {
      title: 'モデル比較',
      description: '異なるAIモデルの出力結果を比較し、最適なモデルを選択',
      icon: <CompareIcon fontSize="large" color="primary" />,
      link: '/compare',
    },
    // {
    //   title: 'プロンプト調整',
    //   description: 'プロンプトをカスタマイズして最適化し、より良い生成結果を取得',
    //   icon: <PromptIcon fontSize="large" color="primary" />,
    //   link: '/prompt',
    // },
  ];

  return (
    <Box sx={{ width: '100%' }}>
      {/* 欢迎部分 */}
      <Paper
        elevation={3}
        sx={{
          p: 4,
          mb: 4,
          background: 'linear-gradient(45deg, #1976d2 30%, #21CBF3 90%)',
          color: 'white',
          borderRadius: 1
        }}
      >
        <Typography variant="h4" gutterBottom>
          レポート生成システムへようこそ
        </Typography>
        <Typography variant="subtitle1" paragraph>
          このシステムはAWS Bedrock、LangChain、Haystackフレームワークを活用して、記録から構造化されたレポートを自動生成します。
        </Typography>
        <Button
          variant="contained"
          color="secondary"
          component={RouterLink}
          to="/upload"
          startIcon={<UploadIcon />}
          sx={{ mt: 2 }}
        >
          ファイルのアップロードを開始
        </Button>
      </Paper>

      {/* 功能部分 */}
      <Typography variant="h5" gutterBottom>
        主な機能
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4, mt: 0 }}>
        {features.map((feature) => (
          <Grid item xs={12} sm={4} md={4} key={feature.title} sx={{ px: 1 }}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 1 }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h6" component="h2" align="center" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  color="primary"
                  component={RouterLink}
                  to={feature.link}
                  fullWidth
                >
                  詳細を見る
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 最近文件部分 */}
      <Typography variant="h5" gutterBottom>
        最近処理したファイル
      </Typography>
      <Paper elevation={2} sx={{ p: 2, borderRadius: 1 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : recentFiles.length > 0 ? (
          <List>
            {recentFiles.map((file) => (
              <React.Fragment key={file.file_id}>
                <ListItem
                  button
                  component={RouterLink}
                  to={file.report_id ? `/report/${file.report_id}` : `/upload`}
                >
                  <ListItemIcon>
                    <ReportIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={file.original_filename}
                    secondary={`カテゴリ: ${file.category} | ステータス: ${
                      file.status === 'completed'
                        ? '完了'
                        : file.status === 'processing'
                        ? '処理中'
                        : 'アップロード済み'
                    }`}
                  />
                </ListItem>
                <Divider variant="inset" component="li" />
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography align="center" sx={{ p: 2 }}>
            最近処理したファイルはありません。ファイルをアップロードしてレポートを生成しましょう！
          </Typography>
        )}
      </Paper>
    </Box>
  );
}

export default HomePage; 