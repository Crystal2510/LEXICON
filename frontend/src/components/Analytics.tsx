import { useMemo } from 'react';

interface AnalyticsProps {
  data: any[];
}

interface ConfidenceBucket {
  label: string;
  count: number;
}

export default function Analytics({ data }: AnalyticsProps) {
  const totalProducts = useMemo(() => data.length, [data]);

  const brandFillRate = useMemo(() => {
    if (!data.length) return 0;
    const filled = data.filter((row) => row.BRAND_NAME && row.BRAND_NAME.trim()).length;
    return Math.round((filled / data.length) * 100);
  }, [data]);

  const attributeCoverage = useMemo(() => {
    if (!data.length) return 0;
    const nonBrandFields = Object.keys(data[0] || {}).filter((k) => k !== 'BRAND_NAME');
    if (!nonBrandFields.length) return 0;
    const totalFields = nonBrandFields.length;
    const avgFillPerRow =
      data.reduce((sum, row) => {
        const filled = nonBrandFields.filter((k) => row[k] && String(row[k]).trim()).length;
        return sum + filled / totalFields;
      }, 0) / data.length;
    return Math.round(avgFillPerRow * 100);
  }, [data]);

  const reviewRequired = useMemo(
    () => data.filter((row) => row.NEEDS_REVIEW === 'Yes').length,
    [data]
  );

  const categoryDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    data.forEach((row) => {
      const classpath = row.Classpath || 'Unknown';
      const topCategory = classpath.split('>')[0].trim();
      counts[topCategory] = (counts[topCategory] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12);
  }, [data]);

  const brandCoverage = useMemo(() => {
    const counts: Record<string, number> = {};
    data.forEach((row) => {
      const brand = row.BRAND_NAME || 'Unknown';
      counts[brand] = (counts[brand] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
  }, [data]);

  const fieldFillRate = useMemo(() => {
    const fields = ['BRAND_NAME', 'Classpath', 'MOBILE_DESC', 'INVOICE_DESC', 'UNSPSC'];
    return fields.map((field) => {
      const filled = data.filter((row) => row[field] && String(row[field]).trim()).length;
      const pct = data.length ? Math.round((filled / data.length) * 100) : 0;
      return { field, pct };
    });
  }, [data]);

  const confidenceDistribution = useMemo((): ConfidenceBucket[] => {
    const buckets: Record<string, number> = {
      '90-100%': 0,
      '80-89%': 0,
      '70-79%': 0,
      '60-69%': 0,
      '<60%': 0,
    };
    data.forEach((row) => {
      const score = parseFloat(row.CONFIDENCE_SCORE);
      if (isNaN(score)) {
        buckets['<60%']++;
      } else if (score >= 90) {
        buckets['90-100%']++;
      } else if (score >= 80) {
        buckets['80-89%']++;
      } else if (score >= 70) {
        buckets['70-79%']++;
      } else if (score >= 60) {
        buckets['60-69%']++;
      } else {
        buckets['<60%']++;
      }
    });
    return Object.entries(buckets).map(([label, count]) => ({ label, count }));
  }, [data]);

  const maxCategoryCount = useMemo(
    () => Math.max(...categoryDistribution.map(([, c]) => c), 1),
    [categoryDistribution]
  );

  const maxBrandCount = useMemo(
    () => Math.max(...brandCoverage.map(([, c]) => c), 1),
    [brandCoverage]
  );

  const maxConfidenceCount = useMemo(
    () => Math.max(...confidenceDistribution.map((b) => b.count), 1),
    [confidenceDistribution]
  );

  const maxFillPct = useMemo(() => Math.max(...fieldFillRate.map((f) => f.pct), 1), [fieldFillRate]);

  const getBarColor = (pct: number) => {
    if (pct >= 90) return 'bg-emerald-500';
    if (pct >= 70) return 'bg-amber-400';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6">
      {/* Hero Score Card */}
      <div className="rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 p-8 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-bold text-blue-100 uppercase tracking-wider">Average Confidence</p>
            <p className="text-6xl font-black text-white mt-2">
              {totalProducts > 0
                ? Math.round(
                    data.reduce((sum, row) => sum + (parseFloat(row.CONFIDENCE_SCORE) || 0), 0) /
                      data.length
                  )
                : 0}
              <span className="text-2xl ml-1">%</span>
            </p>
            <p className="text-sm text-blue-200 mt-2">Across all products</p>
          </div>
          <div className="flex flex-col items-end">
            <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard label="Total Products" value={totalProducts} />
        <SummaryCard label="Brand Fill Rate" value={`${brandFillRate}%`} />
        <SummaryCard label="Attribute Coverage" value={`${attributeCoverage}%`} />
        <SummaryCard label="Review Required" value={reviewRequired} />
      </div>

      {/* Two Charts Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
          <h3 className="text-base font-black text-gray-900 mb-4 uppercase tracking-wider">
            Category Distribution
          </h3>
          <div className="space-y-2">
            {categoryDistribution.map(([category, count]) => (
              <div key={category} className="flex items-center gap-2">
                <span
                  className="text-xs text-gray-600 w-28 truncate shrink-0 text-right"
                  title={category}
                >
                  {category}
                </span>
                <div className="flex-1 h-5 bg-gray-100 rounded overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded transition-all duration-300"
                    style={{ width: `${(count / maxCategoryCount) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-10 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Brand Coverage */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
          <h3 className="text-base font-black text-gray-900 mb-4 uppercase tracking-wider">
            Top 10 Brands
          </h3>
          <div className="space-y-2">
            {brandCoverage.map(([brand, count]) => (
              <div key={brand} className="flex items-center gap-2">
                <span
                  className="text-xs text-gray-600 w-28 truncate shrink-0 text-right"
                  title={brand}
                >
                  {brand}
                </span>
                <div className="flex-1 h-5 bg-gray-100 rounded overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded transition-all duration-300"
                    style={{ width: `${(count / maxBrandCount) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-10 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Field Fill Rate */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
          <h3 className="text-base font-black text-gray-900 mb-4 uppercase tracking-wider">
            Field Fill Rate
          </h3>
          <div className="flex items-end gap-4 h-48">
            {fieldFillRate.map(({ field, pct }) => (
              <div key={field} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs text-gray-600 font-medium">{pct}%</span>
                <div className="w-full h-36 bg-gray-100 rounded-t flex items-end">
                  <div
                    className={`w-full rounded-t transition-all duration-300 ${getBarColor(pct)}`}
                    style={{ height: `${(pct / maxFillPct) * 100}%` }}
                  />
                </div>
                <span className="text-[10px] text-gray-500 text-center leading-tight">
                  {field}
                </span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-3 text-[10px] text-gray-500 justify-end">
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded bg-emerald-500" /> &gt;90%
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded bg-amber-400" /> &gt;70%
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded bg-rose-500" /> &lt;70%
            </span>
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
          <h3 className="text-base font-black text-gray-900 mb-4 uppercase tracking-wider">
            Confidence Distribution
          </h3>
          <div className="space-y-2">
            {confidenceDistribution.map(({ label, count }) => (
              <div key={label} className="flex items-center gap-2">
                <span className="text-xs text-gray-600 w-16 text-right shrink-0">{label}</span>
                <div className="flex-1 h-5 bg-gray-100 rounded overflow-hidden">
                  <div
                    className="h-full bg-teal-500 rounded transition-all duration-300"
                    style={{ width: `${(count / maxConfidenceCount) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-10 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 flex flex-col gap-1">
      <span className="text-xs text-gray-500 uppercase tracking-wider font-bold">{label}</span>
      <span className="text-3xl font-black text-gray-900">{value}</span>
    </div>
  );
}
