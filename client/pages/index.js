import React, { useState } from 'react';
import { Grid, Box, Typography } from '@mui/material';
import DocumentManager from '../components/DocumentManager';
import ChatBox from '../components/ChatBox';
import ReferencesPanel from '../components/ReferencesPanel';

export default function HomePage() {
  const [references, setReferences] = useState([]);

  return (
    <Box sx={{ flexGrow: 1, padding: 2 }}>
      <Typography variant="h4" textAlign="center" sx={{ mb: 3 }}>
        DocuDive!
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <DocumentManager />
        </Grid>
        <Grid item xs={12} md={6}>
          <ChatBox onNewResponse={setReferences} />
        </Grid>
        <Grid item xs={12} md={3}>
          <ReferencesPanel references={references} />
        </Grid>
      </Grid>
    </Box>
  );
}
