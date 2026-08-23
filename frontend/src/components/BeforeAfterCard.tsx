import { Sparkles, AlertTriangle } from 'lucide-react';

interface BeforeAfterCardProps {
  mpn: string;
  partDesc: string;
  brandName: string;
  classpath: string;
  invoiceDesc: string;
  mobileDesc: string;
  confidenceScore: string;
  reviewReason?: string;
  attrCount: number;
}

export default function BeforeAfterCard({
  mpn,
  partDesc,
  brandName,
  classpath,
  invoiceDesc,
  mobileDesc,
  confidenceScore,
  reviewReason,
  attrCount,
}: BeforeAfterCardProps) {
  const conf = parseFloat((confidenceScore || '0').replace('%', ''));
  const confColor =
    conf >= 80 ? 'text-green bg-green-light' :
    conf >= 50 ? 'text-orange-600 bg-orange-50' :
    'text-red bg-red-light';

  const isUnclassified = classpath === 'General' || !classpath;
  const isNoBrand = !brandName;

  return (
    <div className="rounded-xl border border-border shadow-sm overflow-hidden flex">
      {/* LEFT — Raw Input */}
      <div className="flex-1 bg-gray-50 p-5 border-r border-border">
        <p className="text-[10px] font-bold text-muted uppercase tracking-wider mb-3">Raw Input</p>

        <div className="space-y-2">
          <div>
            <span className="text-[10px] font-semibold text-muted uppercase block mb-0.5">MPN</span>
            <span className="font-mono text-sm text-brand font-semibold">{mpn || '-'}</span>
          </div>
          <div>
            <span className="text-[10px] font-semibold text-muted uppercase block mb-0.5">Part Desc</span>
            <span className="text-sm text-text">{partDesc || '-'}</span>
          </div>
        </div>

        {(isNoBrand || isUnclassified) && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {isNoBrand && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-red-light text-red px-2 py-0.5 rounded">
                <AlertTriangle className="w-2.5 h-2.5" />
                No Brand
              </span>
            )}
            {isUnclassified && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-red-light text-red px-2 py-0.5 rounded">
                <AlertTriangle className="w-2.5 h-2.5" />
                Unclassified
              </span>
            )}
          </div>
        )}
      </div>

      {/* RIGHT — Enriched Output */}
      <div className="flex-1 bg-white p-5">
        <div className="flex items-center gap-1.5 mb-3">
          <Sparkles className="w-3.5 h-3.5 text-brand" />
          <p className="text-[10px] font-bold text-muted uppercase tracking-wider">Enriched Output</p>
        </div>

        <div className="space-y-2">
          <div>
            <span className="text-[10px] font-semibold text-muted uppercase block mb-0.5">Brand</span>
            <span className="text-sm text-text font-bold">{brandName || <span className="text-orange-600 font-medium">Missing</span>}</span>
          </div>
          <div>
            <span className="text-[10px] font-semibold text-muted uppercase block mb-0.5">Classpath</span>
            <span className="text-sm text-green font-medium">{classpath || '-'}</span>
          </div>
          <div>
            <span className="text-[10px] font-semibold text-muted uppercase block mb-0.5">Invoice Desc</span>
            <span className="font-mono text-xs text-text">{invoiceDesc || '-'}</span>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-3">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${confColor}`}>
            {confidenceScore}
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-muted">
            {attrCount} attributes
          </span>
        </div>

        {mobileDesc && (
          <p className="text-[11px] text-muted mt-2 truncate" title={mobileDesc}>
            {mobileDesc}
          </p>
        )}
        {reviewReason && (
          <span className="inline-flex mt-2 px-2 py-0.5 bg-amber-50 text-amber-600 text-[10px] rounded font-bold" title={reviewReason}>
            {reviewReason.length > 25 ? reviewReason.slice(0, 25) + '...' : reviewReason}
          </span>
        )}
      </div>
    </div>
  );
}
