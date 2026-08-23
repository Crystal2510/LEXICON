import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, FileText, FileSpreadsheet, LayoutGrid, List, Tag, Layers } from 'lucide-react';
import { downloadCSV, downloadXLSX } from '../api';

interface Props {
  rows: any[];
  columns: string[];
}

const PAGE_SIZE = 50;
const CARD_PAGE_SIZE = 24;
const KEY_COLS = ['Mfg_Part_Num', 'BRAND_NAME', 'MANUFACTURER_NAME', 'Classpath', 'INVOICE_DESC', 'MOBILE_DESC', 'CONFIDENCE_SCORE'];

export default function CatalogGrid({ rows }: Props) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table');

  const filtered = useMemo(() => {
    if (!search.trim()) return rows;
    const q = search.toLowerCase();
    return rows.filter((r: any) =>
      Object.values(r).some(v =>
        v != null && String(v).toLowerCase().includes(q)
      )
    );
  }, [rows, search]);

  const pageSize = viewMode === 'card' ? CARD_PAGE_SIZE : PAGE_SIZE;
  const paged = useMemo(() => filtered.slice(page * pageSize, (page + 1) * pageSize), [filtered, page, pageSize]);
  const totalPages = Math.ceil(filtered.length / pageSize);

  const handleSearch = (val: string) => {
    setSearch(val);
    setPage(0);
    setExpandedRow(null);
  };

  const handleDownload = async (type: 'csv' | 'xlsx') => {
    const blob = type === 'csv' ? await downloadCSV(rows) : await downloadXLSX(rows);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lexicon_enriched_output.${type}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getConfBadge = (conf: string) => {
    const val = parseFloat(conf || '0');
    if (val >= 80) return 'bg-green-light text-green border border-green/20';
    if (val >= 50) return 'bg-orange-50 text-orange-600 border border-orange-200';
    return 'bg-red-light text-red border border-red/20';
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="p-4 border-b border-border bg-white flex items-center gap-3 shrink-0">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search by MPN, brand, description, classpath..."
            className="w-full pl-10 pr-10 py-2.5 rounded-lg border border-border text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-colors"
          />
          {search && (
            <button onClick={() => handleSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <span className="text-xs text-muted shrink-0">{filtered.length.toLocaleString()} rows</span>
        <div className="h-5 w-px bg-border" />

        {/* View Mode Toggle */}
        <div className="flex items-center rounded-lg border border-border overflow-hidden">
          <button
            onClick={() => { setViewMode('table'); setPage(0); }}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
              viewMode === 'table' ? 'bg-brand text-white' : 'text-muted hover:bg-gray-50'
            }`}
          >
            <List className="w-3.5 h-3.5" />
            Table
          </button>
          <button
            onClick={() => { setViewMode('card'); setPage(0); }}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
              viewMode === 'card' ? 'bg-brand text-white' : 'text-muted hover:bg-gray-50'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            Cards
          </button>
        </div>

        <div className="h-5 w-px bg-border" />
        <button onClick={() => handleDownload('csv')} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text hover:bg-gray-50 transition-colors">
          <FileText className="w-4 h-4" />
          CSV
        </button>
        <button onClick={() => handleDownload('xlsx')} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black text-white text-sm font-semibold hover:bg-gray-800 transition-colors">
          <FileSpreadsheet className="w-4 h-4" />
          Export XLSX
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <AnimatePresence mode="wait">
          {viewMode === 'table' ? (
            <motion.div key="table" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-white border-b border-border">
                  <tr>
                    <th className="px-4 py-3 text-left text-[10px] font-bold text-muted uppercase tracking-wider w-12">#</th>
                    {KEY_COLS.map((col) => (
                      <th key={col} className="px-4 py-3 text-left text-[10px] font-bold text-muted uppercase tracking-wider whitespace-nowrap">
                        {col.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {paged.map((row: any, idx: number) => {
                    const gIdx = page * pageSize + idx;
                    const expanded = expandedRow === gIdx;
                    return (
                      <tr
                        key={gIdx}
                        className={`border-b border-border/50 cursor-pointer transition-colors ${expanded ? 'bg-gray-50' : 'hover:bg-gray-50'}`}
                        onClick={() => setExpandedRow(expanded ? null : gIdx)}
                      >
                        <td className="px-4 py-3 text-muted text-xs">{gIdx + 1}</td>
                        <td className="px-4 py-3 font-mono text-xs text-brand font-medium">{row.Mfg_Part_Num || '-'}</td>
                        <td className="px-4 py-3 font-medium text-text">{row.BRAND_NAME || '-'}</td>
                        <td className="px-4 py-3 text-muted">{row.MANUFACTURER_NAME || '-'}</td>
                        <td className="px-4 py-3 text-xs text-green font-medium">{row.Classpath || '-'}</td>
                        <td className="px-4 py-3 font-mono text-xs text-text">{row.INVOICE_DESC || '-'}</td>
                        <td className="px-4 py-3 text-xs text-muted max-w-[180px] truncate">{row.MOBILE_DESC || '-'}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${getConfBadge(row.CONFIDENCE_SCORE)}`}>
                            {row.CONFIDENCE_SCORE || '-'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </motion.div>
          ) : (
            <motion.div key="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }} className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {paged.map((row: any, idx: number) => {
                  const gIdx = page * pageSize + idx;
                  return (
                    <motion.div
                      key={gIdx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      className="rounded-xl border border-border bg-white p-4 cursor-pointer transition-all hover:shadow-md hover:border-brand/30"
                      onClick={() => setExpandedRow(expandedRow === gIdx ? null : gIdx)}
                    >
                      {/* Header */}
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <div className="font-mono text-xs text-brand font-medium truncate">{row.Mfg_Part_Num || 'No MPN'}</div>
                          <div className="font-semibold text-sm text-text mt-0.5 truncate">{row.BRAND_NAME || <span className="text-muted italic">Unknown Brand</span>}</div>
                        </div>
                        <span className={`shrink-0 ml-2 inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${getConfBadge(row.CONFIDENCE_SCORE)}`}>
                          {row.CONFIDENCE_SCORE || '-'}
                        </span>
                      </div>

                      {/* Classpath */}
                      {row.Classpath && (
                        <div className="flex items-center gap-1.5 mb-2">
                          <Layers className="w-3 h-3 text-green shrink-0" />
                          <span className="text-[11px] text-green font-medium truncate">{row.Classpath}</span>
                        </div>
                      )}

                      {/* Invoice desc */}
                      {row.INVOICE_DESC && (
                        <div className="font-mono text-[10px] text-muted bg-gray-50 rounded px-2 py-1 truncate mb-2">
                          {row.INVOICE_DESC}
                        </div>
                      )}

                      {/* Attributes preview */}
                      <div className="flex flex-wrap gap-1">
                        {row.MANUFACTURER_NAME && row.MANUFACTURER_NAME !== '-' && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-gray-100 text-[9px] text-muted">
                            <Tag className="w-2.5 h-2.5" />
                            {row.MANUFACTURER_NAME}
                          </span>
                        )}
                      </div>

                      {/* Expanded details */}
                      <AnimatePresence>
                        {expandedRow === gIdx && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="mt-3 pt-3 border-t border-border/50 space-y-1.5 text-[11px]">
                              {row.Part_Desc && (
                                <div><span className="font-bold text-muted">Input:</span> <span className="text-text">{row.Part_Desc}</span></div>
                              )}
                              {row.MOBILE_DESC && (
                                <div><span className="font-bold text-muted">Mobile:</span> <span className="text-text">{row.MOBILE_DESC}</span></div>
                              )}
                              {[1, 2, 3, 4, 5].map(i => {
                                const label = row[`ATTRIBUTE_LABEL ${i}`];
                                const value = row[`ATTRIBUTE_VALUE ${i}`];
                                if (!label || !value) return null;
                                return (
                                  <div key={i}>
                                    <span className="font-bold text-muted">{label}:</span> <span className="text-text">{value}</span>
                                  </div>
                                );
                              })}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-3 border-t border-border bg-white flex items-center justify-between text-xs text-muted shrink-0">
          <span>Page {page + 1} of {totalPages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-30 hover:bg-gray-50 transition-colors">Prev</button>
            <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1} className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-30 hover:bg-gray-50 transition-colors">Next</button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
