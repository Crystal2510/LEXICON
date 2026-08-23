import { useCallback, useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileSpreadsheet, CheckCircle, Zap, AlertCircle, Eye, Loader2, Database } from 'lucide-react';
import { previewCSV, enrichCSV, uploadReferenceFiles } from '../api';
import type { EnrichmentResult, AppState } from '../App';

interface Props {
  onUploadComplete: (data: EnrichmentResult, name: string) => void;
  onError: (msg: string) => void;
  error: string | null;
  appState: AppState;
  setAppState: (s: AppState) => void;
}

interface PreviewData {
  columns: string[];
  total_rows: number;
  preview: Record<string, string>[];
}

interface LiveFeedItem {
  id: string;
  name: string;
  category: string;
  confidence: number;
  timestamp: number;
}

const PIPELINE_STEPS = [
  { key: 'csv', label: 'CSV' },
  { key: 'parse', label: 'Parse' },
  { key: 'brand', label: 'Brand' },
  { key: 'classify', label: 'Classify' },
  { key: 'generate', label: 'Generate' },
  { key: 'done', label: 'Done' },
];

const MOCK_FEED: Omit<LiveFeedItem, 'timestamp'>[] = [
  { id: 'DCF887B', name: 'DeWalt Impact Driver', category: 'Power Tools>Drivers', confidence: 93 },
  { id: 'MIL2241', name: 'Milwaukee M18 Drill', category: 'Power Tools>Drills', confidence: 91 },
  { id: 'BOS192K', name: 'Bosch Circular Saw 7-1/4', category: 'Power Tools>Saws', confidence: 88 },
  { id: 'MAKTD001', name: 'Makita 18V LXT Recip Saw', category: 'Power Tools>Saws', confidence: 95 },
  { id: 'HRG5620', name: 'Hilti TE 6 Rotary Hammer', category: 'Power Tools>Demolition', confidence: 87 },
];

export default function DataIngestion({ onUploadComplete, onError, error, appState, setAppState }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [previewExpanded, setPreviewExpanded] = useState(true);
  const [loading, setLoading] = useState(false);
  const [processStep, setProcessStep] = useState(0);
  const [deepSourcing, _setDeepSourcing] = useState(true);
  const [liveFeed, setLiveFeed] = useState<LiveFeedItem[]>([]);
  const [_rowsProcessed, setRowsProcessed] = useState(0);
  const [refFiles, setRefFiles] = useState<File[]>([]);
  const [refUploadStatus, setRefUploadStatus] = useState<string>('');
  const [refDragging, setRefDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const refInputRef = useRef<HTMLInputElement>(null);

  const totalRows = preview?.total_rows ?? 0;

  useEffect(() => {
    if (appState !== 'processing') return;
    setProcessStep(0);
    setRowsProcessed(0);
    setLiveFeed([]);

    const timers: ReturnType<typeof setTimeout>[] = [];
    const stepDuration = 2500;

    PIPELINE_STEPS.forEach((_, i) => {
      timers.push(setTimeout(() => setProcessStep(i), i * stepDuration));
    });

    let rowIdx = 0;
    const feedTimer = setInterval(() => {
      if (rowIdx >= Math.min(5, totalRows || 5)) {
        clearInterval(feedTimer);
        return;
      }
      const mock = MOCK_FEED[rowIdx % MOCK_FEED.length];
      setLiveFeed(prev => [...prev, { ...mock, timestamp: Date.now() }].slice(-5));
      setRowsProcessed(rowIdx + 1);
      rowIdx++;
    }, 1800);

    return () => {
      timers.forEach(clearTimeout);
      clearInterval(feedTimer);
    };
  }, [appState, totalRows]);

  const handleFile = useCallback(async (f: File) => {
    if (!f.name.endsWith('.csv')) {
      onError('Only CSV files are supported');
      return;
    }
    setFile(f);
    setLoading(true);
    onError('');
    try {
      const data = await previewCSV(f);
      setPreview(data);
    } catch (err: any) {
      onError(err.message || 'Failed to preview file');
    } finally {
      setLoading(false);
    }
  }, [onError]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files?.[0]) handleFile(files[0]);
  }, [handleFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files?.[0]) handleFile(files[0]);
  }, [handleFile]);

  const handleProcess = useCallback(async () => {
    if (!file) return;
    setAppState('processing');
    onError('');
    try {
      const data = await enrichCSV(file, deepSourcing);
      onUploadComplete(data, file.name);
    } catch (err: any) {
      onError(err.message || 'Failed to process');
      setAppState('idle');
    }
  }, [file, onUploadComplete, onError, setAppState]);

  const handleReset = useCallback(() => {
    setFile(null);
    setPreview(null);
    setPreviewExpanded(false);
    onError('');
  }, [onError]);

  const isProcessing = appState === 'processing';
  const showPreview = preview && !isProcessing;

  return (
    <div className="h-full flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-4xl"
      >
        <div className="text-center mb-8">
          <h1 className="text-5xl font-black text-text mb-3 tracking-tight">Lexicon</h1>
          <p className="text-base text-muted">AI-powered product data enrichment for your catalog</p>
        </div>

        {!showPreview ? (
          <div
            className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer ${
              isDragging
                ? 'border-brand bg-brand-light shadow-lg shadow-brand/10'
                : 'border-border hover:border-gray-400 hover:bg-gray-50'
            } ${isProcessing ? 'pointer-events-none opacity-60' : ''}`}
            onDragEnter={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => !isProcessing && inputRef.current?.click()}
          >
            <input ref={inputRef} type="file" accept=".csv" className="hidden" onChange={handleFileInput} />
            <div className="p-16 flex flex-col items-center gap-5">
              {isProcessing ? (
                <div className="flex flex-col items-center gap-6 w-full max-w-3xl">
                  <div className="w-full">
                    <div className="flex items-center justify-between">
                      {PIPELINE_STEPS.map((step, i) => {
                        const isCompleted = i < processStep;
                        const isActive = i === processStep && processStep < PIPELINE_STEPS.length;
                        return (
                          <div key={step.key} className="flex items-center flex-1 last:flex-none">
                            <div className="flex flex-col items-center gap-1.5">
                              <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-500 border ${
                                isCompleted
                                  ? 'bg-green border-green text-white shadow-md shadow-green/20'
                                  : isActive
                                  ? 'bg-brand border-brand text-white animate-pulse shadow-lg shadow-brand/30'
                                  : 'bg-gray-50 border-gray-200 text-gray-300'
                              }`}>
                                {isCompleted ? (
                                  <CheckCircle className="w-5 h-5" />
                                ) : (
                                  <span className="text-xs font-bold">{i + 1}</span>
                                )}
                              </div>
                              <span className={`text-[10px] font-semibold tracking-wide ${
                                isCompleted ? 'text-green' : isActive ? 'text-brand' : 'text-gray-300'
                              }`}>
                                {step.label}
                              </span>
                            </div>
                            {i < PIPELINE_STEPS.length - 1 && (
                              <div className="flex-1 h-px mx-1.5 mt-[-14px]">
                                <div className={`h-0.5 rounded-full transition-all duration-700 ${
                                  i < processStep ? 'bg-green' : 'bg-gray-200'
                                }`} />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {liveFeed.length > 0 && (
                    <div className="w-full border border-border rounded-xl overflow-hidden bg-white">
                      <div className="px-3 py-2 bg-gray-50 border-b border-border flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
                        <span className="text-[10px] font-bold text-muted uppercase tracking-wider">Live Feed</span>
                      </div>
                      <div className="max-h-48 overflow-y-auto p-2 space-y-1">
                        <AnimatePresence mode="popLayout">
                          {liveFeed.map((item) => (
                            <motion.div
                              key={`${item.id}-${item.timestamp}`}
                              initial={{ opacity: 0, y: 20, scale: 0.95 }}
                              animate={{ opacity: 1, y: 0, scale: 1 }}
                              exit={{ opacity: 0, y: -10, scale: 0.95 }}
                              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-light/30 text-sm"
                            >
                              <CheckCircle className="w-3.5 h-3.5 text-green shrink-0" />
                              <span className="font-mono text-xs font-bold text-green">{item.id}</span>
                              <span className="text-text font-medium">{item.name}</span>
                              <span className="text-muted">&rarr;</span>
                              <span className="text-muted text-xs">{item.category}</span>
                              <span className="ml-auto text-xs font-mono text-brand font-bold">{item.confidence}%</span>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                      </div>
                    </div>
                  )}
                </div>
              ) : loading ? (
                <Loader2 className="w-10 h-10 text-brand animate-spin" />
              ) : (
                <>
                  <div className="w-20 h-20 rounded-2xl bg-brand/5 flex items-center justify-center">
                    <Upload className="w-9 h-9 text-brand/60" />
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-text mb-1">
                      Drop your distributor catalog here
                    </p>
                    <p className="text-sm text-muted">
                      Supports any CSV format &mdash; we&#39;ll auto-detect columns
                    </p>
                  </div>
                </>
              )}

              {!isProcessing && !loading && (
                <div className="flex items-center gap-5 text-xs text-muted mt-2">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                    256 output columns
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                    AI Classification
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                    Auto column mapping
                  </span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-border">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-light flex items-center justify-center">
                  <FileSpreadsheet className="w-5 h-5 text-green" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-text">{file?.name}</div>
                  <div className="text-xs text-muted">
                    {preview?.total_rows.toLocaleString()} rows &middot; {preview?.columns.length} columns detected
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  className="px-3 py-2 text-sm text-muted hover:text-text border border-border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Change File
                </button>
                <button
                  onClick={handleProcess}
                  className="px-5 py-2 bg-black text-white text-sm font-semibold rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2"
                >
                  <Zap className="w-4 h-4" />
                  Process & Enrich
                </button>
              </div>
            </div>

            {preview && (
              <div className="flex flex-wrap gap-1.5 px-1">
                {preview.columns.map((col) => (
                  <span
                    key={col}
                    className="px-2.5 py-1 bg-brand-light text-brand text-xs font-medium rounded-full border border-brand/20"
                  >
                    {col}
                  </span>
                ))}
              </div>
            )}

            <div className="bg-white rounded-xl border border-border overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-border bg-gray-50/50">
                <div className="flex items-center gap-2 text-sm font-semibold text-text">
                  <Eye className="w-4 h-4 text-muted" />
                  Dataset Preview
                  <span className="text-xs font-normal text-muted">(first 50 rows)</span>
                </div>
                <button
                  onClick={() => setPreviewExpanded(!previewExpanded)}
                  className="text-xs text-muted hover:text-text transition-colors"
                >
                  {previewExpanded ? 'Collapse' : 'Expand'}
                </button>
              </div>

              <AnimatePresence>
                {previewExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="overflow-x-auto max-h-96 overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="sticky top-0 bg-white border-b border-border">
                          <tr>
                            <th className="px-3 py-2.5 text-left text-[10px] font-bold text-muted uppercase w-10">#</th>
                            {preview?.columns.map((col) => (
                              <th key={col} className="px-3 py-2.5 text-left text-[10px] font-bold text-muted uppercase whitespace-nowrap">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {preview?.preview.map((row, idx) => (
                            <tr key={idx} className="border-b border-border/30 hover:bg-gray-50/50 transition-colors">
                              <td className="px-3 py-2 text-muted font-medium">{idx + 1}</td>
                              {preview.columns.map((col) => (
                                <td key={col} className="px-3 py-2 text-text max-w-[200px] truncate">
                                  {row[col] || <span className="text-gray-300">-</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        )}

        {!showPreview && !isProcessing && (
          <div className="mt-6 p-5 rounded-xl bg-white border border-border">
            <div className="flex items-center gap-3 mb-3">
              <Database className="w-4 h-4 text-muted" />
              <span className="text-sm font-semibold text-text">Reference Data (Optional)</span>
              {refFiles.length > 0 && (
                <span className="text-xs bg-brand-light text-brand px-2 py-0.5 rounded-full">{refFiles.length} files</span>
              )}
            </div>
            <p className="text-xs text-muted mb-3">Upload UniCat Excel files for higher accuracy. System works without them.</p>
            <div
              className={`border border-dashed rounded-lg p-4 text-center cursor-pointer transition-all ${
                refDragging ? 'border-brand bg-brand-light' : 'border-border hover:border-gray-400'
              }`}
              onDragEnter={(e) => { e.preventDefault(); setRefDragging(true); }}
              onDragLeave={(e) => { e.preventDefault(); setRefDragging(false); }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                setRefDragging(false);
                const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.xlsx') || f.name.endsWith('.xls'));
                if (files.length) setRefFiles(prev => [...prev, ...files]);
              }}
              onClick={() => refInputRef.current?.click()}
            >
              <input
                ref={refInputRef}
                type="file"
                accept=".xlsx,.xls"
                multiple
                className="hidden"
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  if (files.length) setRefFiles(prev => [...prev, ...files]);
                }}
              />
              <p className="text-xs text-muted">Drop Excel files here or click to browse</p>
            </div>
            {refFiles.length > 0 && (
              <div className="mt-3 space-y-1.5">
                {refFiles.map((f, i) => (
                  <div key={i} className="flex items-center justify-between text-xs bg-gray-50 rounded px-3 py-1.5">
                    <span className="text-text truncate">{f.name}</span>
                    <button onClick={() => setRefFiles(prev => prev.filter((_, j) => j !== i))} className="text-muted hover:text-red ml-2">x</button>
                  </div>
                ))}
                <button
                  onClick={async () => {
                    try {
                      setRefUploadStatus('uploading');
                      await uploadReferenceFiles(refFiles);
                      setRefUploadStatus('done');
                    } catch (err: any) {
                      setRefUploadStatus('error: ' + err.message);
                    }
                  }}
                  disabled={refUploadStatus === 'uploading'}
                  className="w-full mt-2 py-2 rounded-lg bg-brand text-white text-xs font-semibold hover:bg-brand-dark transition-colors disabled:opacity-50"
                >
                  {refUploadStatus === 'uploading' ? 'Uploading...' : refUploadStatus === 'done' ? 'Uploaded!' : 'Upload Reference Files'}
                </button>
                {refUploadStatus === 'done' && (
                  <p className="text-xs text-green-600 text-center">Files saved. Process CSV to use them.</p>
                )}
                {refUploadStatus.startsWith('error') && (
                  <p className="text-xs text-red text-center">{refUploadStatus}</p>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-3 p-4 rounded-xl bg-red-light border border-red/20"
          >
            <AlertCircle className="w-5 h-5 text-red shrink-0" />
            <span className="text-sm text-red">{error}</span>
          </motion.div>
        )}

        {!showPreview && (
          <div className="mt-8 grid grid-cols-3 gap-4">
            {[
              { icon: <FileSpreadsheet className="w-5 h-5 text-muted" />, title: 'Auto Column Mapping', desc: 'Works with any CSV format' },
              { icon: <Zap className="w-5 h-5 text-muted" />, title: 'AI Enrichment', desc: 'Auto-classify & normalize' },
              { icon: <CheckCircle className="w-5 h-5 text-muted" />, title: 'Export Ready', desc: 'CSV + XLSX with color coding' },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="p-4 rounded-xl bg-white border border-border text-center">
                <div className="w-10 h-10 rounded-lg bg-gray-50 flex items-center justify-center mx-auto mb-3">{icon}</div>
                <div className="text-sm font-semibold text-text mb-0.5">{title}</div>
                <div className="text-xs text-muted">{desc}</div>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
