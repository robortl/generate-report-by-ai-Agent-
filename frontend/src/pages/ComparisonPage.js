import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Divider,
  TextField,
  Card,
  CardContent,
} from '@mui/material';
import { compareModels, getFiles, getModels } from '../services/api';
import MarkdownRenderer from '../components/MarkdownRenderer';

function ComparisonPage() {
  const [files, setFiles] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [selectedModels, setSelectedModels] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [comparisonResults, setComparisonResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('ComparisonPage: Fetching files and models');
        const filesResponse = await getFiles();
        setFiles(filesResponse.items || []);
        console.log('Files loaded:', filesResponse.items || []);

        // Get models and log the response structure
        const modelsResponse = await getModels();
        console.log('Models response from API:', modelsResponse);
        
        // Check if models is directly an array or needs to be accessed via .items
        const modelsData = Array.isArray(modelsResponse) ? modelsResponse : (modelsResponse.items || []);
        console.log('Processed models data:', modelsData);
        
        setModels(modelsData);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('ファイルまたはモデルデータを読み込めません。後で再試行してください。');
      }
    };

    fetchData();
  }, []);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.value);
  };

  const handleModelChange = (event) => {
    setSelectedModels(event.target.value);
  };

  const handlePromptChange = (event) => {
    setPrompt(event.target.value);
  };

  const handleCompare = async () => {
    if (!selectedFile || selectedModels.length < 2) {
      setError('ファイルと少なくとも二つのモデルを選択してください。');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('Comparing models with file:', selectedFile, 'and models:', selectedModels, 'prompt:', prompt);
      const results = await compareModels(selectedFile, selectedModels, prompt);
      console.log('Comparison results:', results);
      
      // Validate the results structure before setting state
      if (!results) {
        throw new Error('比較結果が空です');
      }
      
      // Ensure results has a comparisons property that is an array
      if (!results.comparisons || !Array.isArray(results.comparisons)) {
        console.error('Missing or invalid comparisons array in results:', results);
        results.comparisons = []; // Initialize with empty array if missing
      }
      
      setComparisonResults(results);
    } catch (err) {
      console.error('Error comparing models:', err);
      setError(err.message || 'モデルの比較中にエラーが発生しました。後で再試行してください。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        モデル比較
      </Typography>
      <Typography variant="body1" paragraph>
        ファイルと複数のモデルを選択して比較し、異なるモデルによって生成されたレポートの違いを確認します。
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="file-select-label">ファイル選択</InputLabel>
              <Select
                labelId="file-select-label"
                id="file-select"
                value={selectedFile}
                label="ファイル選択"
                onChange={handleFileChange}
              >
                {files.map((file) => (
                  <MenuItem key={file.file_id} value={file.file_id}>
                    {file.original_filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="model-select-label">モデル選択（複数選択可）</InputLabel>
              <Select
                labelId="model-select-label"
                id="model-select"
                multiple
                value={selectedModels}
                label="モデル選択（複数選択可）"
                onChange={handleModelChange}
              >
                {models.length > 0 ? (
                  models.map((model) => {
                    // 各モデルの構造をログに記録
                    console.log('Rendering model:', model);
                    // プロパティ名を実際のデータに基づいて使用
                    const modelId = model.id || model.model_id;
                    const modelName = model.name || model.model_name;
                    // モデルIDをモデル名の後に追加
                    const displayName = `${modelName} (${modelId})`;
                    return (
                      <MenuItem key={modelId} value={modelId}>
                        {displayName}
                      </MenuItem>
                    );
                  })
                ) : (
                  <MenuItem disabled>利用可能なモデルがありません</MenuItem>
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="プロンプト（オプション）"
              placeholder="モデル生成をガイドするプロンプトを入力してください..."
              multiline
              rows={3}
              fullWidth
              value={prompt}
              onChange={handlePromptChange}
              margin="normal"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleCompare}
              disabled={loading || !selectedFile || selectedModels.length < 2}
            >
              {loading ? <CircularProgress size={24} /> : 'モデルを比較'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {comparisonResults && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            比較結果
          </Typography>
          <Divider sx={{ mb: 2 }} />

          {comparisonResults.comparisons && Array.isArray(comparisonResults.comparisons) && comparisonResults.comparisons.length > 0 ? (
            // 左右レイアウトで比较結果を表示
            <Box sx={{ mb: 4 }}>
              {comparisonResults.comparisons.map((comparison, index) => {
                // 最初の要素または偶数インデックスの場合、新しいGrid行を開始
                const startNewRow = index === 0 || index % 2 === 0;
                // 行の開始要素の場合
                if (startNewRow) {
                  return (
                    <React.Fragment key={index}>
                      {index > 0 && <Divider sx={{ my: 4 }} />} {/* 各比較ペアの間に区切り線を追加 */}
                      <Grid container spacing={3}>
                        {/* 現在のモデル */}
                        <Grid item xs={12} md={6}>
                          <Card variant="outlined" sx={{ height: '100%' }}>
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                {comparison.model_name || '不明モデル'}
                              </Typography>
                              <Divider sx={{ mb: 2 }} />
                              {comparison.content ? (
                                <MarkdownRenderer content={comparison.content} />
                              ) : (
                                <Typography variant="body1">コンテンツなし</Typography>
                              )}
                            </CardContent>
                          </Card>
                        </Grid>
                        
                        {/* 次の比较項目があれば、右側に表示 */}
                        {index + 1 < comparisonResults.comparisons.length && (
                          <Grid item xs={12} md={6}>
                            <Card variant="outlined" sx={{ height: '100%' }}>
                              <CardContent>
                                <Typography variant="h6" gutterBottom>
                                  {comparisonResults.comparisons[index + 1].model_name || '不明モデル'}
                                </Typography>
                                <Divider sx={{ mb: 2 }} />
                                {comparisonResults.comparisons[index + 1].content ? (
                                  <MarkdownRenderer content={comparisonResults.comparisons[index + 1].content} />
                                ) : (
                                  <Typography variant="body1">コンテンツなし</Typography>
                                )}
                              </CardContent>
                            </Card>
                          </Grid>
                        )}
                      </Grid>
                    </React.Fragment>
                  );
                }
                // 奇数インデックスの場合、前のコンポーネントですでに処理されているため、何もレンダリングしない
                return null;
              })}
            </Box>
          ) : (
            <Typography variant="body1" sx={{ mb: 3 }}>
              比較データが利用可能ではありません
            </Typography>
          )}

          <Typography variant="h6" gutterBottom>
            差異分析
          </Typography>
          {comparisonResults.analysis ? (
            <MarkdownRenderer content={comparisonResults.analysis} />
          ) : (
            <Typography variant="body1">
              差異分析データなし
            </Typography>
          )}
        </Paper>
      )}
    </Box>
  );
}

export default ComparisonPage; 