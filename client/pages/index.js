import React from 'react';
import { Box, Typography } from '@mui/material';
import FileUploader from '../components/FileUploader';
import ChatBox from '../components/ChatBox';

export default function HomePage() {
  return (
    <Box
      sx={{
        maxWidth: '900px',
        margin: '0 auto',
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}
    >
      <Typography variant="h4" textAlign="center">
        Document Q&A Agent
      </Typography>
      <FileUploader />
      <ChatBox />
    </Box>
  );
}
