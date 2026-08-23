import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle, AlertTriangle, Download, CheckSquare, Square,
  Search, X, ChevronUp, ChevronDown, ChevronRight, Filter, ThumbsUp, Pencil
} from 'lucide-react';
import {
  getAllRows, approveRow, approveBatch, downloadReviewItems
} from '../api';

interface Props {
  onUpdate: (stats: any) => void;
}

interface EnrichedRow {
  _row_index: number;
  Mfg_Part_Num: string;
  Part_Desc: string;
  BRAND_NAME: string;
  MANUFACTURER_NAME: string;
  Classpath: string;
  MOBILE_DESC: string;
  INVOICE_DESC: string;
  SHORT_DESC: string;
  UNSPSC: string;
  CONFIDENCE_SCORE: string;
  NEEDS_REVIEW: string;
  REVIEW_REASON: string;
}

type SortField = '_row_index' | 'BRAND_NAME' | 'Classpath' | 'CONFIDENCE_SCORE' | 'NEEDS_REVIEW';

export default function HumanReview({ onUpdate }: Props) {
  const [rows, setRows] = useState<EnrichedRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [editingRow, setEditingRow] = useState<number | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [search, setSearch] = useState('');
  const [filterClasspath, setFilterClasspath] = useState('');
  const [filterReview, setFilterReview] = useState<'all' | 'yes' | 'no'>('all');
  const [sortField, setSortField] = useState<SortField>('CONFIDENCE_SCORE');
  const [sortAsc, setSortAsc] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [recentlyApproved, setRecentlyApproved] = useState<Set<number>>(new Set());

  const fetchRows = useCallback(async () => {
    try {
      const data = await getAllRows();
      setRows(data.rows);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchRows(); }, [fetchRows]);

  const classpathOptions = useMemo(() => {
    const set = new Set<string>();
    rows.forEach(r => { if (r.Classpath) set.add(r.Classpath); });
    return Array.from(set).sort();
  }, [rows]);

  const filteredRows = useMemo(() => {
    let result = rows;
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(r =>
        (r.Mfg_Part_Num || '').toLowerCase().includes(q) ||
        (r.Part_Desc || '').toLowerCase().includes(q) ||
        (r.BRAND_NAME || '').toLowerCase().includes(q) ||
        (r.Classpath || '').toLowerCase().includes(q) ||
        (r.INVOICE_DESC || '').toLowerCase().includes(q)
      );
    }
    if (filterClasspath) {
      result = result.filter(r => r.Classpath === filterClasspath);
    }
    if (filterReview === 'yes') {
      result = result.filter(r => r.NEEDS_REVIEW === 'Yes');
    } else if (filterReview === 'no') {
      result = result.filter(r => r.NEEDS_REVIEW !== 'Yes');
    }
    result = [...result].sort((a, b) => {
      let aVal: any, bVal: any;
      if (sortField === 'CONFIDENCE_SCORE') {
        aVal = parseFloat((a.CONFIDENCE_SCORE || '0').replace('%', ''));
        bVal = parseFloat((b.CONFIDENCE_SCORE || '0').replace('%', ''));
      } else if (sortField === '_row_index') {
        aVal = a._row_index;
        bVal = b._row_index;
      } else {
        aVal = (a[sortField] || '').toLowerCase();
        bVal = (b[sortField] || '').toLowerCase();
      }
      if (aVal < bVal) return sortAsc ? -1 : 1;
      if (aVal > bVal) return sortAsc ? 1 : -1;
      return 0;
    });
    return result;
  }, [rows, search, filterClasspath, filterReview, sortField, sortAsc]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === 'CONFIDENCE_SCORE');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ChevronDown className="w-3 h-3 text-muted/40" />;
    return sortAsc
      ? <ChevronUp className="w-3 h-3 text-brand" />
      : <ChevronDown className="w-3 h-3 text-brand" />;
  };

  const toggleRow = (idx: number) => {
    setSelectedRows(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const toggleAllVisible = () => {
    const allIndices = filteredRows.map(r => r._row_index);
    const allSelected = allIndices.every(i => selectedRows.has(i));
    setSelectedRows(prev => {
      const next = new Set(prev);
      if (allSelected) {
        allIndices.forEach(i => next.delete(i));
      } else {
        allIndices.forEach(i => next.add(i));
      }
      return next;
    });
  };

  const handleBatchApprove = async () => {
    if (selectedRows.size === 0) return;
    setSaving(true);
    setMessage(null);
    try {
      const indices = Array.from(selectedRows);
      setRecentlyApproved(prev => new Set([...prev, ...indices]));
      const result = await approveBatch(indices);
      setMessage({ type: 'success', text: `Approved ${result.approved} items` });
      setSelectedRows(new Set());
      setTimeout(() => {
        setRecentlyApproved(prev => {
          const next = new Set(prev);
          indices.forEach(i => next.delete(i));
          return next;
        });
      }, 1500);
      await fetchRows();
      onUpdate({});
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setSaving(false);
    }
  };

  const handleApproveAll = async () => {
    const allIndices = filteredRows.map(r => r._row_index);
    if (allIndices.length === 0) return;
    setSaving(true);
    setMessage(null);
    try {
      setRecentlyApproved(prev => new Set([...prev, ...allIndices]));
      const result = await approveBatch(allIndices);
      setMessage({ type: 'success', text: `Approved all ${result.approved} visible items` });
      setSelectedRows(new Set());
      setTimeout(() => {
        setRecentlyApproved(new Set());
      }, 1500);
      await fetchRows();
      onUpdate({});
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (item: EnrichedRow) => {
    setEditingRow(item._row_index);
    setEdits({
      Classpath: item.Classpath || '',
      BRAND_NAME: item.BRAND_NAME || '',
      INVOICE_DESC: item.INVOICE_DESC || '',
      MOBILE_DESC: item.MOBILE_DESC || '',
      UNSPSC: item.UNSPSC || '',
    });
  };

  const handleSingleApprove = async (rowIndex: number) => {
    setSaving(true);
    setMessage(null);
    try {
      const result = await approveRow(rowIndex, edits);
      setMessage({ type: 'success', text: `Row approved - confidence: ${result.new_confidence}` });
      setEditingRow(null);
      setEdits({});
      setRecentlyApproved(prev => new Set(prev).add(rowIndex));
      setTimeout(() => {
        setRecentlyApproved(prev => {
          const next = new Set(prev);
          next.delete(rowIndex);
          return next;
        });
      }, 1500);
      await fetchRows();
      onUpdate({});
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await downloadReviewItems();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'lexicon_review_items.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const totalReview = rows.filter(r => r.NEEDS_REVIEW === 'Yes').length;
  const confAvg = rows.length > 0
    ? (rows.reduce((s, r) => s + parseFloat((r.CONFIDENCE_SCORE || '0').replace('%', '')), 0) / rows.length).toFixed(1)
    : '0';

  const missingBrandCount = rows.filter(r => !r.BRAND_NAME).length;
  const unclassifiedCount = rows.filter(r => r.Classpath === 'General' || !r.Classpath).length;
  const lowConfCount = rows.filter(r => parseFloat((r.CONFIDENCE_SCORE || '0').replace('%', '')) < 70).length;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border bg-white shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-[28px] font-black text-text tracking-tight">Review Queue</h1>
            <p className="text-sm text-muted mt-0.5">
              {rows.length} total rows | {totalReview} need review | Avg confidence: {confAvg}%
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text hover:bg-gray-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            {selectedRows.size > 0 && (
              <button
                onClick={handleBatchApprove}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand text-white text-sm font-semibold hover:bg-brand/90 disabled:opacity-50 transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Approve {selectedRows.size}
              </button>
            )}
            <button
              onClick={handleApproveAll}
              disabled={saving || filteredRows.length === 0}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black text-white text-sm font-semibold hover:bg-gray-800 disabled:opacity-50 transition-colors"
            >
              <ThumbsUp className="w-4 h-4" />
              Approve All
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by MPN, brand, description..."
              className="w-full pl-10 pr-10 py-2 rounded-lg border border-border text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-colors"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <select
              value={filterClasspath}
              onChange={(e) => setFilterClasspath(e.target.value)}
              className="pl-10 pr-8 py-2 rounded-lg border border-border text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand appearance-none transition-colors"
            >
              <option value="">All Categories</option>
              {classpathOptions.map(cp => <option key={cp} value={cp}>{cp}</option>)}
            </select>
          </div>
          <div className="flex items-center rounded-lg border border-border overflow-hidden">
            {(['all', 'yes', 'no'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilterReview(f)}
                className={`px-3 py-2 text-xs font-semibold transition-colors ${
                  filterReview === f
                    ? 'bg-brand text-white'
                    : 'bg-white text-muted hover:bg-gray-50'
                }`}
              >
                {f === 'all' ? 'All' : f === 'yes' ? 'Needs Review' : 'Approved'}
              </button>
            ))}
          </div>
          <button
            onClick={toggleAllVisible}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text hover:bg-gray-50 transition-colors"
          >
            {filteredRows.every(r => selectedRows.has(r._row_index)) ? (
              <CheckSquare className="w-4 h-4 text-brand" />
            ) : (
              <Square className="w-4 h-4" />
            )}
            <span className="text-xs">{selectedRows.size}/{filteredRows.length}</span>
          </button>
        </div>
      </div>

      {/* Message */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className={`mx-4 mt-3 p-3 rounded-lg text-sm font-medium ${
              message.type === 'success' ? 'bg-green-light text-green' : 'bg-red-light text-red'
            }`}
          >
            {message.text}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Summary Banner */}
      <div className="px-4 pt-4 pb-2 shrink-0">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-red/10 p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red/20 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red" />
            </div>
            <div>
                <p className="text-3xl font-black text-red">{missingBrandCount}</p>
              <p className="text-[11px] font-semibold text-red/70 uppercase tracking-wide">Missing Brand</p>
            </div>
          </div>
          <div className="rounded-xl bg-orange-50 p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-3xl font-black text-orange-600">{unclassifiedCount}</p>
              <p className="text-[11px] font-semibold text-orange-600/70 uppercase tracking-wide">Unclassified</p>
            </div>
          </div>
          <div className="rounded-xl bg-orange-500/10 p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <p className="text-3xl font-black text-orange-500">{lowConfCount}</p>
              <p className="text-[11px] font-semibold text-orange-500/70 uppercase tracking-wide">Low Confidence</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-border sticky top-0 z-10">
            <tr>
              <th className="px-3 py-2.5 w-8">
                <span className="text-[10px] font-bold text-muted uppercase">#</span>
              </th>
              <th className="px-3 py-2.5 text-left cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => toggleSort('CONFIDENCE_SCORE')}>
                <div className="flex items-center gap-1 text-[10px] font-bold text-muted uppercase tracking-wider">
                  Conf <SortIcon field="CONFIDENCE_SCORE" />
                </div>
              </th>
              <th className="px-3 py-2.5 text-left">
                <div className="text-[10px] font-bold text-muted uppercase tracking-wider">MPN</div>
              </th>
              <th className="px-3 py-2.5 text-left cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => toggleSort('BRAND_NAME')}>
                <div className="flex items-center gap-1 text-[10px] font-bold text-muted uppercase tracking-wider">
                  Brand <SortIcon field="BRAND_NAME" />
                </div>
              </th>
              <th className="px-3 py-2.5 text-left cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => toggleSort('Classpath')}>
                <div className="flex items-center gap-1 text-[10px] font-bold text-muted uppercase tracking-wider">
                  Classpath <SortIcon field="Classpath" />
                </div>
              </th>
              <th className="px-3 py-2.5 text-left">
                <div className="text-[10px] font-bold text-muted uppercase tracking-wider">Invoice DESC</div>
              </th>
              <th className="px-3 py-2.5 text-left">
                <div className="text-[10px] font-bold text-muted uppercase tracking-wider">Mobile DESC</div>
              </th>
              <th className="px-3 py-2.5 text-left cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => toggleSort('NEEDS_REVIEW')}>
                <div className="flex items-center gap-1 text-[10px] font-bold text-muted uppercase tracking-wider">
                  Status <SortIcon field="NEEDS_REVIEW" />
                </div>
              </th>
              <th className="px-3 py-2.5 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => {
              const conf = parseFloat((row.CONFIDENCE_SCORE || '0').replace('%', ''));
              const isEditing = editingRow === row._row_index;
              const needsReview = row.NEEDS_REVIEW === 'Yes';
              return (
                <>
                  <tr
                    key={row._row_index}
                    onClick={() => isEditing ? setEditingRow(null) : startEdit(row)}
                    className={`border-b border-border/30 transition-all duration-500 cursor-pointer ${
                      recentlyApproved.has(row._row_index) ? 'bg-green-light/40 shadow-[inset_0_0_0_1px_rgba(34,197,94,0.3)]' :
                      isEditing ? 'bg-brand-light/20' :
                      needsReview ? 'bg-orange-50 hover:bg-orange-100' :
                      'hover:bg-gray-50'
                    }`}
                  >
                    <td className="px-3 py-2">
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => { e.stopPropagation(); toggleRow(row._row_index); }}
                        className="cursor-pointer"
                      >
                        {selectedRows.has(row._row_index) ? (
                          <CheckSquare className="w-4 h-4 text-brand" />
                        ) : (
                          <Square className="w-4 h-4 text-muted" />
                        )}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        conf >= 80 ? 'text-green' :
                        conf >= 50 ? 'text-orange-600' :
                        'text-red'
                      }`}>
                        {row.CONFIDENCE_SCORE}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-brand font-medium max-w-[120px] truncate">
                      {row.Mfg_Part_Num || '-'}
                    </td>
                    <td className="px-3 py-2 text-text font-medium max-w-[100px] truncate">
                      {row.BRAND_NAME || <span className="text-orange-600 font-medium">Missing</span>}
                    </td>
                    <td className="px-3 py-2 text-muted text-xs max-w-[150px] truncate">
                      {row.Classpath || '-'}
                    </td>
                    <td className="px-3 py-2 text-text text-xs font-mono max-w-[150px] truncate">
                      {row.INVOICE_DESC || '-'}
                    </td>
                    <td className="px-3 py-2 text-muted text-xs max-w-[200px] truncate">
                      {row.MOBILE_DESC || '-'}
                    </td>
                    <td className="px-3 py-2">
                      {needsReview ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-black bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded tracking-wide">
                          <AlertTriangle className="w-2.5 h-2.5" />
                          Review
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-green-light text-green px-1.5 py-0.5 rounded">
                          <CheckCircle className="w-2.5 h-2.5" />
                          OK
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`transition-transform duration-200 ${isEditing ? 'rotate-90' : ''}`}>
                        <ChevronRight className="w-4 h-4 text-muted" />
                      </span>
                    </td>
                  </tr>
                  {/* Inline Edit Row */}
                  {isEditing && (
                    <tr key={`edit-${row._row_index}`} className="bg-brand-light/10 border-b border-brand/20">
                      <td colSpan={9} className="px-4 py-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Pencil className="w-4 h-4 text-brand" />
                          <span className="text-xs font-bold text-brand">Editing: {row.Mfg_Part_Num}</span>
                          <span className="text-xs text-muted">|</span>
                          <span className="text-xs text-muted truncate max-w-[300px]">{row.Part_Desc}</span>
                        </div>
                        <div className="grid grid-cols-5 gap-3">
                          <div>
                            <label className="text-[10px] font-bold text-muted uppercase mb-1 block">Brand</label>
                            <input
                              type="text"
                              value={edits.BRAND_NAME || ''}
                              onChange={(e) => setEdits({ ...edits, BRAND_NAME: e.target.value })}
                              className="w-full px-2 py-1.5 rounded border border-border text-xs text-text bg-white focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand transition-colors"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-muted uppercase mb-1 block">Classpath</label>
                            <input
                              type="text"
                              value={edits.Classpath || ''}
                              onChange={(e) => setEdits({ ...edits, Classpath: e.target.value })}
                              className="w-full px-2 py-1.5 rounded border border-border text-xs text-text bg-white focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand transition-colors"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-muted uppercase mb-1 block">Invoice DESC</label>
                            <input
                              type="text"
                              value={edits.INVOICE_DESC || ''}
                              onChange={(e) => setEdits({ ...edits, INVOICE_DESC: e.target.value })}
                              className="w-full px-2 py-1.5 rounded border border-border text-xs text-text bg-white font-mono focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand transition-colors"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-muted uppercase mb-1 block">Mobile DESC</label>
                            <input
                              type="text"
                              value={edits.MOBILE_DESC || ''}
                              onChange={(e) => setEdits({ ...edits, MOBILE_DESC: e.target.value })}
                              className="w-full px-2 py-1.5 rounded border border-border text-xs text-text bg-white focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand transition-colors"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-muted uppercase mb-1 block">UNSPSC</label>
                            <input
                              type="text"
                              value={edits.UNSPSC || ''}
                              onChange={(e) => setEdits({ ...edits, UNSPSC: e.target.value })}
                              className="w-full px-2 py-1.5 rounded border border-border text-xs text-text bg-white font-mono focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand transition-colors"
                            />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 mt-3">
                          <button
                            onClick={() => handleSingleApprove(row._row_index)}
                            disabled={saving}
                            className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:bg-brand/90 disabled:opacity-50 transition-colors"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            {saving ? 'Saving...' : 'Approve Changes'}
                          </button>
                          <button
                            onClick={() => setEditingRow(null)}
                            className="px-4 py-1.5 rounded-lg border border-border text-xs text-muted hover:text-text hover:bg-gray-50 transition-colors"
                          >
                            Cancel
                          </button>
                          {edits.INVOICE_DESC && (
                            <span className={`text-[10px] font-medium ${edits.INVOICE_DESC.length <= 40 ? 'text-green' : 'text-red'}`}>
                              {edits.INVOICE_DESC.length}/40 chars
                            </span>
                          )}
                          {edits.MOBILE_DESC && (
                            <span className={`text-[10px] font-medium ${edits.MOBILE_DESC.length >= 60 && edits.MOBILE_DESC.length <= 80 ? 'text-green' : 'text-orange-600'}`}>
                              {edits.MOBILE_DESC.length}/80 chars
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center">
                  <p className="text-sm text-muted">No rows match your filters</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-border bg-gray-50 shrink-0 flex items-center justify-between text-xs text-muted">
        <span>Showing {filteredRows.length} of {rows.length} rows</span>
        <span>{selectedRows.size} selected | {filteredRows.filter(r => r.NEEDS_REVIEW === 'Yes').length} need review</span>
      </div>
    </motion.div>
  );
}
