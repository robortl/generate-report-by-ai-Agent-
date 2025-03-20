import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Box, Typography } from '@mui/material';

// 自定义Markdown渲染组件
const MarkdownRenderer = ({ content }) => {
  if (!content) {
    return <Typography variant="body1">无内容</Typography>;
  }

  return (
    <Box sx={{ 
      '& h1': { fontSize: '1.8rem', fontWeight: 600, my: 2 },
      '& h2': { fontSize: '1.6rem', fontWeight: 600, my: 2 },
      '& h3': { fontSize: '1.4rem', fontWeight: 600, my: 1.5 },
      '& h4': { fontSize: '1.2rem', fontWeight: 600, my: 1.5 },
      '& h5': { fontSize: '1.1rem', fontWeight: 600, my: 1 },
      '& h6': { fontSize: '1rem', fontWeight: 600, my: 1 },
      '& p': { my: 1.5, lineHeight: 1.6 },
      '& ul, & ol': { pl: 4, my: 1.5 },
      '& li': { mb: 0.5 },
      '& blockquote': { 
        borderLeft: '4px solid #9e9e9e', 
        pl: 2, 
        py: 0.5, 
        my: 1.5,
        backgroundColor: 'rgba(0, 0, 0, 0.03)'
      },
      '& a': {
        color: 'primary.main',
        textDecoration: 'none',
        '&:hover': {
          textDecoration: 'underline'
        }
      },
      '& table': {
        borderCollapse: 'collapse',
        width: '100%',
        my: 2
      },
      '& th, & td': {
        border: '1px solid #e0e0e0',
        padding: '8px 16px',
        textAlign: 'left'
      },
      '& th': {
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        fontWeight: 600
      },
      '& pre': {
        my: 1.5,
        p: 0,
        borderRadius: 1,
        overflow: 'auto'
      },
      '& code': {
        fontFamily: 'monospace',
        fontSize: '0.9em',
        px: 0.5,
        py: 0.25,
        borderRadius: 0.5,
        backgroundColor: 'rgba(0, 0, 0, 0.04)'
      }
    }}>
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={materialDark}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );
};

export default MarkdownRenderer;
