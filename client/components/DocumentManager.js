import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Divider
} from '@mui/material';
import axios from 'axios';

export default function DocumentManager() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [previewText, setPreviewText] = useState('');

  // Read the backend URL from your .env.local
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  /**
   * Handle file selection from the user.
   */
  const handleFileSelect = (event) => {
    setSelectedFiles(Array.from(event.target.files));
  };

  /**
   * Upload all selected PDF files to the backend.
   */
  const handleUpload = async () => {
    if (!selectedFiles.length) return;
    setUploading(true);
    setUploadStatus('');

    try {
      const newDocs = [];
      // Upload each file sequentially (you could also do parallel if desired)
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        // Send POST request to backend /upload endpoint
        const response = await axios.post(`${backendUrl}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        console.log('Uploaded:', file.name, response.data);

        newDocs.push({
          fileName: file.name,
          fileId: response.data.file_id,
          preview: response.data.preview
        });
      }
      // Update local state with newly uploaded docs
      setUploadedDocs((prev) => [...prev, ...newDocs]);
      setUploadStatus('All files uploaded successfully!');
    } catch (error) {
      console.error(error);
      setUploadStatus('Upload failed. Check console for details.');
    } finally {
      setUploading(false);
      setSelectedFiles([]); // Clear the file selection
    }
  };

  /**
   * Delete a document from Pinecone (and local UI state).
   */
  const handleDelete = async (fileId) => {
    try {
      // Call DELETE endpoint to remove vectors from Pinecone
      await axios.delete(`${backendUrl}/delete`, {
        headers: { 'Content-Type': 'application/json' },
        data: { doc_id: fileId }
      });
      // Remove the doc from local state
      setUploadedDocs((prev) => prev.filter(doc => doc.fileId !== fileId));
      setPreviewText('');
    } catch (error) {
      console.error("Delete failed:", error);
    }
  };

  return (
    <Paper sx={{ padding: 2, borderRadius: 2 }} elevation={3}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Document Upload & Management
      </Typography>

      {/* File Selection */}
      <Box mt={1}>
        <input
          type="file"
          accept="application/pdf"
          multiple
          onChange={handleFileSelect}
        />
      </Box>

      {/* Upload Button & Status */}
      <Box mt={1}>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={uploading || !selectedFiles.length}
          sx={{ borderRadius: 2 }}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
        {uploading && <LinearProgress sx={{ mt: 1 }} />}
      </Box>
      {uploadStatus && (
        <Typography variant="body2" sx={{ mt: 1 }}>
          {uploadStatus}
        </Typography>
      )}

      {/* Uploaded Documents List */}
      <Box mt={2}>
        <Typography variant="subtitle1">Uploaded Files:</Typography>
        {uploadedDocs.length === 0 ? (
          <Typography variant="body2">No files uploaded.</Typography>
        ) : (
          <List dense>
            {uploadedDocs.map((doc, idx) => (
              <ListItem
                key={idx}
                // Show a preview snippet on hover
                onMouseEnter={() => setPreviewText(doc.preview)}
                onMouseLeave={() => setPreviewText('')}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start'
                }}
              >
                {/* File Name & ID */}
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {doc.fileName}
                </Typography>
                <Typography variant="body2">
                  ID: {doc.fileId}
                </Typography>

                {/* Buttons BELOW file name and ID */}
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => handleDelete(doc.fileId)}
                    sx={{ borderRadius: 2 }}
                  >
                    Delete
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    href={`${backendUrl}/download?doc_id=${doc.fileId}&filename=${encodeURIComponent(doc.fileName)}`}
                    target="_blank"
                    sx={{ borderRadius: 2 }}
                  >
                    Download
                  </Button>
                </Box>
              </ListItem>
            ))}
            <Divider />
          </List>
        )}
      </Box>

      {/* Preview Box (shows snippet from backend) */}
      {previewText && (
        <Box mt={2} sx={{ backgroundColor: '#f5f5f5', padding: 1, borderRadius: 2 }}>
          <Typography variant="subtitle2">Preview:</Typography>
          <Typography variant="body2">{previewText}</Typography>
        </Box>
      )}
    </Paper>
  );
}
