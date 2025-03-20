import React, { Component } from 'react';
import { Box, Typography, Button, Paper, Alert } from '@mui/material';
import { RefreshRounded } from '@mui/icons-material';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  // 捕获子组件中的错误
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  // 记录错误信息
  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    console.error("Error caught by ErrorBoundary:", error, errorInfo);
  }

  // 重置应用
  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
    // 强制刷新页面
    window.location.reload();
  }

  // 检查是否为连接重置错误
  isConnectionResetError() {
    const { error } = this.state;
    return error && (
      error.message?.includes('ERR_CONNECTION_RESET') ||
      error.message?.includes('Network Error') ||
      error.message?.includes('Failed to fetch')
    );
  }

  render() {
    if (this.state.hasError) {
      // 连接重置错误的特殊处理
      if (this.isConnectionResetError()) {
        return (
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              minHeight: '80vh',
              padding: 4
            }}
          >
            <Paper 
              elevation={3} 
              sx={{ 
                p: 4, 
                maxWidth: 600, 
                width: '100%', 
                textAlign: 'center'
              }}
            >
              <Typography variant="h5" color="error" gutterBottom>
                接続エラー (ERR_CONNECTION_RESET)
              </Typography>
              
              <Alert severity="error" sx={{ mb: 3 }}>
                サーバーへの接続がリセットされました。ネットワーク接続を確認してください。
              </Alert>
              
              <Typography variant="body1" paragraph>
                考えられる原因:
              </Typography>
              
              <Box sx={{ textAlign: 'left', mb: 3 }}>
                <Typography variant="body2" paragraph>
                  • バックエンドサーバーが起動していないか応答していません
                </Typography>
                <Typography variant="body2" paragraph>
                  • ネットワーク接続に問題があります
                </Typography>
                <Typography variant="body2" paragraph>
                  • プロキシ設定やファイアウォールが接続をブロックしています
                </Typography>
              </Box>
              
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<RefreshRounded />}
                onClick={this.handleReset}
                fullWidth
              >
                再読み込み
              </Button>
            </Paper>
          </Box>
        );
      }
      
      // 一般的なエラー処理
      return (
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            padding: 4 
          }}
        >
          <Typography variant="h5" color="error" gutterBottom>
            エラーが発生しました
          </Typography>
          <Typography variant="body1" paragraph>
            アプリケーションでエラーが発生しました。
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<RefreshRounded />}
            onClick={this.handleReset}
          >
            リセット
          </Button>
        </Box>
      );
    }

    // 正常时是children表示
    return this.props.children;
  }
}

export default ErrorBoundary;