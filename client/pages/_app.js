import * as React from 'react';
import Head from 'next/head';
import { ThemeProvider, CssBaseline, createTheme } from '@mui/material';

const theme = createTheme({
  typography: {
    fontFamily: "'Poppins', sans-serif",
  },
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
    background: { default: '#f7f7f7' },
  },
  shape: {
    borderRadius: 12,
  },
});

export default function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>Document Q&A Agent</title>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
        {/* Load Poppins from Google Fonts */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet" />
      </Head>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Component {...pageProps} />
      </ThemeProvider>
    </>
  );
}
