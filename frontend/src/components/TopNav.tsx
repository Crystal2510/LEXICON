import { RotateCcw } from 'lucide-react';
import type { AppState } from '../App';

interface Props {
  fileName: string;
  appState: AppState;
  onReset: () => void;
  accuracy?: number;
}

function getAccuracyColor(accuracy: number): string {
  if (accuracy > 80) return 'bg-green-light text-green';
  if (accuracy > 60) return 'bg-orange-50 text-orange-600';
  return 'bg-red-100 text-red-600';
}

export default function TopNav({ fileName, appState, onReset, accuracy }: Props) {
  return (
    <header className="h-14 bg-white border-b border-border flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-3">
        {appState === 'done' && fileName && (
          <>
            <span className="text-sm text-muted">Dataset:</span>
            <span className="text-sm font-semibold text-text">{fileName}</span>
            <span className="text-[10px] font-bold bg-green-light text-green px-2 py-0.5 rounded-full uppercase">
              Processed
            </span>
          </>
        )}
        {appState === 'done' && typeof accuracy === 'number' && (
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${getAccuracyColor(accuracy)}`}>
            {accuracy.toFixed(1)}% accuracy
          </span>
        )}
        {appState === 'processing' && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-brand border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-muted">Processing...</span>
          </div>
        )}
      </div>
      {appState === 'done' && (
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-sm text-muted hover:text-text hover:bg-gray-50 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          New Session
        </button>
      )}
    </header>
  );
}
