import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { Layers, Tag, FileCode, Copy, AlertTriangle, CheckCircle2, Eye, ChevronDown, ChevronUp, BarChart2 } from 'lucide-react';
import Analytics from './Analytics';
import BeforeAfterCard from './BeforeAfterCard';

interface Props {
  stats: any;
  rows: any[];
}

const COLORS = ['#2563EB', '#16A34A', '#D97706', '#DC2626', '#7C3AED', '#EA580C', '#2563EB', '#0891B2', '#6366F1', '#A855F7'];

function useCountUp(target: number | string, duration = 800) {
  const [display, setDisplay] = useState('0');
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const numStr = String(target).replace(/[^0-9.]/g, '');
    const numVal = parseFloat(numStr);
    if (isNaN(numVal) || numVal === 0) {
      setDisplay(String(target));
      return;
    }
    const hasPercent = String(target).includes('%');
    const hasComma = String(target).includes(',');
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * numVal);
      let formatted = hasComma ? current.toLocaleString() : String(current);
      if (hasPercent) formatted += '%';
      setDisplay(formatted);
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  return display;
}

function MetricCard({ icon, label, value, pct, color }: { icon: React.ReactNode; label: string; value: any; pct?: string; color: string }) {
  const tc: Record<string, string> = {
    blue: 'text-brand',
    green: 'text-green',
    yellow: 'text-orange-600',
    red: 'text-red',
  };
  const isNumeric = typeof value === 'number' || (typeof value === 'string' && /^\d[\d,]*%?$/.test(String(value).replace(/,/g, '')));
  const animatedValue = useCountUp(value, 900);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="p-5 rounded-xl bg-white border border-border"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-9 h-9 rounded-lg bg-gray-50 flex items-center justify-center`}>
          <span className={tc[color]}>{icon}</span>
        </div>
        <span className="text-sm font-bold text-muted">{label}</span>
      </div>
      <div className="text-[26px] font-black text-text">{isNumeric ? animatedValue : value}</div>
      {pct && <div className="text-xs text-muted mt-1">{pct}</div>}
    </motion.div>
  );
}

function FillBar({ label, pct }: { label: string; pct: number }) {
  const color = pct >= 80 ? 'bg-green' : pct >= 50 ? 'bg-orange-500' : 'bg-brand';
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-muted font-bold">{label}</span>
        <span className="text-text font-black">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function Dashboard({ stats, rows }: Props) {
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics'>('overview');
  const [previewOpen, setPreviewOpen] = useState(false);
  const previewRows = rows?.slice(0, 50) || [];
  const previewCols = ['Mfg_Part_Num', 'BRAND_NAME', 'Classpath', 'INVOICE_DESC', 'MOBILE_DESC', 'CONFIDENCE_SCORE'];

  const fillRates = [
    { label: 'Brands Identified', pct: stats.brand_pct },
    { label: 'Classpath Classified', pct: stats.class_pct },
    { label: 'Invoice Desc Filled', pct: stats.inv_pct },
    { label: 'UNSPSC Codes', pct: stats.unspsc_pct },
    { label: 'Attributes Extracted', pct: stats.attr_pct },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-6 space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[32px] font-black text-text tracking-tight">Analytics Dashboard</h1>
          <p className="text-sm text-muted mt-1">{stats.total.toLocaleString()} products processed</p>
        </div>
        <div className="flex items-center rounded-lg border border-border overflow-hidden">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 text-xs font-semibold transition-colors ${
              activeTab === 'overview'
                ? 'bg-brand text-white'
                : 'bg-white text-muted hover:bg-gray-50'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 text-xs font-semibold transition-colors ${
              activeTab === 'analytics'
                ? 'bg-brand text-white'
                : 'bg-white text-muted hover:bg-gray-50'
            }`}
          >
            <span className="flex items-center gap-1.5">
              <BarChart2 className="w-3.5 h-3.5" />
              Analytics
            </span>
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
      <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard icon={<Layers className="w-4 h-4" />} label="Total Products" value={stats.total.toLocaleString()} color="blue" />
        <MetricCard icon={<CheckCircle2 className="w-4 h-4" />} label="Classified" value={`${stats.class_pct}%`} pct={`${stats.classified.toLocaleString()} products`} color="green" />
        <MetricCard icon={<Tag className="w-4 h-4" />} label="Brands Found" value={`${stats.brand_pct}%`} pct={`${stats.brand_found.toLocaleString()} products`} color="blue" />
        <MetricCard icon={<FileCode className="w-4 h-4" />} label="UNSPSC Filled" value={`${stats.unspsc_pct}%`} color="blue" />
        <MetricCard icon={<Copy className="w-4 h-4" />} label="Duplicates" value={stats.dup_count} color={stats.dup_count > 0 ? 'yellow' : 'green'} />
        <MetricCard icon={<AlertTriangle className="w-4 h-4" />} label="Needs Review" value={stats.review_count} color={stats.review_count > 0 ? 'yellow' : 'green'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl bg-white border border-border">
          <h3 className="text-base font-bold text-text mb-4">Confidence Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stats.histogram}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#6B7280' }} />
              <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="p-5 rounded-xl bg-white border border-border">
          <h3 className="text-base font-bold text-text mb-4">Taxonomy Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={stats.taxonomy}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                nameKey="name"
                paddingAngle={2}
              >
                {stats.taxonomy.map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11, color: '#6B7280' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="p-5 rounded-xl bg-white border border-border">
        <h3 className="text-base font-bold text-text mb-4">Data Fill Rates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
          {fillRates.map(({ label, pct }) => (
            <FillBar key={label} label={label} pct={pct} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="p-6 rounded-xl bg-green-light border border-green/20 text-center">
          <div className="text-4xl font-black text-green">{stats.conf_high}</div>
          <div className="text-sm font-bold text-green/70 mt-2">High Confidence</div>
          <div className="text-xs text-green/50 mt-0.5">80-100% accuracy</div>
        </div>
        <div className="p-6 rounded-xl bg-orange-50 border border-orange-200 text-center">
          <div className="text-4xl font-black text-orange-600">{stats.conf_mid}</div>
          <div className="text-sm font-bold text-orange-600/70 mt-2">Moderate Confidence</div>
          <div className="text-xs text-orange-500/50 mt-0.5">50-79% accuracy</div>
        </div>
        <div className="p-6 rounded-xl bg-red-light border border-red/20 text-center">
          <div className="text-4xl font-black text-red">{stats.conf_low}</div>
          <div className="text-sm font-bold text-red/70 mt-2">Low Confidence</div>
          <div className="text-xs text-red/50 mt-0.5">Below 50% - review needed</div>
        </div>
      </div>

      {/* Transformation Examples */}
      <div className="mb-6">
        <h3 className="text-lg font-black text-gray-900 mb-3">Transformation Examples</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {rows.slice(0, 3).map((row, i) => (
            <BeforeAfterCard
              key={i}
              mpn={row.Mfg_Part_Num || ''}
              partDesc={row.Part_Desc || ''}
              brandName={row.BRAND_NAME || ''}
              classpath={row.Classpath || ''}
              invoiceDesc={row.INVOICE_DESC || ''}
              mobileDesc={row.MOBILE_DESC || ''}
              confidenceScore={row.CONFIDENCE_SCORE || ''}
              reviewReason={row.REVIEW_REASON || ''}
              attrCount={
                ['ATTRIBUTE_LABEL 1','ATTRIBUTE_LABEL 2','ATTRIBUTE_LABEL 3','ATTRIBUTE_LABEL 4','ATTRIBUTE_LABEL 5',
                 'ATTRIBUTE_LABEL 6','ATTRIBUTE_LABEL 7','ATTRIBUTE_LABEL 8','ATTRIBUTE_LABEL 9','ATTRIBUTE_LABEL 10',
                 'ATTRIBUTE_LABEL 11','ATTRIBUTE_LABEL 12','ATTRIBUTE_LABEL 13','ATTRIBUTE_LABEL 14','ATTRIBUTE_LABEL 15',
                 'ATTRIBUTE_LABEL 16','ATTRIBUTE_LABEL 17','ATTRIBUTE_LABEL 18','ATTRIBUTE_LABEL 19','ATTRIBUTE_LABEL 20'
                ].filter(col => row[col] && String(row[col]).trim() !== '').length
              }
            />
          ))}
        </div>
      </div>

      {/* Enriched Data Preview */}
      <div className="rounded-xl bg-white border border-border overflow-hidden">
        <button
          onClick={() => setPreviewOpen(!previewOpen)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2 text-sm font-bold text-text">
            <Eye className="w-4 h-4 text-muted" />
            Enriched Data Preview
            <span className="text-xs font-normal text-muted">(first 50 rows)</span>
          </div>
          {previewOpen ? <ChevronUp className="w-4 h-4 text-muted" /> : <ChevronDown className="w-4 h-4 text-muted" />}
        </button>

        <AnimatePresence>
          {previewOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="overflow-x-auto max-h-80 overflow-y-auto border-t border-border">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-gray-50 border-b border-border">
                    <tr>
                      <th className="px-3 py-2 text-left text-[10px] font-bold text-muted uppercase w-10">#</th>
                      {previewCols.map((col) => (
                        <th key={col} className="px-3 py-2 text-left text-[10px] font-bold text-muted uppercase whitespace-nowrap">
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row: any, idx: number) => (
                      <tr key={idx} className="border-b border-border/30 hover:bg-gray-50">
                        <td className="px-3 py-2 text-muted">{idx + 1}</td>
                        <td className="px-3 py-2 font-mono text-brand font-medium">{row.Mfg_Part_Num || '-'}</td>
                        <td className="px-3 py-2 font-medium text-text">{row.BRAND_NAME || '-'}</td>
                        <td className="px-3 py-2 text-xs text-green">{row.Classpath || '-'}</td>
                        <td className="px-3 py-2 font-mono text-text">{row.INVOICE_DESC || '-'}</td>
                        <td className="px-3 py-2 text-muted max-w-[200px] truncate">{row.MOBILE_DESC || '-'}</td>
                        <td className="px-3 py-2">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            parseFloat(row.CONFIDENCE_SCORE || '0') >= 80 ? 'bg-green-light text-green' :
                            parseFloat(row.CONFIDENCE_SCORE || '0') >= 50 ? 'bg-orange-50 text-orange-600' :
                            'bg-red-light text-red'
                          }`}>
                            {row.CONFIDENCE_SCORE || '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {!previewOpen && (
          <div className="px-4 pb-4 flex flex-wrap gap-2">
            {previewRows.slice(0, 8).map((row: any, idx: number) => (
              <div key={idx} className="flex items-center gap-1.5 px-2 py-1 bg-gray-50 rounded text-[10px]">
                <span className="font-mono text-brand">{row.Mfg_Part_Num}</span>
                <span className="text-muted">&rarr;</span>
                <span className="font-medium">{row.BRAND_NAME}</span>
              </div>
            ))}
            {previewRows.length > 8 && <span className="text-[10px] text-muted self-center">+{previewRows.length - 8} more</span>}
          </div>
        )}
      </div>
      </>
      )}

      {activeTab === 'analytics' && (
        <Analytics data={rows} />
      )}
    </motion.div>
  );
}
