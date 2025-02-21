import React from 'react';
import { Paper, Typography, Box, List } from '@mui/material';
import ReferenceItem from './ReferenceItem';

export default function ReferencesPanel({ references }) {
  return (
    <Paper sx={{ padding: 2, height: '80vh', overflowY: 'auto', borderRadius: 2 }} elevation={3}>
      <Typography variant="h6">References</Typography>
      {references && references.length > 0 ? (
        <List>
          {references.map((ref, idx) => (
            <ReferenceItem key={idx} reference={ref} />
          ))}
        </List>
      ) : (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">No relevant references.</Typography>
        </Box>
      )}
    </Paper>
  );
}
