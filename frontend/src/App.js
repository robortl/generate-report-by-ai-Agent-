import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import ReportPage from './pages/ReportPage';
import ReportsPage from './pages/ReportsPage';
import ComparisonPage from './pages/ComparisonPage';
import ComparePage from './pages/ComparePage';
import PromptPage from './pages/PromptPage';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

// 创建主题
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(','),
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/report/:reportId" element={<ReportPage />} />
            <Route path="/compare" element={<ComparisonPage />} />
            <Route path="/compare/:reportId" element={<ComparePage />} />
            <Route path="/prompt" element={<PromptPage />} />
          </Routes>
        </Layout>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App; 