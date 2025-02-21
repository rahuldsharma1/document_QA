import React, { useState } from 'react';
import { Paper, Typography } from '@mui/material';

export default function ReferenceItem({ reference }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Paper
      elevation={2}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      sx={{
        padding: 1,
        marginBottom: 1,
        cursor: 'pointer',
        transition: 'all 0.3s ease-in-out',
        borderRadius: 2,
      }}
    >
      <Typography variant="subtitle2">
        {reference.filename} (chunk #{reference.chunk_index + 1})
      </Typography>
      {expanded ? (
        <Typography variant="body2">{reference.text}</Typography>
      ) : (
        <Typography variant="body2">
          {reference.text && reference.text.length > 80 ? reference.text.slice(0, 80) + '...' : reference.text}
        </Typography>
      )}
    </Paper>
  );
}
