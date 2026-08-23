import { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import DataIngestion from './components/DataIngestion';
import Dashboard from './components/Dashboard';
import HumanReview from './components/HumanReview';
import CatalogGrid from './components/CatalogGrid';

export type Page = 'upload' | 'dashboard' | 'review' | 'catalog';
export type AppState = 'idle' | 'processing' | 'done';

export interface EnrichmentResult {
  rows: any[];
  stats: any;
  columns: string[];
}

export default function App() {
  const [page, setPage] = useState<Page>('upload');
  const [appState, setAppState] = useState<AppState>('idle');
  const [result, setResult] = useState<EnrichmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState('');

  const handleUploadComplete = useCallback((data: EnrichmentResult, name: string) => {
    setResult(data);
    setFileName(name);
    setAppState('done');
    setPage('dashboard');
  }, []);

  const handleError = useCallback((msg: string) => {
    setError(msg);
  }, []);

  const handleReset = useCallback(() => {
    setAppState('idle');
    setResult(null);
    setError(null);
    setFileName('');
    setPage('upload');
  }, []);

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      <Sidebar page={page} setPage={setPage} hasData={appState === 'done'} totalProducts={result?.rows?.length} accuracy={result?.stats?.conf_avg} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNav fileName={fileName} appState={appState} onReset={handleReset} accuracy={result?.stats?.accuracy} />
        <main className="flex-1 overflow-auto">
          {page === 'upload' && (
            <DataIngestion
              onUploadComplete={handleUploadComplete}
              onError={handleError}
              error={error}
              appState={appState}
              setAppState={setAppState}
            />
          )}
          {page === 'dashboard' && result && <Dashboard stats={result.stats} rows={result.rows} />}
          {page === 'review' && result && <HumanReview onUpdate={(stats) => setResult({ ...result, stats })} />}
          {page === 'catalog' && result && <CatalogGrid rows={result.rows} columns={result.columns} />}
        </main>
      </div>
    </div>
  );
}
