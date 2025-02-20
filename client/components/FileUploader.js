import React, { useState } from 'react';
import { Box, Button, Typography, Paper, CircularProgress } from '@mui/material';
import axios from 'axios';

export default function FileUploader() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  // Read the backend URL from the environment variable
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  // Handle multiple file selection
  const handleFileSelect = (event) => {
    setSelectedFiles(Array.from(event.target.files));
  };

  // Upload all selected PDFs
  const handleUpload = async () => {
    if (!selectedFiles.length) return;
    setUploading(true);
    setUploadStatus('');

    try {
      // Upload each file one by one (you could also do this in parallel)
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(`${backendUrl}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        console.log('Uploaded:', file.name, response.data);
      }
      setUploadStatus('All files uploaded successfully!');
    } catch (error) {
      console.error(error);
      setUploadStatus('Upload failed. Check console for details.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Paper sx={{ padding: '1rem' }} elevation={3}>
      <Typography variant="h6">Upload Your PDFs</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ marginTop: '0.5rem' }}>
        You can select multiple PDFs at once.
      </Typography>
      <Box mt={2}>
        <input
          multiple
          type="file"
          accept="application/pdf"
          onChange={handleFileSelect}
          style={{ marginBottom: '1rem' }}
        />
        <br />
        <Button variant="contained" onClick={handleUpload} disabled={!selectedFiles.length || uploading}>
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
        {uploading && <CircularProgress size={24} sx={{ ml: 2 }} />}
      </Box>
      {uploadStatus && (
        <Typography variant="body1" sx={{ mt: 2 }}>
          {uploadStatus}
        </Typography>
      )}
    </Paper>
  );
}
