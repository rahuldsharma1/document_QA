import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, Button, Typography, Paper, CircularProgress, List, ListItem, ListItemText, Divider } from '@mui/material';
import axios from 'axios';

export default function ChatBox({ onNewResponse }) {
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  const chatEndRef = useRef(null);
  const scrollToBottom = () => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSendQuestion = async () => {
    if (!question.trim()) return;
    // Append user's question to conversation
    setConversation((prev) => [...prev, { sender: 'user', message: question }]);
    const currentQuestion = question;
    setQuestion('');
    setLoadingAnswer(true);

    try {
      const formData = new FormData();
      formData.append('question', currentQuestion);
      const response = await axios.post(`${backendUrl}/query`, formData);
      const { answer, sources } = response.data;
      setConversation((prev) => [...prev, { sender: 'ai', message: answer, sources }]);
      if (onNewResponse) {
        onNewResponse(sources && sources.length > 0 ? sources : []);
      }
    } catch (error) {
      console.error(error);
      setConversation((prev) => [...prev, { sender: 'ai', message: 'Error: could not get a response.' }]);
      if (onNewResponse) {
        onNewResponse([]);
      }
    } finally {
      setLoadingAnswer(false);
    }
  };

  // Trigger send when user hits Enter (without Shift)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendQuestion();
    }
  };

  return (
    <Paper sx={{ padding: 2, height: '80vh', display: 'flex', flexDirection: 'column', borderRadius: 2 }} elevation={3}>
      <Typography variant="h6">Chat</Typography>
      <Box sx={{ flexGrow: 1, overflowY: 'auto', mt: 1, mb: 1 }}>
        {conversation.map((msg, idx) => (
          <Box key={idx} sx={{ mb: 2 }}>
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
        <div ref={chatEndRef} />
      </Box>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          label="Type your question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          sx={{ borderRadius: 2 }}
        />
        <Button variant="contained" onClick={handleSendQuestion} disabled={loadingAnswer} sx={{ borderRadius: 2 }}>
          {loadingAnswer ? <CircularProgress size={24} /> : 'Send'}
        </Button>
      </Box>
    </Paper>
  );
}
