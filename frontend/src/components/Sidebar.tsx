import { motion } from 'framer-motion';
import { Upload, BarChart3, Users, Table2 } from 'lucide-react';
import type { Page } from '../App';

interface Props {
  page: Page;
  setPage: (p: Page) => void;
  hasData: boolean;
  totalProducts?: number;
  accuracy?: number;
}

const nav = [
  { id: 'upload' as Page, label: 'Data Ingestion', icon: Upload },
  { id: 'dashboard' as Page, label: 'Analytics', icon: BarChart3 },
  { id: 'review' as Page, label: 'Human Review', icon: Users },
  { id: 'catalog' as Page, label: 'Catalog Grid', icon: Table2 },
];

export default function Sidebar({ page, setPage, hasData, totalProducts, accuracy }: Props) {
  return (
    <aside className="w-60 bg-white border-r border-border flex flex-col shrink-0">
      <div className="h-14 border-b border-border flex items-center gap-3 px-5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-md shadow-brand/20">
          <span className="text-white text-xs font-bold">L</span>
        </div>
        <span className="text-lg font-black text-text tracking-tight">LEXICON</span>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {nav.map(({ id, label, icon: Icon }) => {
          const active = page === id;
          const disabled = !hasData && id !== 'upload';
          return (
            <button
              key={id}
              onClick={() => !disabled && setPage(id)}
              disabled={disabled}
              className={`relative w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                disabled
                  ? 'text-gray-300 cursor-not-allowed'
                  : active
                  ? 'text-blue-700'
                  : 'text-muted hover:bg-gray-50 hover:text-text'
              }`}
            >
              {active && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 bg-blue-50 rounded-lg border-l-[3px] border-blue-600"
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-3">
                <Icon className="w-4 h-4" />
                {label}
                {id === 'review' && !disabled && (
                  <span className="ml-auto text-[10px] font-bold bg-orange-50 text-orange-600 border border-orange-200 px-1.5 py-0.5 rounded-full">
                    HITL
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Stats section */}
      <div className="px-4 py-3 border-t border-border space-y-2">
        {hasData && typeof totalProducts === 'number' && (
          <div className="rounded-lg bg-brand/5 border border-brand/10 p-3">
            <div className="text-xl font-black text-brand">{totalProducts.toLocaleString()}</div>
            <div className="text-[10px] text-muted font-bold uppercase tracking-wider">Products Enriched</div>
          </div>
        )}
        {typeof accuracy === 'number' && accuracy > 0 && (
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-muted font-medium">Avg Confidence</span>
            <span className={`font-bold ${accuracy >= 80 ? 'text-green' : accuracy >= 50 ? 'text-orange-600' : 'text-red'}`}>
              {accuracy.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-border mt-auto">
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </span>
          <span className="text-xs font-bold text-green-700">Pipeline Ready</span>
        </div>
        <div className="text-[10px] text-muted/50 tracking-wide">LEXICON v2.0</div>
      </div>
    </aside>
  );
}
