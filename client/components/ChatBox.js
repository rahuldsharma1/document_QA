import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Paper, CircularProgress, List, ListItem, ListItemText, Divider } from '@mui/material';
import axios from 'axios';

export default function ChatBox() {
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loadingAnswer, setLoadingAnswer] = useState(false);

  // Read the backend URL from the environment variable
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  const handleSendQuestion = async () => {
    if (!question.trim()) return;

    // Add the user question to the conversation
    setConversation((prev) => [...prev, { sender: 'user', message: question }]);
    const currentQuestion = question;
    setQuestion('');
    setLoadingAnswer(true);

    try {
      const formData = new FormData();
      formData.append('question', currentQuestion);

      const response = await axios.post(`${backendUrl}/query`, formData);
      const { answer, sources } = response.data;

      // Append the AI's answer to the conversation
      setConversation((prev) => [
        ...prev,
        { sender: 'ai', message: answer, sources },
      ]);
    } catch (error) {
      console.error(error);
      setConversation((prev) => [
        ...prev,
        { sender: 'ai', message: 'Error: could not get a response.' },
      ]);
    } finally {
      setLoadingAnswer(false);
    }
  };

  return (
    <Paper sx={{ padding: '1rem' }} elevation={3}>
      <Typography variant="h6">Ask a Question</Typography>
      <Box mt={2} sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          label="Type your question..."
          variant="outlined"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button variant="contained" onClick={handleSendQuestion} disabled={loadingAnswer}>
          {loadingAnswer ? 'Thinking...' : 'Send'}
        </Button>
      </Box>
      <Box
        sx={{
          border: '1px solid #ddd',
          borderRadius: '4px',
          marginTop: '1rem',
          padding: '1rem',
          height: '300px',
          overflowY: 'auto',
        }}
      >
        {conversation.map((msg, idx) => (
          <Box key={idx} sx={{ marginBottom: '1rem' }}>
            <Typography variant="body1" sx={{ fontWeight: 'bold', color: msg.sender === 'user' ? 'blue' : 'green' }}>
              {msg.sender === 'user' ? 'You:' : 'AI:'}
            </Typography>
            <Typography variant="body1">{msg.message}</Typography>
            {msg.sources && msg.sources.length > 0 && (
              <List dense>
                {msg.sources.map((src, sIdx) => (
                  <React.Fragment key={sIdx}>
                    <ListItem>
                      <ListItemText
                        primary={`Source: ${src.filename} (chunk #${src.chunk_index + 1})`}
                        secondary={src.text?.slice(0, 80) + '...'}
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            )}
          </Box>
        ))}
      </Box>
    </Paper>
  );
}
