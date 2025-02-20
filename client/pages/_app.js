import * as React from 'react';
import Head from 'next/head';
import { ThemeProvider, CssBaseline, createTheme } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'light'
  }
});

export default function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>Document Q&A Agent</title>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
      </Head>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Component {...pageProps} />
      </ThemeProvider>
    </>
  );
}
