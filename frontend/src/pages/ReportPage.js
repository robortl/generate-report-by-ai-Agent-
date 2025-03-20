import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Divider,
  Chip,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tabs,
  Tab,
  Alert,
  Container,
} from '@mui/material';
import {
  Description as ReportIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  KeyboardArrowRight as ArrowIcon,
  InsertDriveFile as FileIcon,
  Compare as CompareIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { getReport, regenerateReport, downloadS3File } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { styled } from '@mui/material/styles';

// 样式定义
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginTop: theme.spacing(3),
  marginBottom: theme.spacing(3),
}));

const MarkdownContainer = styled(Box)(({ theme }) => ({
  '& h1': {
    fontSize: '2em',
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(2),
    color: theme.palette.primary.main,
    fontWeight: 600,
    borderBottom: `1px solid ${theme.palette.divider}`,
    paddingBottom: theme.spacing(1),
  },
  '& h2': {
    fontSize: '1.5em',
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(2),
    color: theme.palette.primary.main,
    fontWeight: 600,
  },
  '& h3': {
    fontSize: '1.3em',
    marginTop: theme.spacing(3),
    marginBottom: theme.spacing(2),
    color: theme.palette.text.secondary,
    fontWeight: 500,
  },
  '& p': {
    marginBottom: theme.spacing(2),
    lineHeight: 1.8,
    fontSize: '1rem',
  },
  '& ul, & ol': {
    marginBottom: theme.spacing(2),
    paddingLeft: theme.spacing(3),
  },
  '& li': {
    marginBottom: theme.spacing(1),
    lineHeight: 1.6,
  },
  '& blockquote': {
    borderLeft: `4px solid ${theme.palette.primary.main}`,
    margin: theme.spacing(2, 0),
    padding: theme.spacing(1, 2),
    backgroundColor: theme.palette.background.default,
    '& p': {
      margin: 0,
    },
  },
  '& code': {
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(0.5, 1),
    borderRadius: 4,
    fontSize: '0.9em',
  },
  '& pre': {
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(2),
    borderRadius: 4,
    overflow: 'auto',
    '& code': {
      padding: 0,
      backgroundColor: 'transparent',
    },
  },
  '& table': {
    width: '100%',
    borderCollapse: 'collapse',
    marginBottom: theme.spacing(2),
    '& th, & td': {
      border: `1px solid ${theme.palette.divider}`,
      padding: theme.spacing(1),
      textAlign: 'left',
    },
    '& th': {
      backgroundColor: theme.palette.background.default,
      fontWeight: 600,
    },
  },
  '& img': {
    maxWidth: '100%',
    height: 'auto',
    display: 'block',
    margin: theme.spacing(2, 'auto'),
  },
  '& hr': {
    margin: theme.spacing(3, 0),
    border: 'none',
    borderTop: `1px solid ${theme.palette.divider}`,
  },
}));

// 标签面板组件
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`report-tabpanel-${index}`}
      aria-labelledby={`report-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function ReportPage() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [regenerating, setRegenerating] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [s3DownloadLoading, setS3DownloadLoading] = useState(false);

  // 获取报告数据
  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        const data = await getReport(reportId);
        setReport(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching report:', err);
        setError('无法加载报告数据。请稍后再试。');
        setLoading(false);
      }
    };

    fetchReport();
  }, [reportId]);

  // 处理标签切换
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // 处理报告重新生成
  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      const data = await regenerateReport(reportId);
      setReport(data);
      setRegenerating(false);
    } catch (err) {
      console.error('Error regenerating report:', err);
      setError('重新生成报告失败。请稍后再试。');
      setRegenerating(false);
    }
  };

  // 处理S3文件下载
  const handleS3Download = async () => {
    try {
      setS3DownloadLoading(true);
      await downloadS3File(reportId);
      setS3DownloadLoading(false);
    } catch (err) {
      console.error('Error downloading S3 file:', err);
      setError('下载S3文件失败。请稍后再试。');
      setS3DownloadLoading(false);
    }
  };

  // 处理模型比较
  const handleCompare = () => {
    navigate(`/compare/${reportId}`);
  };

  // 处理设置调整
  const handleSettings = () => {
    navigate(`/settings/${reportId}`);
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

  if (!report) {
    return (
      <Container>
        <Typography variant="h6">Report not found</Typography>
      </Container>
    );
  }

  return (
    <Container>
      <StyledPaper elevation={3}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            レポート詳細
          </Typography>
          <Box>
            <Button
              variant="contained"
              color="primary"
              startIcon={<DownloadIcon />}
              onClick={handleS3Download}
              disabled={s3DownloadLoading}
              sx={{ mr: 1 }}
            >
              {s3DownloadLoading ? 'ダウンロード中...' : '原ファイルをダウンロード'}
            </Button>
          </Box>
        </Box>
        {/* 报告标题 */}
        <Typography variant="h4" gutterBottom>
          {report.title}
        </Typography>
        
        {/* 报告元数据 */}
        <Typography variant="body2" color="textSecondary" gutterBottom>
          Created: {new Date(new Date(report.created_at).getTime() + 9*60*60*1000).toLocaleString('ja-JP')}
        </Typography>
        
        {/* 报告摘要 */}
        <Box my={3}>
          <Typography variant="h6" gutterBottom>
            要約
          </Typography>
          <Typography variant="body1">
            <ReactMarkdown>{report.summary}</ReactMarkdown>
          </Typography>
        </Box>
        
        <Divider />
        
        {/* 报告详细内容 */}
        <Box mt={3}>
          <Typography variant="h6" gutterBottom>
            詳細内容
          </Typography>
          <MarkdownContainer>
            <ReactMarkdown>{report.content}</ReactMarkdown>
          </MarkdownContainer>
        </Box>
      </StyledPaper>
    </Container>
  );
}

export default ReportPage; 