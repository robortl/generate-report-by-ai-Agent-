import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Description as ReportIcon,
} from '@mui/icons-material';
import { uploadFile, getCategories, generateReport, getFiles } from '../services/api';

function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [recentFiles, setRecentFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(true);

  // カテゴリリストの取得
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await getCategories();
        setCategories(data);
        if (data.length > 0) {
          setCategory(data[0].id);
        }
      } catch (err) {
        console.error('Error fetching categories:', err);
        setError('ファイルカテゴリを読み込めませんでした。後でもう一度お試しください。');
      }
    };

    const fetchRecentFiles = async () => {
      try {
        setLoadingFiles(true);
        const response = await getFiles(null, 10);
        setRecentFiles(response.items || []);
        setLoadingFiles(false);
      } catch (err) {
        console.error('Error fetching recent files:', err);
        setLoadingFiles(false);
      }
    };

    fetchCategories();
    fetchRecentFiles();
  }, []);

  // ファイル選択の処理
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError(null);
    }
  };

  // カテゴリ選択の処理
  const handleCategoryChange = (event) => {
    setCategory(event.target.value);
  };

  // ファイルアップロードの処理
  const handleUpload = async () => {
    if (!file) {
      setError('アップロードするファイルを選択してください');
      return;
    }

    if (!category) {
      setError('ファイルカテゴリを選択してください');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);

      // ファイルのアップロード
      const uploadResponse = await uploadFile(file, category);
      setSuccess('ファイルのアップロードに成功しました！');

      // レポートの自動生成
      setLoading(true);
      const reportResponse = await generateReport(uploadResponse.file_id);
      setLoading(false);

      // レポートページへ移動
      navigate(`/report/${reportResponse.report_id}`);
    } catch (err) {
      console.error('Error uploading file:', err);
      setError('ファイルのアップロードに失敗しました。後でもう一度お試しください。');
      setUploading(false);
      setLoading(false);
    }
  };

  // ファイルクリックの処理
  const handleFileClick = (file) => {
    if (file.report_id) {
      navigate(`/report/${file.report_id}`);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        ファイルアップロード
      </Typography>

      <Grid container spacing={3}>
        {/* アップロードフォーム */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ファイルを選択
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}

            <Box sx={{ mb: 3 }}>
              <Button
                variant="contained"
                component="label"
                startIcon={<UploadIcon />}
                fullWidth
                sx={{ py: 1.5, mb: 2 }}
              >
                ファイルを選択
                <input
                  type="file"
                  hidden
                  accept=".txt,.pdf,.doc,.docx,.md"
                  onChange={handleFileChange}
                />
              </Button>

              {fileName && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    p: 2,
                    border: '1px dashed #ccc',
                    borderRadius: 1,
                  }}
                >
                  <FileIcon sx={{ mr: 1 }} />
                  <Typography variant="body2" noWrap>
                    {fileName}
                  </Typography>
                </Box>
              )}
            </Box>

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel id="category-label">ファイルカテゴリ</InputLabel>
              <Select
                labelId="category-label"
                value={category}
                label="ファイルカテゴリ"
                onChange={handleCategoryChange}
              >
                {categories.map((cat) => (
                  <MenuItem key={cat.id} value={cat.id}>
                    {cat.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant="contained"
              color="primary"
              onClick={handleUpload}
              disabled={!file || uploading || loading}
              fullWidth
              sx={{ py: 1.5 }}
            >
              {uploading ? (
                <CircularProgress size={24} sx={{ mr: 1 }} />
              ) : (
                <UploadIcon sx={{ mr: 1 }} />
              )}
              {uploading ? 'アップロード中...' : 'アップロードしてレポートを生成'}
            </Button>

            {loading && (
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <CircularProgress size={24} sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  レポートを生成中です、お待ちください...
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* 最近のファイルリスト */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                最近アップロードしたファイル
              </Typography>

              {loadingFiles ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : recentFiles.length > 0 ? (
                <List>
                  {recentFiles.map((file) => (
                    <React.Fragment key={file.file_id}>
                      <ListItem
                        button
                        onClick={() => handleFileClick(file)}
                        disabled={!file.report_id}
                      >
                        <ListItemIcon>
                          {file.report_id ? <ReportIcon /> : <FileIcon />}
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
                  最近アップロードしたファイルはありません。
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default UploadPage; 